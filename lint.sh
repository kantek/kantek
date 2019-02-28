#!/usr/bin/env bash
echo "mypy" && mypy --config-file=mypy.ini kantek && echo "flake8" && flake8 --config=.flake8 kantek && echo "pylint" && pylint --rcfile=.pylintrc kantek
