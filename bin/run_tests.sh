#!/bin/bash

echo Formatting code with black...
black .
echo

echo Running style checks with flake8...
flake8 .
echo

echo Running type checks with mypy...
mypy .
echo

echo Running tests...
pytest .
echo
