#!/bin/bash

set -e
set -u

cd "$( dirname "${BASH_SOURCE[0]}" )"
export PYTHONPATH='.'
streamlit run app.py --server.port=8080
