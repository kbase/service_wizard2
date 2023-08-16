#!/bin/bash

if [[ -n $VIRTUAL_ENV ]]; then
    echo "Pipenv shell is  activated and ready for updates"
    rm Pipfile.lock
    pipenv install --dev
    pipenv sync
    echo "Updated dependencies for: `which python`"
else
    echo "Pipenv shell is not activated. Please 'pipenv shell' before running this script"
fi
