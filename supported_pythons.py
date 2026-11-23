"""Read supported Python versions from the package classifiers."""

import argparse
import json
import re
import tomllib
from pathlib import Path


def supported_versions():
    project_file = Path(__file__).resolve().parent / "pyproject.toml"
    with project_file.open("rb") as file:
        classifiers = tomllib.load(file)["project"]["classifiers"]

    prefix = "Programming Language :: Python :: "
    versions = [
        classifier.removeprefix(prefix)
        for classifier in classifiers
        if classifier.startswith(prefix)
        and re.fullmatch(r"3\.\d+", classifier.removeprefix(prefix))
    ]
    if not versions or len(versions) != len(set(versions)):
        raise ValueError("Expected unique Python version classifiers in pyproject.toml")
    return sorted(versions, key=lambda version: tuple(map(int, version.split("."))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print a JSON array for CI")
    output.add_argument(
        "--latest", action="store_true", help="Print the newest supported version"
    )
    args = parser.parse_args()

    versions = supported_versions()
    if args.json:
        print(json.dumps(versions))
    elif args.latest:
        print(versions[-1])
    else:
        print(" ".join(versions))


if __name__ == "__main__":
    main()
