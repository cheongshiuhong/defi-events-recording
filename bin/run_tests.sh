#!/bin/bash

echo
echo Running script [run_tests.sh]
echo

echo 1. Running style checks with flake8...
flake8 .
echo

echo 2. Running type checks with mypy...
mypy .
echo

echo 3. Running tests...
pytest .
echo
