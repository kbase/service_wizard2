#!/bin/bash


if [ -z "$GITHUB_ACTION" ]; then
    echo "This step is intended to be run from Github Actions"
    pip install pipenv
    rm Pipfile.lock
    pipenv install --dev
    pipenv sync --system --dev
    exit 0
fi


if [[ -n $VIRTUAL_ENV ]]; then
    echo "Pipenv shell is  activated and ready for updates"

    pipenv install --dev
    pipenv sync
    echo "Updated dependencies for: `which python`"
else
    echo "Pipenv shell is not activated. Please 'pipenv shell' before running this script"
fi
