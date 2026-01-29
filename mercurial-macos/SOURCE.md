# Source

## Technical Source

The Mercurial bundle in this directory was built as a standalone, universal (arm64 + x86_64) executable using PyInstaller and the official Mercurial wheel. It includes all required Python runtime components so that no external Python installation is needed.

This bundle uses PyInstaller's `--onedir` mode, which creates a directory structure containing the executable and all dependencies. The executables and dynamic libraries are merged into universal binaries using `lipo`, allowing for proper code signing of all components on macOS while maintaining compatibility with both architectures.

---

### 1. Working Directory

**Run from:** Any directory. This creates the working directory and the two required files.

Create a working directory (e.g. `/tmp/hg-build`) and add these two files:

- `hg.py` - launcher
- `hook-mercurial.py` - PyInstaller hook

**Option A – Create everything with one script:**

```bash
# --- Step 1: Create working directory and launcher/hook files ---
WORK_DIR="/tmp/hg-build"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

cat > hg.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import sys
from mercurial import dispatch

if __name__ == "__main__":
    sys.exit(dispatch.run())
PYTHON_EOF

cat > hook-mercurial.py << 'PYTHON_EOF'
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# include all mercurial submodules
hiddenimports = collect_submodules('mercurial')

# include data files (.toml, templates, config files, etc.)
datas = collect_data_files('mercurial', include_py_files=True)

# include compiled extension modules (.so / .dylib)
binaries = collect_dynamic_libs('mercurial')
PYTHON_EOF

ls -la
# You are now in the working directory; use this directory for Steps 3–7.
```

**Option B – Create files manually:**

Create `hg.py` (launcher):

```python
#!/usr/bin/env python3
import sys
from mercurial import dispatch

if __name__ == "__main__":
    sys.exit(dispatch.run())
```

Create `hook-mercurial.py` (PyInstaller hook) in the same directory. It tells PyInstaller to include Mercurial’s Python modules, compiled extensions, and data files:

```python
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# include all mercurial submodules
hiddenimports = collect_submodules('mercurial')

# include data files (.toml, templates, config files, etc.)
datas = collect_data_files('mercurial', include_py_files=True)

# include compiled extension modules (.so / .dylib)
binaries = collect_dynamic_libs('mercurial')
```

After Step 1, `cd` into the working directory (e.g. `cd /tmp/hg-build`) before running Step 2 or 3.

### 2. Prepare Virtual Environments for Each Architecture

**Run from:** Any directory.

P10S is expecting the specific version 7.0.2 in the filename. If you update this version you need to include the new version in the filename and update `.erb/scripts/download-mercurial-macos.js`.

```bash
# --- Step 2: Create venvs (run once) ---
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

**Run from:** Your working directory (the one that contains `hg.py` and `hook-mercurial.py`).

**Note:** We use `--onedir` mode instead of `--onefile`. This creates a directory with the executable and a `_internal` folder containing all dependencies, which allows proper code signing of all components.

```bash
# --- Step 3: Build arm64 and x86_64 (run from directory with hg.py and hook) ---
# ARM64 build (native)
source /tmp/hg-pyinstaller-venv-arm64/bin/activate
pyinstaller --onedir --additional-hooks-dir=. --name hg hg.py
mv dist/hg dist/hg-arm64
deactivate

# x86_64 build (Rosetta)
source /tmp/hg-pyinstaller-venv-x86/bin/activate
arch -x86_64 pyinstaller --onedir --additional-hooks-dir=. --name hg hg.py
mv dist/hg dist/hg-x86_64
deactivate
```

Why the hook is needed: Mercurial ships both Python modules and compiled C extensions plus data files. The hook ensures PyInstaller bundles `mercurial.cext` (compiled modules) and all required data files so runtime imports like `mercurial.cext.parsers` and `mercurial/configitems.toml` succeed.

After these builds complete, you should have:
```
dist/
├── hg-arm64/
│   ├── hg                    # ARM64 executable
│   └── _internal/            # ARM64 dependencies
└── hg-x86_64/
    ├── hg                    # x86_64 executable
    └── _internal/            # x86_64 dependencies
