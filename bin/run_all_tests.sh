#!/bin/bash

run_tests() {
    echo
    echo Running tests...
    echo

    echo 1. Running style checks with flake8...
    flake8 . --count --exit-zero
    echo

    echo 2. Running type checks with mypy...
    mypy --install-types --non-interactive .
    echo

    echo 3. Running tests...
    pytest .
    echo
}

echo
echo Going into services/interface...
echo

cd services/interface
run_tests


echo
echo Going into services/interface...
echo

cd ../recording
run_tests
