#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ICU4CRelease:
    filename: str
    sha256: str
    platform: str
    arch: str


ICU_VERSION = "78.1"
ICU_RELEASES = [
    ICU4CRelease(
        filename="icu4c-78.1-Ubuntu22.04-x64.tgz",
        sha256="eeb150b28f824f645433ebacbbda8e8bac855bd3d98d0eea2b2e781b07ae1a37",
        platform="linux",
        arch="x86_64",
    ),
    ICU4CRelease(
        filename="icu4c-78.1-Fedora_Linux40-x64.tgz",
        sha256="92931fe41c13e0ad05656f4b5d661dd1b1c85d4e206303f299594f50f03c80db",
        platform="linux",
        arch="x86_64",
    ),
    ICU4CRelease(
        filename="icu4c-78.1-Win64-MSVC2022.zip",
        sha256="7cdb80d49dddc74371788dcbd55907ae4ac2353db38bca74f10c0560f1bb8538",
        platform="windows",
        arch="x86_64",
    ),
    ICU4CRelease(
        filename="icu4c-78.1-Win32-MSVC2022.zip",
        sha256="50e272cba56c6d635823fadee2dbbe7abc72627d73883740aafc3e222c12cfd9",
        platform="windows",
        arch="i686",
    ),
    ICU4CRelease(
        filename="icu4c-78.1-WinARM64-MSVC2022.zip",
        sha256="b603fc41bf150b271ded8280d03bdfe748401dad9b8dc0e0808f97482b177381",
        platform="windows",
        arch="aarch64",
    ),
]


def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash


def download_file(url: str, output_path: Path) -> None:
    subprocess.run(
        ["curl", "-fsSL", "-o", str(output_path), url],
        check=True,
    )


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)

    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(dest_dir)
    elif archive_path.name.endswith((".tgz", ".tar.gz")):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(dest_dir)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")


def get_release_for_platform() -> ICU4CRelease:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "aarch64"
    elif machine in ("i386", "i686"):
        machine = "i686"

    for release in ICU_RELEASES:
        if release.platform == system and release.arch == machine:
            return release

    for release in ICU_RELEASES:
        if release.platform == system:
            return release

    raise ValueError(f"No ICU4C release found for platform={system}, arch={machine}")


def check_homebrew_icu_version() -> bool:
    try:
        result = subprocess.run(
            ["brew", "list", "--versions", "icu4c"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print("ICU4C not installed via Homebrew", file=sys.stderr)
            print("Install with: brew install icu4c", file=sys.stderr)
            return False

        installed_version = result.stdout.strip()

        if ICU_VERSION in installed_version:
            print(f"ICU4C {ICU_VERSION} verified via Homebrew")
            return True
        else:
            print(
                f"Warning: Installed version doesn't match expected {ICU_VERSION}",
                file=sys.stderr,
            )
            print("Consider upgrading with: brew upgrade icu4c", file=sys.stderr)
            return False

    except FileNotFoundError:
        print("Homebrew not found on system", file=sys.stderr)
        print("Install Homebrew from https://brew.sh", file=sys.stderr)
        return False


def main() -> int:
    system = platform.system().lower()

    if system == "darwin":
        return 0 if check_homebrew_icu_version() else 1

    output_dir = Path.cwd() / "icu4c"

    try:
        release = get_release_for_platform()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    base_url = (
        f"https://github.com/unicode-org/icu/releases/download/release-{ICU_VERSION}"
    )
    url = f"{base_url}/{release.filename}"

    archive_path = Path(release.filename)

    try:
        download_file(url, archive_path)

        if not verify_sha256(archive_path, release.sha256):
            print(
                f"Error: SHA256 hash mismatch for {release.filename}", file=sys.stderr
            )
            archive_path.unlink(missing_ok=True)
            return 1

        extract_archive(archive_path, output_dir)
        print(f"ICU4C {ICU_VERSION} installed to {output_dir.absolute()}")
        return 0

    finally:
        archive_path.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