```

### 4. Create a Universal Binary Bundle

Do **4a** then **4b**, both from your working directory (same as Step 3; must contain a `dist/` folder from Step 3).

Since we're building for a universal Electron app, we need a universal Mercurial bundle: merge both architectures with `lipo`, then resolve symlinks so the bundle is code-signable.

---

#### 4a. Create and run the merge script

**Run from:** Your working directory (must contain `dist/` from Step 3).

This creates `dist/merge_internal.sh`, runs it to build `dist/hg-universal`, and merges Mach-O binaries + resolves symlinks during the merge.

```bash
# --- Step 4a: Create merge script and run it (run from working dir) ---
cd dist

# Create the universal bundle directory structure
mkdir -p hg-universal
mkdir -p hg-universal/_internal

lipo -create -output hg-universal/hg hg-arm64/hg hg-x86_64/hg
chmod +x hg-universal/hg

lipo -info hg-universal/hg
# Should output: "Architectures in the fat file: hg-universal/hg are: x86_64 arm64"

cat > merge_internal.sh << 'MERGE_SCRIPT'
#!/bin/bash
set -e

ARM64_DIR="hg-arm64/_internal"
X86_DIR="hg-x86_64/_internal"
UNIVERSAL_DIR="hg-universal/_internal"

# Counters for reporting
MERGED_COUNT=0
COPIED_COUNT=0
SKIPPED_COUNT=0

# Function to check if a file is a Mach-O binary
is_macho() {
    file "$1" | grep -q "Mach-O"
}

echo "Analyzing files in both architectures..."

# Get all unique relative paths from both architectures
find "$ARM64_DIR" -type f -o -type l | sed "s|^$ARM64_DIR/||" | sort -u > /tmp/arm64_files.txt
find "$X86_DIR" -type f -o -type l | sed "s|^$X86_DIR/||" | sort -u > /tmp/x86_files.txt
cat /tmp/arm64_files.txt /tmp/x86_files.txt | sort -u > /tmp/all_files.txt

TOTAL_FILES=$(wc -l < /tmp/all_files.txt)
echo "Found $TOTAL_FILES unique files to process"
echo ""

CURRENT=0

