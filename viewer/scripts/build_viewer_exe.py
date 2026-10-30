"""
Build script for packaging 3D Viewer into a standalone Windows .exe.
"""
import os
import sys
import PyInstaller.__main__

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENTRY_POINT = os.path.join(BASE_DIR, "viewer", "main.py")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def build(onefile: bool = False):
    print("=" * 60)
    print(f"Starting PyInstaller build for IFC_Viewer (onefile={onefile})...")
    print(f"Base Directory: {BASE_DIR}")
    print(f"Entry Point:    {ENTRY_POINT}")
    print("=" * 60)

    args = [
        ENTRY_POINT,
        "--name=IFC_Viewer",
        "--noconsole",
        "--noconfirm",
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--collect-all=ifcopenshell",
        "--collect-all=pyvista",
        "--collect-all=pyvistaqt",
        "--collect-all=vtkmodules",
        "--collect-submodules=pandas",
        "--collect-submodules=openpyxl",
        "--collect-submodules=PySide6",
        "--hidden-import=src",
        "--hidden-import=src.core",
        "--hidden-import=src.ui",
        "--hidden-import=viewer",
        "--hidden-import=viewer.core",
        "--hidden-import=viewer.ui",
    ]

    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    if onefile:
        exe_path = os.path.join(DIST_DIR, "IFC_Viewer.exe")
        print(f"Build complete! Executable created at:\n{exe_path}")
    else:
        exe_path = os.path.join(DIST_DIR, "IFC_Viewer", "IFC_Viewer.exe")
        print(f"Build complete! Portable app created at:\n{exe_path}")
    print("=" * 60)
    return exe_path


if __name__ == "__main__":
    is_onefile = "--onefile" in sys.argv
    build(onefile=is_onefile)
