#!/bin/bash
export KB_DEPLOYMENT_CONFIG=deploy.toml
#jinja deploy.cfg.toml.jinja  > $KB_DEPLOYMENT_CONFIG

# FastAPI recommends running a single process service per docker container instance as below,
# and scaling via adding more containers. If we need to run multiple processes, use guvicorn as
# a process manger as described in the FastAPI docs


#!/bin/bash
python -m dotenv run jinja -f dotenv -o $KB_DEPLOYMENT_CONFIG deploy.cfg.toml.jinja

exec uvicorn --host 0.0.0.0 --port 5000 --factory src.factory:create_app