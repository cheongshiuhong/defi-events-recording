#!/bin/bash

echo
echo Running script [run_tests.sh]
echo

echo 1. Formatting code with black...
black .
echo

echo 2. Running style checks with flake8...
flake8 .
echo

echo 3. Running type checks with mypy...
mypy .
echo

echo 4. Running tests...
pytest .
echo
