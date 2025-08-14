# Source

## Technical Source

The Mercurial bundle in this directory was built from MacPorts with universal architecture support.

To build:

1. Install Mercurial with universal architecture:
   ```bash
   sudo port install mercurial +universal
   ```
2. Copy the Mercurial launcher and Python runtime:
   ```bash
   mkdir hg-universal
   cp /opt/local/bin/hg hg-universal/
   cp -R /opt/local/Library/Frameworks/Python.framework/Versions/3.13 hg-universal/
   ```
3. Test:
   ```bash
   ./hg-universal/hg version
   ```
4. Create compressed archive:
   ```bash
   tar -c --xz -f hg-macos-universal.tar.xz hg-universal
   ```
5. Generate checksum file:
   ```bash
   shasum -a 256 hg-macos-universal.tar.xz > hg-macos-universal.tar.xz.sha256
   ```

The resulting archive contains a universal (x86_64 + arm64) Mercurial binary and a self-contained Python 3.13 runtime with all required site-packages.

## Data Source

### Mercurial
Source code: https://www.mercurial-scm.org/
Copyright © 2005–2025 Olivia Mackall and contributors.
Licensed under the GNU General Public License, version 2 or any later version (GPL-2.0-or-later).

### Python
Source code: https://www.python.org/
Copyright © 2001–2025 Python Software Foundation.
Licensed under the Python Software Foundation License Version 2 (PSF-2.0).