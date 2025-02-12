# Purpose
The purpose of this repo is to store dependencies needed for building/packaging Platform.Bible and/or Paratext 10 Studio that are at risk of becoming unavailable by other sources.

## Git LFS
Make sure you have `git-lfs` installed to use this repo appropriately. Here are [GitHub docs explaining how to do this](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage).

The purpose of [Git LFS](https://git-lfs.com/) is to limit the size of data stored in a local repository by allowing a remote server, like those on GitHub.com, to store all large files there. Generally speaking, it's a bad practice to store large, binary files in a Git repo the same way you would store source code. Git's internal storage and tooling wasn't designed for large file support.

If we don't use LFS, then this repository could become unusable after adding too many dependencies as Git commands would use too much RAM.

## Adding new dependencies
To add dependencies to this repo:
1. Download and validate the dependencies from wherever you are sourcing them.
2. Create a subdirectory in this repo where the dependencies should reside. Copy all the dependencies to this subdirectory.
3. Add a `SOURCE` file explaining where the dependencies originated and a `LICENSE` file that provides the license that applies to the dependencies.
4. Update the `.gitattributes` file in the root of this repository to include your new subdirectory. For example, the following would add all files in all subdirectories of `new_dependency` to be tracked by LFS except for `SOURCE` and `LICENSE`.
```
new_dependency/**/* filter=lfs diff=lfs merge=lfs -text
new_dependency/SOURCE -filter -diff -merge text
new_dependency/LICENSE -filter -diff -merge text
```
5. Once `.gitattributes` has been updated and saved, run `git add <new files>` (or use your Git client to add them in whatever way it allows) to stage your new files. Also make sure to add `.gitattributes` to the list of files to update.
6. From the command line, run `git lfs ls-files` to verify that your new files are being tracked by LFS before committing.
```sh
git lfs ls-files
```
7. Commit your changes and proceed as you normally would.