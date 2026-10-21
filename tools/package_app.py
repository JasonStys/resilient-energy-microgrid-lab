"""Freeze and verify portable energy-lab bundles by Jason Stys. Index: docs/CODE_INDEX.md.

Function main; variables: fixed resources, notice paths, executable, archive digest. No installer/elevation.
"""

import hashlib
import platform
import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path


def main() -> None:
    """Include production assets, SQL and actual runtime notices; smoke before creating an unsigned ZIP."""
    root = Path(__file__).resolve().parents[1]
    if not (root / "web/dist/index.html").is_file():
        raise SystemExit("Build production assets first")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",
        "--name",
        "ResilientEnergyMicrogridLab",
    ]
    for source, destination in (
        ("web/dist", "web/dist"),
        ("gridlab/resources", "gridlab/resources"),
        ("LICENSE", "licenses/project"),
        ("licenses/PYTHON.txt", "licenses/python"),
        ("docs/THIRD_PARTY.md", "docs"),
        ("node_modules/vite/LICENSE.md", "licenses/vite"),
    ):
        command.extend(["--add-data", source + ":" + destination])
    package = distribution("pyinstaller")
    notices = [
        package.locate_file(path)
        for path in package.files or []
        if str(path).endswith("licenses/COPYING.txt")
    ]
    if len(notices) != 1:
        raise SystemExit("Expected locked PyInstaller license")
    command.extend(["--add-data", str(notices[0]) + ":licenses/pyinstaller"])
    if sys.platform == "linux":
        for notice in (
            "/usr/share/doc/libstdc++6/copyright",
            "/usr/share/doc/libgcc-s1/copyright",
            "/usr/share/common-licenses/GPL-3",
        ):
            source = Path(notice)
            if not source.is_file():
                raise SystemExit("Expected Ubuntu/Debian runtime notices")
            command.extend(
                ["--add-data", str(source) + ":licenses/compiler-runtime/" + source.parent.name]
            )
    command.append("launcher.py")
    subprocess.run(command, cwd=root, check=True, timeout=600)
    executable = (
        root
        / "dist/ResilientEnergyMicrogridLab"
        / (
            "ResilientEnergyMicrogridLab.exe"
            if sys.platform == "win32"
            else "ResilientEnergyMicrogridLab"
        )
    )
    subprocess.run(
        [sys.executable, "tools/smoke_app.py", str(executable)], cwd=root, check=True, timeout=120
    )
    slug = (
        f"resilient-energy-microgrid-lab-{platform.system().lower()}-{platform.machine().lower()}"
    )
    archive = Path(
        shutil.make_archive(
            str(root / "dist" / slug), "zip", root / "dist", "ResilientEnergyMicrogridLab"
        )
    )
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (root / "dist" / (slug + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"Verified portable bundle: {archive.name} SHA-256 {digest}")


if __name__ == "__main__":
    main()
