#!/bin/bash

if [[ -n $VIRTUAL_ENV ]]; then
    echo "Pipenv shell is  activated and ready for updates"
    pipenv install --dev
    #pipenv requirements > requirements_generated.txt
    pipenv sync
    echo "Updated dependencies for: `which python`"
else
    echo "Pipenv shell is not activated. Please 'pipenv shell' before running this script"
fi