while IFS= read -r relpath; do
    CURRENT=$((CURRENT + 1))
    arm64_file="$ARM64_DIR/$relpath"
    x86_file="$X86_DIR/$relpath"
    universal_file="$UNIVERSAL_DIR/$relpath"
    
    # Create parent directory
    mkdir -p "$(dirname "$universal_file")"
    
    # Handle symlinks - replace with real file(s), universal when target is a binary in both arches
    if [ -L "$arm64_file" ]; then
        target=$(readlink "$arm64_file")
        
        if [ -z "$target" ]; then
            echo "[$CURRENT/$TOTAL_FILES] Warning: Empty symlink $relpath"
            COPIED_COUNT=$((COPIED_COUNT + 1))
            continue
        fi
        
        # Target path relative to _internal (symlink is in same tree)
        link_dir=$(dirname "$relpath")
        if [ "$link_dir" = "." ]; then
            target_relpath="$target"
        else
            target_relpath="$link_dir/$target"
        fi
        arm64_target="$ARM64_DIR/$target_relpath"
        x86_target="$X86_DIR/$target_relpath"
        
        # If target exists as Mach-O in BOTH arches, merge to universal (so arch -x86_64 works)
        if [ -f "$arm64_target" ] && [ -f "$x86_target" ] && is_macho "$arm64_target" && is_macho "$x86_target"; then
            echo "[$CURRENT/$TOTAL_FILES] Symlink -> universal binary: $relpath -> $target_relpath"
            if lipo -create -output "$universal_file" "$arm64_target" "$x86_target" 2>/dev/null; then
                if lipo -info "$universal_file" 2>/dev/null | grep -q "x86_64 arm64\|arm64 x86_64"; then
                    MERGED_COUNT=$((MERGED_COUNT + 1))
                    chmod --reference="$arm64_target" "$universal_file" 2>/dev/null || chmod u+x "$universal_file"
                else
                    cp "$arm64_target" "$universal_file"
                    COPIED_COUNT=$((COPIED_COUNT + 1))
                fi
            else
                cp "$arm64_target" "$universal_file"
                COPIED_COUNT=$((COPIED_COUNT + 1))
            fi
        elif [ -f "$arm64_target" ]; then
            cp "$arm64_target" "$universal_file"
            echo "[$CURRENT/$TOTAL_FILES] Resolved symlink: $relpath -> $target_relpath"
            COPIED_COUNT=$((COPIED_COUNT + 1))
        elif [ -f "$ARM64_DIR/$target" ]; then
            cp "$ARM64_DIR/$target" "$universal_file"
            echo "[$CURRENT/$TOTAL_FILES] Resolved symlink: $relpath -> $target"
            COPIED_COUNT=$((COPIED_COUNT + 1))
        else
            cp -L "$arm64_file" "$universal_file" 2>/dev/null || true
            echo "[$CURRENT/$TOTAL_FILES] Copied symlink target: $relpath"
            COPIED_COUNT=$((COPIED_COUNT + 1))
        fi
        continue
    fi
    
    # Case 1: File exists in both architectures
    if [ -f "$arm64_file" ] && [ -f "$x86_file" ]; then
        # Check if both are Mach-O binaries
        if is_macho "$arm64_file" && is_macho "$x86_file"; then
            echo "[$CURRENT/$TOTAL_FILES] Merging binary: $relpath"
            
            if lipo -create -output "$universal_file" "$arm64_file" "$x86_file" 2>/dev/null; then
                # Verify the merge was successful
                if lipo -info "$universal_file" 2>/dev/null | grep -q "x86_64 arm64\|arm64 x86_64"; then
                    MERGED_COUNT=$((MERGED_COUNT + 1))
                else
                    echo "  Warning: Merge verification failed, using arm64 version"
                    cp "$arm64_file" "$universal_file"
                    COPIED_COUNT=$((COPIED_COUNT + 1))
                fi
            else
                echo "  Warning: Cannot merge (incompatible), using arm64 version"
                cp "$arm64_file" "$universal_file"
                COPIED_COUNT=$((COPIED_COUNT + 1))
            fi
            
            # Preserve permissions
            chmod --reference="$arm64_file" "$universal_file" 2>/dev/null || chmod u+x "$universal_file"
        else
            # Not a binary - check if files are identical
            if cmp -s "$arm64_file" "$x86_file"; then
                # Files are identical, just copy one
                cp "$arm64_file" "$universal_file"
                COPIED_COUNT=$((COPIED_COUNT + 1))
            else
                # Files differ but aren't binaries - this is unusual
                echo "[$CURRENT/$TOTAL_FILES] Warning: Non-binary files differ: $relpath"
                echo "  Using arm64 version"
                cp "$arm64_file" "$universal_file"
                COPIED_COUNT=$((COPIED_COUNT + 1))
            fi
        fi
    
    # Case 2: File only exists in arm64
    elif [ -f "$arm64_file" ]; then
        echo "[$CURRENT/$TOTAL_FILES] ARM64 only: $relpath"
        cp "$arm64_file" "$universal_file"
        chmod --reference="$arm64_file" "$universal_file" 2>/dev/null || true
        COPIED_COUNT=$((COPIED_COUNT + 1))
    
    # Case 3: File only exists in x86_64
    elif [ -f "$x86_file" ]; then
        echo "[$CURRENT/$TOTAL_FILES] x86_64 only: $relpath"
        cp "$x86_file" "$universal_file"
        chmod --reference="$x86_file" "$universal_file" 2>/dev/null || true
        COPIED_COUNT=$((COPIED_COUNT + 1))
    
    else
        echo "[$CURRENT/$TOTAL_FILES] Warning: File not found in either architecture: $relpath"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    fi
    
done < /tmp/all_files.txt

# Summary
echo ""
echo "=================================================="
echo "Merge Complete!"
echo "=================================================="
echo "Universal binaries created: $MERGED_COUNT"
echo "Files copied: $COPIED_COUNT"
echo "Files skipped: $SKIPPED_COUNT"
echo "Total processed: $TOTAL_FILES"
echo "=================================================="

