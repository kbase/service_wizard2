#!/bin/bash

# Check if a Pipenv environment already exists
if pipenv --venv &>/dev/null; then
    echo "Pipenv environment already exists. No need to bootstrap"
else
    # If Pipenv environment doesn't exist, create a new one
    pipenv --python 3.11-service_wizard2
    echo "Created new Pipenv environment."

    # Install dependencies
    pipenv install --dev
#    pipenv requirements > requirements_generated.txt
    pipenv sync
    echo "Installed dependencies."
fi

# Activate the Pipenv environment
pipenv shell

# Sync the dependencies
pipenv sync
