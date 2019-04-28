#!/usr/bin/env bash
echo "mypy"
mypy --config-file=mypy.ini kantek

echo -e "\nflake8"
flake8 --config=.flake8 kantek

echo -e "\npylint"
pylint --rcfile=.pylintrc kantek