# Cleanup temp files
rm -f /tmp/arm64_files.txt /tmp/x86_files.txt /tmp/all_files.txt

MERGE_SCRIPT

chmod +x merge_internal.sh
./merge_internal.sh
```

The merge script merges Mach-O binaries with `lipo`, copies identical files once, resolves symlinks to real files (for code signing), and preserves permissions.

---

#### 4b. Create and run the resolve_symlinks script

**Run from:** Your working directory. Run this **after 4a** (so `dist/hg-universal` exists).

This creates `dist/resolve_symlinks.sh`, then runs it **from inside `dist/hg-universal`** with argument `.` so symlinks in the **universal bundle only** are resolved. **Do not run `./resolve_symlinks.sh` from `dist/`** — that would resolve symlinks in `hg-arm64` and `hg-x86_64` and can break future merges.

```bash
# --- Step 4b: Create resolve_symlinks script and run it (run from working dir) ---
cd dist/hg-universal

cat > resolve_symlinks.sh << 'RESOLVE_SCRIPT'
#!/usr/bin/env bash
set -e
DIR="${1:-.}"

# Guard: must be run from inside hg-universal, not from dist/
if [ -d "hg-arm64" ] && [ -d "hg-x86_64" ]; then
    echo "Error: Run this script from inside dist/hg-universal, not from dist/."
    echo "  Do: cd hg-universal && bash ../resolve_symlinks.sh ."
    exit 1
fi

