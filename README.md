# Service Wizard 2
[![codecov](https://codecov.io/gh/kbase/service_wizard2/graph/badge.svg?token=JxuP8XOFwU)](https://codecov.io/gh/kbase/service_wizard2)

The service wizard manages the lifecycle of "dynamic services" in KBase.
The previous service wizard talked directly to rancher1, this one talks directly to kubernetes.
Dynamic services are responsible for providing data and/or UI components for the KBase UI and Narrative.

# Known issues

* Still does not allow you to update environmental variables for a service that was launched once, it requires a new
  deployment.
* Starting up too many services causes the status endpoint to not respond.
* Only supports one type of toleration for now.
* Doesn't completely support multiple replicas for now.
* Doesn't support volumes, only bind mounts
* Doesn't yet support forcing a dynamic service to land on a specific host (e.g. staticnarrative service,
  htmlfilsetservice) or define behavior for multiple replicas on specific hosts
* If the catalog admin is not valid, you get an authentication error, but its not clear that its the auth token from the
  service rather than from the user request

# Environment Variables

The following environment variables are used to configure the application.
Ensure that all the required environment variables are properly set before running the application.
See [.env](.env) file for example

## *Required Environment Variables*

## Client URLs

- `AUTH_SERVICE_URL`: Defines the URL of the authentication service used for user authentication and authorization.
- `CATALOG_URL`: Sets the URL for the catalog service, which manages and provides access to application catalogs.
- `AUTH_LEGACY_URL`: Defines the URL of the legacy authentication service to be appended to the env inside the dynamic
  service

## Service Wizard URLs

- `EXTERNAL_SW_URL`: Specifies the URL for the external Service Wizard. Also serves as identifier for Sentry
- `EXTERNAL_DS_URL`: Sets the URL for the external Dynamic Services.
- `KBASE_SERVICES_ENDPOINT`: Specifies the endpoint URL for the KBase service, which provides various functionalities
  for the application.
- `KBASE_ROOT_ENDPOINT`: Specifies the root endpoint URL for KBase.
- `ROOT_PATH`: Specifies the root path for the application.

## SW Admin Stuff

- `KBASE_ADMIN_ROLE`: The role identifier for a KBase administrator within the application.
- `CATALOG_ADMIN_ROLE`: The role identifier for a Catalog administrator within the application.
- `SERVICE_WIZARD_ADMIN_ROLE`: The role identifier for a Service Wizard administrator within the application.
- `CATALOG_ADMIN_TOKEN`: The token required for performing administrative actions in the catalog service.

## Kubernetes configs

- `KUBECONFIG`: Specifies the path to the kubeconfig file. This environment variable is required
  when `USE_INCLUSTER_CONFIG` is set to "false", else it will read from the default location.
- `NAMESPACE`: Specifies the namespace for the application where it operates.
- `USE_INCLUSTER_CONFIG`: A boolean flag indicating whether the application should use in-cluster configuration. Set it
  to "true" to use in-cluster configuration or "false" to use an external configuration file.

**NOTE THAT** setting the `KUBECONFIG` environment variable will have no effect when `USE_INCLUSTER_CONFIG` is set to "
true". The application will automatically use the in-cluster configuration provided by the underlying infrastructure. If
you want to use an external configuration file, ensure that `USE_INCLUSTER_CONFIG` is set to "false" and provide the
path to the configuration file using the `KUBECONFIG` environment variable.

**NOTE THAT**  setting `NAMESPACE` also creates a toleration V1Toleration(effect="NoSchedule", key=namespace, operator="Exists")

## *Optional Environment Variables*

## Telemetry and Miscellaneous configs

- `SENTRY_DSN`: The DSN for the sentry instance to use for error reporting
- `METRICS_USERNAME` : The username for the /metrics endpoint which can be used by prometheus
- `METRICS_PASSWORD` : The password for the /metrics endpoint which can be used by prometheus
  **NOTE THAT** the `/metrics` endpoint will not be available unless both the username and password are set.
- `DOTENV_FILE_LOCATION`: The location of the .env file to use for local development. Defaults to .env
- `LOG_LEVEL`: The log level to use for the application. Defaults to INFO

# Code Review Request

* Organization and error handling for authorization, files in random places from ripping out FASTAPI parts.
* Organization and directory structure of APP
* Organization and directory structure of TESTS
* Organization and directory structure of TESTS (unit tests)
* Organization and directory structure of TESTS (integration tests)
* Organization and directory structure of FASTAPI (routes)
* RPC Calls backwards compataiblity design
* Not Using Classes design
* Dependency system design (passing around request.app.state)
* Caching
* Async/await
*

# Local Development

This repo uses a pipenv to manage dependencies.
To install pipenv, run `pip install pipenv`
To install dependencies, run

```
pipenv --python 3.11-service_wizard2
pipenv install --dev
pipenv shell
```

To start the server, run

```
uvicorn --host 0.0.0.0 --factory src.factory:create_app --reload --port 1234
```

To install pre-commit hook and test it

```
pre-commit install
pre-commit run --all-files
```

Convenience scripts are provided in the [scripts](scripts) directory to setup the pipenv environment and install
dependencies.

In order to connect to a kubernetes cluster, you will need to have a kubeconfig file in your home directory.
The kubeconfig file is typically located at `~/.kube/config`.
Read more about kubeconfig
files [here](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/).
Ensure that your context is set to the correct cluster and namespace and matches the environmental variables in
the [env](test/.env) file.

# PYCHARM

You can run the service in pycharm as well, but you will need to set the following parameters in the run configuration:

parameters = `<uvicorn_path_goes_here> --reload --port 5002 --host 0.0.0.0 --factory src.factory:create_app `

## Usage

OpenAPI documentation is provided at the `/docs` endpoint of the server (in KBase, this is
at `<host>/service/service_wizard2/docs`, for example
[https://ci.kbase.us/services/service_wizard2/docs](https://ci.kbase.us/services/service_wizard2/docs)).

However, the RPC endpoints are not documented. See the [original service wizard spec](src/ServiceWizard_Artifacts/ServiceWizard.spec) for details on how to use the endpoint.


### Error codes

Errors are return as JSONRPC errors.

## Administration

* Ensure the approproiate kubernetes roles/rolebindings/ are in place for the service account
  used by the service.
* Ensure that the namespace is created for both the Service Wizard and the Dynamic Services.
* Ensure that the environment is properly configured for the service.


## File structure

* `/src/clients` - KBase and Kubernetes clients with caches
* `/src/configs` - the configuration for the app
* `/src/dependencies` - shared service code
* `/src/models` - models for the app returns, logic for calculating service status, other models
* `/src/routes` - the routes for the app
* `/src/rpc` - the RPC endpoints for the app and common code
* `/test/src` - test code. Subdirectories should mirror the folder structure above, e.g.
* `/test/ServiceWizard_Artifacts` - the original Service Wizard related code

## Development
* Update the release notes in the [RELEASE_NOTES.md](RELEASE_NOTES.md) file.
* You can run the app via `docker-compose.yaml`
* You can update your credentials in your `kubeconfig` to deploy and launch the app in Rancher2 Desktop


### Running tests

Python 3.11 must be installed on the system.

```
pipenv sync --dev  # only the first time or when Pipfile.lock changes
pipenv shell
PYTHONPATH=. pytest test
```
