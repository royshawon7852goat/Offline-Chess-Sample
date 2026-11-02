"""
SHADOW CHESS - Executable Builder & Packager
Builds standalone Windows .exe using PyInstaller and creates a distributable ZIP package.
"""

import os
import sys
import shutil
import subprocess
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
SCRATCH_DIR = os.path.dirname(BASE_DIR)
ZIP_OUTPUT = os.path.join(SCRATCH_DIR, "ShadowChess.zip")


def create_executable():
    """Compiles the game into a standalone Windows executable using PyInstaller."""
    print("=" * 60)
    print("SHADOW CHESS — BUILDING WINDOWS EXECUTABLE")
    print("=" * 60)

    icon_path = os.path.join(BASE_DIR, "assets", "icon.ico")
    assets_src = os.path.join(BASE_DIR, "assets")
    data_src = os.path.join(BASE_DIR, "data")

    # Command arguments for PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=ShadowChess",
        "--noconsole",
        f"--add-data={assets_src};assets",
        f"--add-data={data_src};data",
        "--clean",
        "--onedir",
        os.path.join(BASE_DIR, "main.py")
    ]

    if os.path.exists(icon_path):
        cmd.insert(4, f"--icon={icon_path}")

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode != 0:
        print("[Build] Warning: PyInstaller exited with non-zero code.")
        return False

    print("\n[Build] PyInstaller compilation completed successfully.")
    
    # Ensure assets and data are copied into dist/ShadowChess
    app_dist = os.path.join(DIST_DIR, "ShadowChess")
    if os.path.exists(app_dist):
        dist_assets = os.path.join(app_dist, "assets")
        dist_data = os.path.join(app_dist, "data")
        
        if not os.path.exists(dist_assets):
            shutil.copytree(assets_src, dist_assets)
        if not os.path.exists(dist_data):
            shutil.copytree(data_src, dist_data)
            
    return True


def package_zip():
    """Creates a complete ZIP distribution containing the project and executable."""
    print("\n" + "=" * 60)
    print("CREATING STANDALONE ZIP PACKAGE")
    print("=" * 60)

    if os.path.exists(ZIP_OUTPUT):
        os.remove(ZIP_OUTPUT)

    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include all project source files, assets, data, and tests
        for root, dirs, files in os.walk(BASE_DIR):
            # Exclude build artifacts and caches from source tree
            if any(part in ["build", "__pycache__", ".git", ".pytest_cache"] for part in root.split(os.sep)):
                continue

            for file in files:
                if file.endswith((".pyc", ".tmp", ".log")):
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.join("ShadowChess", os.path.relpath(file_path, BASE_DIR))
                zf.write(file_path, rel_path)

    print(f"[Package] Standalone ZIP created successfully at:\n  {ZIP_OUTPUT}")
    print(f"[Package] File size: {os.path.getsize(ZIP_OUTPUT) / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    success = create_executable()
    package_zip()
