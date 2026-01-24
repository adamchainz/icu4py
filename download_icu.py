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
# tag = "v78.2.post2"
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
BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/v78.2.post2"

CHECKSUMS = {
    "icu-78.2-linux-aarch64.tar.gz": "5c166b6b8696f5e056aaba30ae5ce55b79dc93e102aaa6aa781a15b6c8ecad64",
    "icu-78.2-linux-i686.tar.gz": "aef6d5d9c20b09a7b8ce3ac1abd355f1bdc182013d5a1aaf0298c990324434e3",
    "icu-78.2-linux-musl-aarch64.tar.gz": "abd2bff2feafa56186070333e1426d36bfcb507c76f2cc1e07d933bc11504344",
    "icu-78.2-linux-musl-i686.tar.gz": "0b7bafcf2d9d72e22a8396b39c1213da077ccc55d5edaa0b0efa204033ee8d98",
    "icu-78.2-linux-musl-x86_64.tar.gz": "4469eaf4d41b1ff160e8f844e6b0e17c7b362230c6a5f765bdff2ca3a456b7ca",
    "icu-78.2-linux-x86_64.tar.gz": "617503c6e8f9aa19d079187feb78a86be09d901b2f90b36a7ff1d2098a9f8287",
    "icu-78.2-macos-arm64.tar.gz": "16f97976388e79f50845e404e3a9b5cc4f48f386e54aa96f4a90620d4c69ff09",
    "icu-78.2-macos-x86_64.tar.gz": "cf4a1f05d7d9642aa9f6643cb79b8474cb8c9becbfc3c87d35bdbdf7c281f8f2",
    "icu-78.2-windows-AMD64.tar.gz": "bad9974e21e1b4f22e59fcb58f1766ccce5676c13896b007be99e097e54a60ec",
    "icu-78.2-windows-ARM64.tar.gz": "df7359d39eaa71bee355634486fb1f7a781f7acfc453f3145f0258c5800708d8",
    "icu-78.2-windows-x86.tar.gz": "c9aae81ebb8093e18c0c27bcec34be980c63fd8544fc5b2b999067b4541a2c41",
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