resolve_symlinks() {
    local dir="$1"
    find "$dir" -type l | while read -r symlink; do
        target=$(readlink "$symlink")
        if cp -L "$symlink" "$symlink.tmp" 2>/dev/null; then
            rm "$symlink"
            mv "$symlink.tmp" "$symlink"
            echo "Resolved: $symlink -> $target"
        else
            symlink_dir=$(dirname "$symlink")
            if [[ "$target" != /* ]] && [ -f "$symlink_dir/$target" ]; then
                rm "$symlink"
                cp "$symlink_dir/$target" "$symlink"
                echo "Resolved: $symlink -> $symlink_dir/$target"
            elif [ -f "$target" ]; then
                rm "$symlink"
                cp "$target" "$symlink"
                echo "Resolved: $symlink -> $target"
            else
                echo "Warning: Cannot resolve symlink $symlink -> $target"
            fi
        fi
    done
}
resolve_symlinks "$DIR"
echo "Symlink resolution complete!"
RESOLVE_SCRIPT

chmod +x resolve_symlinks.sh
bash ./resolve_symlinks.sh .
cd ..
```

**To run symlink resolution by itself** (e.g. you already have `dist/hg-universal` and only want to fix symlinks):

1. `cd dist/hg-universal` (you must be inside the universal bundle).
2. `bash ../resolve_symlinks.sh .`

Do **not** run `./resolve_symlinks.sh` from `dist/` with no arguments — that resolves symlinks in `hg-arm64` and `hg-x86_64` instead of `hg-universal` and can break future Step 4a runs.

### 5. Verify the Universal Bundle

**Run from:** Your working directory (same as Step 3). Run this **after 4b** (so `dist/hg-universal` exists).

This creates `dist/verify_bundle.sh` with bash, then runs it (same pattern as Step 4b). Do not paste the verification commands directly into the terminal—they use process substitution and quoting that break.

```bash
# --- Step 5: Create verify_bundle.sh and run it (run from working dir) ---
cd dist

cat > verify_bundle.sh << 'VERIFY_SCRIPT'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/hg-universal"

echo "=== Verifying main executable ==="
lipo -info hg
# Expected: "Architectures in the fat file: hg are: x86_64 arm64"

echo ""
echo "=== Testing with native architecture ==="
./hg --version

echo ""
echo "=== Testing with x86_64 (Rosetta) ==="
arch -x86_64 ./hg --version

echo ""
echo "=== Testing with arm64 ==="
arch -arm64 ./hg --version

echo ""
echo "=== Verifying Python framework binary ==="
lipo -info _internal/Python3.framework/Versions/3.9/Python3

echo ""
echo "=== Checking merged binaries in _internal ==="
COUNT=0
while IFS= read -r f; do
    if [ $COUNT -lt 5 ]; then
        INFO=$(lipo -info "$f" 2>&1 | grep -o 'x86_64 arm64\|arm64 x86_64' || echo "single arch")
        echo "  $(basename "$f"): $INFO"
        COUNT=$((COUNT + 1))
    fi
done < <(find _internal/mercurial -name "*.so" -type f 2>/dev/null)

if [ $COUNT -eq 0 ]; then
    echo "  Warning: No .so files found"
fi

echo ""
echo "=== Directory structure ==="
ls -lah _internal/ | head -20

echo ""
echo "=== Size comparison ==="
du -sh ../hg-arm64 ../hg-x86_64 .

echo ""
echo "=== Checking for remaining symlinks ==="
SYMLINK_COUNT=$(find . -type l | wc -l | tr -d ' ')
if [ "$SYMLINK_COUNT" -gt 0 ]; then
    echo "Warning: Found $SYMLINK_COUNT symlinks remaining:"
    find . -type l -ls
    echo "These should be resolved before packaging"
else
    echo "✅ No symlinks found - bundle is ready for code signing"
fi

echo ""
echo "=== Testing actual Mercurial functionality ==="
HG_BIN="$(pwd)/hg"
TEMP_REPO=$(mktemp -d)
cd "$TEMP_REPO"
echo "Creating test repository..."
"$HG_BIN" init
echo "test content" > testfile.txt
"$HG_BIN" add testfile.txt
"$HG_BIN" commit -m "Test commit"
echo "Repository log:"
"$HG_BIN" log
cd ..
rm -rf "$TEMP_REPO"
echo "✅ Mercurial functionality test passed!"
VERIFY_SCRIPT

chmod +x verify_bundle.sh
bash verify_bundle.sh
cd ..
```

Expected output for version tests:
```
Mercurial Distributed SCM (version 7.0.2)
(see https://mercurial-scm.org for more information)

Copyright (C) 2005-2025 Olivia Mackall and others
This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
```

Expected lipo output for binaries:
```
Architectures in the fat file: [filename] are: x86_64 arm64
```

Expected size comparison:
```
28M    ../hg-arm64      # ARM64-only build
26M    ../hg-x86_64     # x86_64-only build  
~41M   .                # Universal build (smaller than 28M+26M due to deduplicated data files)
```

### 6. Inspect the Final Structure

Your `hg-universal` directory should look like this:

```
hg-universal/
├── hg                           # Universal binary (arm64 + x86_64)
└── _internal/                   # Merged dependencies
    ├── Python3                  # Python executable (symlinks resolved to actual file)
    ├── Python3.framework/       # Python framework
    │   └── Versions/3.9/
    │       └── Python3          # Universal Python binary
    ├── base_library.zip         # Python standard library (data)
    ├── python3.9/               # Python runtime files
    └── mercurial/               # Mercurial Python package
        ├── __init__.py
        ├── *.so                 # Universal Mercurial C extensions
        ├── cext/                # Compiled extensions
        │   ├── parsers.cpython-39-darwin.so  # Universal
        │   └── osutil.cpython-39-darwin.so   # Universal
        └── ... other modules and data files
```

You can inspect the structure with:

```bash
# --- Step 6 (optional): Inspect structure (run from working dir) ---
cd dist/hg-universal
ls -lah

ls -lah _internal/

ls -lah _internal/mercurial/cext/
```

### 7. Package and Checksum

**Run from:** Your working directory (the one that contains `dist/`). If you are currently in `dist/hg-universal` (e.g. after Step 5), run `cd ../..` first, then paste the block below.

```bash
# --- Step 7: Package and checksum (run from working dir; must have dist/hg-universal) ---
cd dist

# Create compressed archive
tar -c --xz -f hg-macos-universal_7.0.2.tar.xz hg-universal

# Generate SHA256 checksum
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

### PyInstaller
Source code: https://pyinstaller.org/
Copyright © 2010-2025 PyInstaller Development Team.
Licensed under the GNU General Public License version 2.0 (GPL-2.0).