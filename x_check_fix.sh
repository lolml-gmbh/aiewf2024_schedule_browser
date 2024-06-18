#!/bin/bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "${DIR}"
export PYTHONPATH="${DIR}"

python package_versions.py update
python package_versions.py check

ruff format .
ruff check --fix .
