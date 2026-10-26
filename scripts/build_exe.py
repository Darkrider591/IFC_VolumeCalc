"""
Build script for packaging IFC BIM Attribute Parser into a standalone Windows .exe.
Uses PyInstaller with automatic collection of ifcopenshell and PySide6 dependencies.
"""
import os
import sys
import shutil
import subprocess
import PyInstaller.__main__

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY_POINT = os.path.join(BASE_DIR, "src", "main.py")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def build(onefile: bool = False):
    print("=" * 60)
    print(f"Starting PyInstaller build (onefile={onefile})...")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Entry Point:    {ENTRY_POINT}")
    print("=" * 60)

    # PyInstaller arguments
    args = [
        ENTRY_POINT,
        "--name=IFC_VolumeCalc",
        "--noconsole",  # GUI mode without black console window
        "--noconfirm",  # Overwrite output directory without confirmation
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--collect-all=ifcopenshell",
        "--collect-submodules=pandas",
        "--collect-submodules=openpyxl",
        "--collect-submodules=PySide6",
        "--hidden-import=src",
        "--hidden-import=src.core",
        "--hidden-import=src.ui",
    ]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    if onefile:
        exe_path = os.path.join(DIST_DIR, "IFC_VolumeCalc.exe")
        print(f"Build complete! Executable created at:\n{exe_path}")
    else:
        exe_path = os.path.join(DIST_DIR, "IFC_VolumeCalc", "IFC_VolumeCalc.exe")
        print(f"Build complete! Portable app created at:\n{exe_path}")
    print("=" * 60)
    return exe_path


if __name__ == "__main__":
    is_onefile = "--onefile" in sys.argv
    build(onefile=is_onefile)
