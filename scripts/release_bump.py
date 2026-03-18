from __future__ import annotations

import argparse
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
PYPROJECT_FILE = ROOT / "pyproject.toml"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"


def bump_version(current: str, release_type: str) -> str:
    major, minor, patch = (int(part) for part in current.split("."))
    if release_type == "major":
        return f"{major + 1}.0.0"
    if release_type == "minor":
        return f"{major}.{minor + 1}.0"
    if release_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported release type: {release_type}")


def update_pyproject(version: str) -> None:
    content = PYPROJECT_FILE.read_text(encoding="utf-8")
    if f'version = "{version}"' in content:
        return
    updated = re.sub(
        r'(?m)^version = "[^"]+"$',
        f'version = "{version}"',
        content,
        count=1,
    )
    if updated == content:
        raise RuntimeError("Failed to update version in pyproject.toml")
    PYPROJECT_FILE.write_text(updated, encoding="utf-8")


def ensure_changelog_heading(version: str) -> None:
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    heading = f"## {version}"
    if heading in content:
        return
    updated = content.rstrip() + f"\n\n## {version}\n\n- TBD\n"
    CHANGELOG_FILE.write_text(updated + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump Prompt Engine release version.")
    parser.add_argument(
        "--release-type",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Semantic version part to bump when --version is not provided.",
    )
    parser.add_argument(
        "--version",
        help="Explicit semantic version to set, for example 0.2.0.",
    )
    args = parser.parse_args()

    current = VERSION_FILE.read_text(encoding="utf-8").strip()
    version = args.version or bump_version(current, args.release_type)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Version must match semantic version format X.Y.Z")

    VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    update_pyproject(version)
    ensure_changelog_heading(version)
    print(version)


if __name__ == "__main__":
    main()
