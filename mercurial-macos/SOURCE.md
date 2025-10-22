# Source

## Technical Source

The Mercurial bundle in this directory was built as a standalone, universal (arm64 + x86_64) executable using PyInstaller and the official Mercurial wheel. It includes all required Python runtime components so that no external Python installation is needed.

## Build Steps

### 1. Working Directory

Put the following files in a clean working directory (e.g. `/tmp/hg-build`):

- `hg.py` - launcher
- `hook-mercurial.py` - PyInstaller hook

#### `hg.py` (launcher)

```python
#!/usr/bin/env python3
import sys
from mercurial import dispatch

if __name__ == "__main__":
    sys.exit(dispatch.run())
```

#### `hook-mercurial.py` (PyInstaller hook)

This file instructs PyInstaller to include Mercurial's Python modules, compiled extensions and data files, place it in the same working directory as `hg.py`.

```python
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# include all mercurial submodules
hiddenimports = collect_submodules('mercurial')

# include data files (.toml, templates, config files, etc.)
datas = collect_data_files('mercurial', include_py_files=True)

# include compiled extension modules (.so / .dylib)
binaries = collect_dynamic_libs('mercurial')
```

### 2. Prepare Virtual Environments for each Architecture

P10S is expecting the specific version 7.0.2 in the filename. If you update this version you need to include the new version in the filename and update `.erb/scripts/download-mercurial-macos.js`.

```bash
# ARM64 (native)
python3 -m venv /tmp/hg-pyinstaller-venv-arm64
source /tmp/hg-pyinstaller-venv-arm64/bin/activate
pip install --upgrade pip
pip install pyinstaller mercurial==7.0.2
deactivate

# x86_64 (Rosetta)
arch -x86_64 python3 -m venv /tmp/hg-pyinstaller-venv-x86
source /tmp/hg-pyinstaller-venv-x86/bin/activate
pip install --upgrade pip
pip install pyinstaller mercurial==7.0.2
deactivate
```

### 3. Build Executables for Each Architecture Using the Hook and Launcher Files

Make sure you are in the directory with `hg.py` and `hook-mercurial.py`.

```bash
# ARM64 build (native)
source /tmp/hg-pyinstaller-venv-arm64/bin/activate
pyinstaller --onefile --additional-hooks-dir=. hg.py
mv dist/hg dist/hg-arm64
deactivate

# x86_64 build (Rosetta)
source /tmp/hg-pyinstaller-venv-x86/bin/activate
arch -x86_64 pyinstaller --onefile --additional-hooks-dir=. hg.py
mv dist/hg dist/hg-x86_64
deactivate
```

Why the hook is needed: Mercurial ships both Python modules and compiled C extensions plus data files. The hook ensures PyInstaller bundles `mercurial.cext` (compiled modules) and all required data files so runtime imports like `mercurial.cext.parsers` and `mercurial/configitems.toml` succeed. 

### 4. Create a universal binary 

```bash
cd dist
lipo -create -output hg hg-arm64 hg-x86_64
chmod +x hg
```

Verify:

```bash
lipo -info hg
./hg --version
```

Expected output:

```
Mercurial Distributed SCM (version 7.0.2)
(see https://mercurial-scm.org for more information)

Copyright (C) 2005-2025 Olivia Mackall and others
This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

### 5. Package and checksum

```bash
mkdir hg-universal
mv hg hg-universal/hg
tar -c --xz -f hg-macos-universal_7.0.2.tar.xz hg-universal
shasum -a 256 hg-macos-universal_7.0.2.tar.xz > hg-macos-universal_7.0.2.tar.xz.sha256
```

## Data Source

### Mercurial
Source code: https://www.mercurial-scm.org/
Copyright © 2005–2025 Olivia Mackall and contributors.
Licensed under the GNU General Public License, version 2 or any later version (GPL-2.0-or-later).

### Python
Source code: https://www.python.org/
Copyright © 2001–2025 Python Software Foundation.
Licensed under the Python Software Foundation License Version 2 (PSF-2.0).