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
# tag = "v78.3"
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
ICU_VERSION = "78.3"
BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/v78.3"

CHECKSUMS = {
    "icu-78.3-linux-aarch64.tar.gz": "16dbca31860da46d03ce8b7d1dadc23462ae9e9258fffd6f2e47e5308a6a4f52",
    "icu-78.3-linux-musl-aarch64.tar.gz": "64399d3509611584675cd21eab85ac0f858d9bdf9d3145f3628fde086cf4d178",
    "icu-78.3-linux-musl-x86_64.tar.gz": "61273a705e888c8aaaed8cd6f1ad95454ef3ba43e359a486b0ca18fdeaac9d92",
    "icu-78.3-linux-x86_64.tar.gz": "9d7861a5924fdfbdebbe898c7e4a6454a810c9c4c2b7c1eb787452495f36111f",
    "icu-78.3-macos-aarch64.tar.gz": "0bbaf9306d14db4ce02c1608ab3af8cbb1c3311f079aeae56a5db22a651d16ca",
    "icu-78.3-macos-x86_64.tar.gz": "4fbd86d56d938cc15b581beb2ebe37609fca3ad0689877d53a012895b9e5b534",
    "icu-78.3-windows-AMD64.tar.gz": "666428609339f1778eba38ef43d1f311abb0913ef762b718cc743c5af4d0502c",
    "icu-78.3-windows-ARM64.tar.gz": "d1d7bc676400f847502259a9955c7f63a7f78c69ec70cead6b57d3af7b090e0a",
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
