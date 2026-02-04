from __future__ import annotations

import hashlib
import platform
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

# [[[cog
# # Run with: uvx --from cogapp cog -r download_icu.py
# import json
# import subprocess
# from functools import partial
#
# tag = "v78.2.post4"
# icu_version = tag.lstrip("v").split(".post")[0]
#
#
# gh = partial(
#     subprocess.run,
#     capture_output=True,
#     text=True,
#     check=True,
# )
#
# result = gh(["gh", "release", "view", tag, "--repo", "adamchainz/icu4c-builds", "--json", "assets"])
# release_data = json.loads(result.stdout)
#
# checksums = {}
# for asset in release_data["assets"]:
#     name = asset["name"]
#     sha256 = asset["digest"].removeprefix("sha256:")
#     checksums[name] = sha256
#
# cog.outl(f'ICU_VERSION = "{icu_version}"')
# cog.outl(f'BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/{tag}"')
# cog.outl()
# cog.outl("CHECKSUMS = {")
# for name, sha in sorted(checksums.items()):
#     cog.outl(f'    "{name}": "{sha}",')
# cog.outl("}")
# ]]]
ICU_VERSION = "78.2"
BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/v78.2.post4"

CHECKSUMS = {
    "icu-78.2-linux-aarch64.tar.gz": "e02b5b98f37f591f1ebdd33bf2d1793b5f0537e3448eb14bccab8f650d6fecd0",
    "icu-78.2-linux-musl-aarch64.tar.gz": "c4c148542154d3c5553919496c1cfae8a12b293ec59ad5b1cd23b66765394c03",
    "icu-78.2-linux-musl-x86_64.tar.gz": "409528c4295ed354f1dab0230d229347651c0f971a14c8bbce454a72c38a935a",
    "icu-78.2-linux-x86_64.tar.gz": "5e249aa62ed73047640d5d78b5e650dbdc4da0b9b618df064a0c6425a63fc83a",
    "icu-78.2-macos-aarch64.tar.gz": "bac7d114fa69cc1dca9353548395e4d57542468518d0e41b3aeb66b9c24eb4a2",
    "icu-78.2-macos-x86_64.tar.gz": "3a755f1a58ebff19deed8863ce74d51b32c008091b2f1c3612e5913f1c1817d8",
    "icu-78.2-windows-AMD64.tar.gz": "329cbcc0e0f811ea189f9d1d138d2c17506168e1cdae9672e68be649cdea4a9e",
    "icu-78.2-windows-ARM64.tar.gz": "6e7e532db64b577a6d8c7f5dc908e19488fb5ad0062b052b56751590cba3ecd5",
}
# [[[end]]]


def get_platform_info() -> tuple[str, str, str]:
    system = sys.platform
    machine = platform.machine().lower()

    if system.startswith("linux"):
        is_musl = False
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "alpine" in content or "musl" in content:
                    is_musl = True
        except FileNotFoundError:
            pass

        libc = "musl" if is_musl else ""

        if machine in ("x86_64", "amd64"):
            arch = "x86_64"
        elif machine in ("aarch64", "arm64"):
            arch = "aarch64"
        elif machine in ("i386", "i686", "x86"):
            arch = "i686"
        else:
            raise ValueError(f"Unsupported Linux architecture: {machine}")

        return "linux", libc, arch

    elif system == "darwin":
        if machine in ("x86_64", "amd64"):
            arch = "x86_64"
        elif machine in ("arm64", "aarch64"):
            arch = "aarch64"
        else:
            raise ValueError(f"Unsupported macOS architecture: {machine}")

        return "macos", "", arch

    elif system == "win32":
        if machine in ("x86_64", "amd64"):
            arch = "AMD64"
        elif machine == "arm64":
            arch = "ARM64"
        elif machine in ("i386", "i686", "x86"):
            arch = "x86"
        else:
            raise ValueError(f"Unsupported Windows architecture: {machine}")

        return "windows", "", arch

    else:
        raise ValueError(f"Unsupported platform: {system}")


def get_filename(os_name: str, libc: str, arch: str) -> str:
    if os_name == "linux":
        if libc == "musl":
            return f"icu-{ICU_VERSION}-linux-musl-{arch}.tar.gz"
        else:
            return f"icu-{ICU_VERSION}-linux-{arch}.tar.gz"
    elif os_name == "macos":
        return f"icu-{ICU_VERSION}-macos-{arch}.tar.gz"
    elif os_name == "windows":
        return f"icu-{ICU_VERSION}-windows-{arch}.tar.gz"
    else:
        raise ValueError(f"Unknown OS: {os_name}")


def verify_checksum(filepath: Path, expected: str) -> None:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    actual = sha256.hexdigest()
    if actual != expected:
        raise ValueError(
            f"Checksum mismatch for {filepath.name}:\n  Expected: {expected}\n  Got:      {actual}"
        )


def download_and_extract() -> Path:
    os_name, libc, arch = get_platform_info()
    filename = get_filename(os_name, libc, arch)
    expected_checksum = CHECKSUMS.get(filename)

    if not expected_checksum:
        raise ValueError(f"No checksum found for {filename}")

    url = f"{BASE_URL}/{filename}"

    if os_name == "windows":
        install_dir = Path("C:/icu")
    else:
        install_dir = Path("/tmp/icu")

    install_dir.mkdir(parents=True, exist_ok=True)
    tarball_path = install_dir / filename

    print(f"Downloading {url}...")
    urllib.request.urlretrieve(url, tarball_path)

    print("Verifying checksum...")
    verify_checksum(tarball_path, expected_checksum)

    icu_root = install_dir / "icu"
    if icu_root.exists():
        shutil.rmtree(icu_root)

    print(f"Extracting to {install_dir}...")
    with tarfile.open(tarball_path) as tar:
        members = tar.getmembers()
        if not members:
            raise ValueError("Tarball is empty")

        root_name = members[0].name.split("/")[0]

        for member in members:
            if member.name.startswith(root_name + "/"):
                member.name = "icu/" + member.name[len(root_name) + 1 :]
                tar.extract(member, install_dir)

    tarball_path.unlink()

    print(f"ICU extracted to: {icu_root}")
    print(f"Include directory: {icu_root / 'include'}")
    print(f"Library directory: {icu_root / 'lib'}")

    return icu_root


if __name__ == "__main__":
    download_and_extract()
