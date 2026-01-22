from __future__ import annotations

import hashlib
import platform
import sys
import tarfile
import urllib.request
from pathlib import Path

ICU_VERSION = "78.2"
RELEASE_TAG = f"v{ICU_VERSION}"
BASE_URL = f"https://github.com/adamchainz/icu4c-builds/releases/download/{RELEASE_TAG}"

CHECKSUMS = {
    "icu-78.2-linux-aarch64.tar.gz": "a82d39ce630137380fd7b944bbb5fe0a1cfd053b6a42057bfbe7c0df16499d6d",
    "icu-78.2-linux-i686.tar.gz": "d2acb369e8d0fc280d99072a5355fb4f9714fad6b78d8af7f5d831de9569b59f",
    "icu-78.2-linux-musl-aarch64.tar.gz": "74041415cad18f5bbc393d8e71b8e58eb3dc7b675725047a8cd550587717732e",
    "icu-78.2-linux-musl-i686.tar.gz": "0800feac51f7e859532f7fe474b296eb6a2a1c7b0ae1bc06fe3452727aa241c2",
    "icu-78.2-linux-musl-x86_64.tar.gz": "be602f1ddf70cdc6bb5b6dcfea34719ea99f6898b732b2260c3750afbb597317",
    "icu-78.2-linux-x86_64.tar.gz": "91542ea97fff4cc304028f02289070c560b88d5ab52490edf8ba5f38f6d97583",
    "icu-78.2-macos-arm64.tar.gz": "09ef21f2b9fbf293a2b0c6f08202a685d82d54df1da5639e6a2917a208470be0",
    "icu-78.2-macos-x86_64.tar.gz": "cef0cd0b19180b2a71d6a1153a673c194e586780132981c3dc902bbaf31ddf5f",
    "icu-78.2-windows-AMD64.tar.gz": "089a5e481a1b722f89a41b3a801115b374ecd1c8d550ccabb431fb7d4d6720df",
    "icu-78.2-windows-ARM64.tar.gz": "63ca5a82b83aa10b6c840b91db696f7076c8d366cf257ec831c337de13d747bf",
    "icu-78.2-windows-x86.tar.gz": "bd98acd38e89da04c1d7bbd76c73c37cd8f6199a4c6e79ae499e5fbb693e21dc",
}


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

    print(f"Extracting to {install_dir}...")
    with tarfile.open(tarball_path) as tar:
        tar.extractall(install_dir)

    tarball_path.unlink()

    icu_root = install_dir / "icu"
    print(f"ICU extracted to: {icu_root}")
    print(f"Include directory: {icu_root / 'include'}")
    print(f"Library directory: {icu_root / 'lib'}")

    return icu_root


if __name__ == "__main__":
    download_and_extract()
