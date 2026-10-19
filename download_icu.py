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
# tag = "v78.3.post3"
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
BASE_URL = "https://github.com/adamchainz/icu4c-builds/releases/download/v78.3.post3"

CHECKSUMS = {
    "icu-78.3-linux-aarch64.tar.gz": "a50b679065b61feb43ffd84a55d2763920ae1e4b5e0672fc1da7676bdab59025",
    "icu-78.3-linux-musl-aarch64.tar.gz": "49801af7ddae4e1d969f81c233f6b80d2557bbd5cdffd5284f0e952ed3ba6400",
    "icu-78.3-linux-musl-x86_64.tar.gz": "650e60322439a2b57d44c752d027c0d2aaa80984d652f5569bbb343d574d5e75",
    "icu-78.3-linux-x86_64.tar.gz": "b4fc48948ecb6a068d33e7578eff26d039632e1414cc8ef5c333bf3c2c969b91",
    "icu-78.3-macos-aarch64.tar.gz": "45d3521f32cf1c9e4d750e8fb016eb21df19e4818f5e01812aba216c43591ac8",
    "icu-78.3-macos-x86_64.tar.gz": "4b058b77dff82a212254aeb68fd520fdaa50aa007d05425112ef1ae4131adb68",
    "icu-78.3-windows-AMD64.tar.gz": "e5b7501ea1831ed3e6da9d9c8f060780a676c27ffef4e293467d8285f1f82e03",
    "icu-78.3-windows-ARM64.tar.gz": "7878dc74452860998116004947ccd46994979227273e11e7978b50e4d9421461",
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

    license_path = Path(__file__).parent / "LICENSE-ICU"
    shutil.copyfile(icu_root / "LICENSE", license_path)
    print(f"Copied ICU license to: {license_path}")

    print(f"ICU extracted to: {icu_root}")
    print(f"Include directory: {icu_root / 'include'}")
    print(f"Library directory: {icu_root / 'lib'}")

    return icu_root


if __name__ == "__main__":
    download_and_extract()
