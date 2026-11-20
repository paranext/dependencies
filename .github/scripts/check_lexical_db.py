"""Checks that lexical-db/ holds a database that marble-tools' main branch built, and that its
checksum file and build-info.json describe it.

build-info.json comes from the `english-database` artifact of marble-tools' Build English Database
workflow, next to the database it describes. It is the lasting record of which marble-tools and
marble-lexicon commits built the published database, so a database update that forgets to replace
it, or that publishes a database built from an unmerged branch, fails here.

Usage (from the repository root): python3 .github/scripts/check_lexical_db.py [lexical-db]
Set GITHUB_TOKEN to raise the GitHub API rate limit for the main-branch check.
"""
import hashlib
import json
import lzma
import os
import sys
import urllib.request

MARBLE_TOOLS = 'paranext/marble-tools'


def sha256_of(chunks):
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def file_chunks(path):
    with open(path, 'rb') as file:
        yield from iter(lambda: file.read(1 << 20), b'')


def xz_chunks(path):
    with lzma.open(path, 'rb') as file:
        yield from iter(lambda: file.read(1 << 20), b'')


def is_on_main(commit):
    """Whether a marble-tools commit is on its main branch, by GitHub's compare API: main is the
    commit itself or ahead of it."""
    request = urllib.request.Request(
        f'https://api.github.com/repos/{MARBLE_TOOLS}/compare/{commit}...main',
        headers={'Accept': 'application/vnd.github+json'},
    )
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(request) as response:
        status = json.load(response)['status']
    return status in ('identical', 'ahead')


def check(directory, on_main=is_on_main):
    """Returns the problems found, as messages; none means the directory is consistent"""
    problems = []
    xz_path = os.path.join(directory, 'lexical.db.xz')
    with open(os.path.join(directory, 'lexical.db.xz.sha256'), encoding='utf-8') as file:
        recorded_xz = file.read().split()[0]
    if sha256_of(file_chunks(xz_path)) != recorded_xz:
        problems.append('lexical.db.xz does not match lexical.db.xz.sha256')

    info_path = os.path.join(directory, 'build-info.json')
    if not os.path.exists(info_path):
        return problems + ['build-info.json is missing; copy it from the english-database artifact']
    with open(info_path, encoding='utf-8') as file:
        info = json.load(file)
    if sha256_of(xz_chunks(xz_path)) != info['database']['sha256']:
        problems.append(
            'the decompressed lexical.db does not match build-info.json: the database was '
            'replaced without its build-info.json, or the other way round'
        )
    tools = info['marbleTools']
    if 'pullRequestHead' in tools:
        problems.append(
            'build-info.json describes a pull request build; rebuild with the workflow on '
            f'{MARBLE_TOOLS} main'
        )
    elif not on_main(tools['commit']):
        problems.append(f"marble-tools commit {tools['commit']} is not on {MARBLE_TOOLS} main")
    return problems


def main(argv):
    directory = argv[1] if len(argv) > 1 else 'lexical-db'
    problems = check(directory)
    for problem in problems:
        print(f'FAIL: {problem}')
    if not problems:
        print(f'{directory}: the database, its checksum and build-info.json agree')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
