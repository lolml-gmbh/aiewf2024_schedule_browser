# Copyright (c) 2024 [LOLML GmbH](https://lolml.com/), Julian Wergieluk, George Whelan
import json
import os
import subprocess
import sys
from dataclasses import dataclass

DEFAULT_CMP_OP = ">="
DEFAULT_ENV_NAME = "aiewf"
PACKAGE_MANAGER = os.getenv("PACKAGE_MANAGER", "micromamba")


@dataclass
class PackageSpec:
    name: str
    version: str
    cmp_op: str


def read_package_specs(file_path: str) -> list[PackageSpec]:
    with open(file_path) as file:
        package_list = file.read().splitlines()

    package_data = []
    for i, package_line in enumerate(package_list):
        package_line = package_line.strip()
        if package_line.startswith("#"):
            continue
        if not package_line:
            continue
        cmp_op = ""
        version = ""
        if "<" in package_line and "<=" not in package_line:
            raise ValueError(f"Package line {i}: {package_line}: operator `<` is not supported")
        if ">" in package_line and ">=" not in package_line:
            raise ValueError(f"Package line {i}: {package_line}: operator `>` is not supported")
        if "<=" in package_line:
            cmp_op = "<="
        if ">=" in package_line:
            cmp_op = ">="
        if "==" in package_line:
            cmp_op = "=="
        if cmp_op:
            package_name, version = package_line.split(cmp_op)
        else:
            package_name = package_line

        package_data.append(PackageSpec(name=package_name, version=version, cmp_op=cmp_op))
    return package_data


def write_package_specs(file_path: str, package_specs: list[PackageSpec]):
    spec_lines = []
    for package_spec in package_specs:
        if package_spec.cmp_op:
            spec_lines.append(f"{package_spec.name}{package_spec.cmp_op}{package_spec.version}")
        else:
            spec_lines.append(f"{package_spec.name}")

    # spec_lines.sort()
    spec = "\n".join(spec_lines) + "\n"
    with open(file_path, "w") as f:
        f.write(spec)


def get_env_package_versions(env_name: str) -> dict[str, str]:
    command = f"{PACKAGE_MANAGER} list -n {env_name} --json".split(" ")
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout
    output_data = json.loads(output)

    env_package_versions = {}
    for p in output_data:
        env_package_versions[p["name"]] = p["version"]

    command = "pip list --format=json".split(" ")
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    output = result.stdout
    output_data = json.loads(output)
    for p in output_data:
        if p["name"] in env_package_versions:
            continue
        env_package_versions[p["name"]] = p["version"]
    return env_package_versions


def update_package_versions_from_env(
    package_specs: list[PackageSpec], env_name: str, ignore_missing: bool = False
) -> list[PackageSpec]:
    env_package_versions = get_env_package_versions(env_name)
    package_specs_dict = {p.name: p for p in package_specs}
    updated_package_specs = []
    for name, spec in package_specs_dict.items():
        if name in env_package_versions:
            env_version = env_package_versions[name]
            if spec.version and env_version < spec.version:
                raise ValueError(
                    f"Environment {env_name} has version {env_version} of package {name}, but "
                    f"{spec.version} is required"
                )
            cmp_op = spec.cmp_op if spec.cmp_op else DEFAULT_CMP_OP
            updated_spec = PackageSpec(name=name, version=env_version, cmp_op=cmp_op)
            updated_package_specs.append(updated_spec)
        elif not ignore_missing:
            raise ValueError(f"Package {name} not found in environment {env_name}")
        else:
            updated_package_specs.append(spec)
    return updated_package_specs


def update_requirements(env_name: str, path: str, ignore_missing: bool = False) -> None:
    requirements = read_package_specs(path)
    updated_requirements = update_package_versions_from_env(requirements, env_name, ignore_missing)
    write_package_specs(path, updated_requirements)


def check_requirements(env_name: str, path: str) -> None:
    # check if the environment has the required packages
    requirements = read_package_specs(path)
    env_package_versions = get_env_package_versions(env_name)
    for package in requirements:
        if package.name not in env_package_versions:
            raise ValueError(f"Package '{package.name}' not found in the environment '{env_name}'")


def main(args: list[str]) -> None:
    if not args:
        print("Usage: python package_versions.py [update|check] [env_name]")
        return
    env = args[1] if len(args) > 1 else DEFAULT_ENV_NAME
    if not env:
        print("No environment name provided")
        return

    if args[0] in ("update", "u"):
        update_requirements(env, "conda_packages.txt")
        update_requirements(env, "pip_packages.txt", True)
        return
    if args[0] in ("check", "c"):
        check_requirements(env, "conda_packages.txt")
        check_requirements(env, "pip_packages.txt")
        return


if __name__ == "__main__":
    main(sys.argv[1:])
