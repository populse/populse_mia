"""
Parses and aggregates Python package dependencies from multiple local
projects.

This script collects dependencies from either `pyproject.toml` or
`setup.py` (with an associated info file) for a set of packages.
It then deduplicates, filters out local packages, and writes
a cleaned list of external dependencies to a `requirements-all.txt`
file in the parent directory.
"""

###############################################################################
# Populse_mia - Copyright (C) IRMaGe/CEA, 2018
# Distributed under the terms of the CeCILL license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL_V2.1-en.html
# for details.
###############################################################################

try:
    import tomllib  # Python 3.11+

except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11

import re
from collections import defaultdict
from pathlib import Path


def parse_setup_py(setup_path: Path, info_path) -> list[str]:
    """
    Parses a setup.py file using its associated info.py to extract
    dependencies.

    :param setup_path (Path): The path to the `setup.py` file.
    :param info_path (dict): A mapping of setup.py paths to their
                             corresponding info.py files.

    :returns (List[str]): A list of package requirements.
    """
    release_info = {}

    with open(info_path[setup_path]) as f:
        code = f.read()
        exec(code, release_info)

    return release_info["REQUIRES"]


def parse_pyproject_toml(path: Path) -> list[str]:
    """
    Parses a pyproject.toml file to extract dependencies in PEP 621 or
    Poetry format.

    :param path (Path): The path to the `pyproject.toml` file.

    :returns (List[str]): A list of package requirements.
    """

    with open(path, "rb") as f:
        data = tomllib.load(f)

    deps = []

    # PEP 621-compliant project metadata
    if "project" in data and "dependencies" in data["project"]:
        deps.extend(data["project"]["dependencies"])

    # Poetry-style
    elif (
        "tool" in data
        and "tool" in data["tool"]
        and "dependencies" in data["tool"]["tool"]
    ):
        deps_dict = data["tool"]["tool"]["dependencies"]
        deps.extend(
            f"{pkg}{v if isinstance(v, str) else ''}"
            for pkg, v in deps_dict.items()
            if pkg.lower() != "python"
        )

    return deps


def collect_dependencies(package_dirs: list[Path], info_path) -> set[str]:
    """
    Collects dependencies from a list of package directories.

    :param package_dirs (List[Path]): List of paths to package directories.
    :param info_path (dict): Mapping from setup.py paths to corresponding
                             info.py files.

    :returns (Set[str]): A set of all collected dependencies.
    """
    deps = set()

    for pkg_path in package_dirs:

        if (pkg_path / "pyproject.toml").is_file():
            pkg_deps = parse_pyproject_toml(pkg_path / "pyproject.toml")
            print(f"Parsed pyproject.toml for {pkg_path.name}: {pkg_deps}")

        elif (pkg_path / "setup.py").is_file():
            pkg_deps = parse_setup_py(pkg_path / "setup.py", info_path)
            print(f"Parsed setup.py for {pkg_path.name}: {pkg_deps}")

        else:
            print(f"Warning: No setup.py or pyproject.toml in {pkg_path}")
            continue

        deps.update(pkg_deps)

    return deps


def main():
    """
    Main function that coordinates dependency collection, filtering, and output
    writing.
    """
    base_dir = Path(__file__).resolve().parent
    package_dirs = [
        base_dir.parent / "populse_db",
        base_dir.parent / "capsul",
        base_dir,  # current dir: populse-mia
        base_dir.parent / "soma-base",
        base_dir.parent / "soma-workflow",
        base_dir.parent / "mia_processes",
    ]
    info_path = {
        base_dir.parent
        / "capsul"
        / "setup.py": base_dir.parent
        / "capsul"
        / "capsul"
        / "info.py",
        base_dir.parent
        / "soma-base"
        / "setup.py": base_dir.parent
        / "soma-base"
        / "python"
        / "soma"
        / "info.py",
        base_dir.parent
        / "soma-workflow"
        / "setup.py": base_dir.parent
        / "soma-workflow"
        / "python"
        / "soma_workflow"
        / "info.py",
    }
    deps = collect_dependencies([p.resolve() for p in package_dirs], info_path)
    # Packages to exclude from final requirements
    local_packages = {
        "populse-mia",
        "populse-db",
        "mia_processes",
        "soma-workflow",
        "soma-base",
        "capsul",
    }

    # Normalize, deduplicate and keep the most specific version

    versioned_deps = defaultdict(list)
    for dep in deps:
        name = re.split(r"[<=>]", dep, 1)[0].strip().lower()
        versioned_deps[name].append(dep)

    cleaned_deps = []
    for name, entries in versioned_deps.items():
        if name in local_packages:
            continue
        # Prefer the entry with a version specifier if there are multiple
        best = max(entries, key=lambda s: len(re.findall(r"[<=>]", s)))
        cleaned_deps.append(best)

    output_file = base_dir.parent / "requirements-all.txt"
    output_file.write_text("\n".join(sorted(cleaned_deps)))
    print(f"Wrote {len(cleaned_deps)} filtered dependencies to {output_file}")
    print(sorted(cleaned_deps))


if __name__ == "__main__":
    main()
