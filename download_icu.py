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
# tag = "v78.2.post1"
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
BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/v78.2.post1"

CHECKSUMS = {
    "icu-78.2-linux-aarch64.tar.gz": "22b355555b9180a35e5aea1bc44c99c2769ca055e1de49617de8715c6bc8b39e",
    "icu-78.2-linux-i686.tar.gz": "b1f8447cd390c8120aa46fa3b1130ee9336f49004274136b6afd02c9bdb4741d",
    "icu-78.2-linux-musl-aarch64.tar.gz": "d91836ce3b02710a6547a0bb6914ecbe467550deeb7e6ecb8e5c158621413381",
    "icu-78.2-linux-musl-i686.tar.gz": "f3bf96cad253e68f70a792b00f158e7bda86e8edd5f1d2865dd9cac96a02e41f",
    "icu-78.2-linux-musl-x86_64.tar.gz": "ac6175d1a01188b249225e4664e379c31c9e5e76d476a9258ad68b159cd2e39c",
    "icu-78.2-linux-x86_64.tar.gz": "b13660d8d0705aca181e0739f258176de9908f88b7ec318cc66fcba5b03ebe21",
    "icu-78.2-macos-arm64.tar.gz": "2982c4fd0c36649ffe430b55889621101fb848d623f195771f28eb16a2be99e1",
    "icu-78.2-macos-x86_64.tar.gz": "67247ae7d5ca0c57bbbfc020a839d7aea92281690c57a223443d2ba05ee7370a",
    "icu-78.2-windows-AMD64.tar.gz": "65ed1428f5e69b74d4882e51fa3048e7057186d28c688fa03d77c673d3c00a40",
    "icu-78.2-windows-ARM64.tar.gz": "37f62ae11d94deb187a7656a6f9fe91bd9e69561ea2d82856f551f822c40340b",
    "icu-78.2-windows-x86.tar.gz": "834f680bb7982c1add9629f65a2eaf23a2a882736ecc5676d2fe62aa91a5f03d",
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
            arch = "arm64"
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
