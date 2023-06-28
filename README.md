# Service Wizard 2

The service wizard manages the lifecycle of "dynamic services" in KBase. 
The previous service wizard talked directly to rancher1, this one talks directly to kubernetes.
Dynamic services are responsible for providing  data and/or UI components for the KBase UI and Narrative.

# Environment Variables

The following environment variables are used to configure the application:
See [.env](.env) file for example


- `NAMESPACE`: Specifies the namespace for the application where it operates.
- `AUTH_SERVICE_URL`: Defines the URL of the authentication service used for user authentication and authorization.
- `KBASE_ENDPOINT`: Specifies the endpoint URL for the KBase service, which provides various functionalities for the application.
- `CATALOG_URL`: Sets the URL for the catalog service, which manages and provides access to application catalogs.
- `CATALOG_ADMIN_TOKEN`: The token required for performing administrative actions in the catalog service.
- `USE_INCLUSTER_CONFIG`: A boolean flag indicating whether the application should use in-cluster configuration. Set it to "true" to use in-cluster configuration or "false" to use an external configuration file.
- `KUBECONFIG`: Specifies the path to the kubeconfig file. This environment variable is required when `USE_INCLUSTER_CONFIG` is set to "false", else it will read from the default location.
Note that setting the `KUBECONFIG` environment variable will have no effect when `USE_INCLUSTER_CONFIG` is set to "true". The application will automatically use the in-cluster configuration provided by the underlying infrastructure. If you want to use an external configuration file, ensure that `USE_INCLUSTER_CONFIG` is set to "false" and provide the path to the configuration file using the `KUBECONFIG` environment variable.
- The `KBASE_ADMIN_ROLE`, `CATALOG_ADMIN_ROLE`, and `SERVICE_WIZARD_ROLE` environment variables grant administrative rights within the application. Having at least one of these roles is required for performing administrative actions within service_wizard2.

Ensure that all the required environment variables are properly set before running the application.





# Code Review Request
* Organization and directory structure of APP
* Organization and directory structure of TESTS
* Organization and directory structure of TESTS (unit tests)
* Organization and directory structure of TESTS (integration tests)
* Organization and directory structure of FASTAPI (routes)
* RPC Calls backwards compataiblity design
* Rolling own incomplete RPC respoonses vs using existing libraries
* Not Using Classes design
* Dependency system design (passing around request.app.state)
* Caching


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

Convenience scripts are provided in the [scripts](scripts) directory to setup the pipenv environment and install dependencies.

In order to connect to a kubernetes cluster, you will need to have a kubeconfig file in your home directory.
The kubeconfig file is typically located at `~/.kube/config`.
Read more about kubeconfig files [here](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/).
Ensure that your context is set to the correct cluster and namespace and matches the environmental variables in the [env](test/.env) file.


# PYCHARM 
You can run the service in pycharm as well, but you will need to set the following parameters in the run configuration:

script path =`/Users/XXX/.local/share/virtualenvs/service_wizard2-vG0FwGFD/bin/uvicorn`
parameters = `--reload --port 5002 --host 0.0.0.0 --factory src.factory:create_app `

## Usage

OpenAPI documentation is provided at the `/docs` endpoint of the server (in KBase, this is
at `<host>/service/service_wizard2/docs`, for example
[https://ci.kbase.us/services/service_wizard2/docs](https://ci.kbase.us/services/service_wizard2/docs)).

### Error codes

Error codes are listed in [errors.py](src/service/errors.py).

## Administration

To start the service Docker container:

* The collections listed in
  [collection_and_field_names.py](src/common/storage/collection_and_field_names.py) must be
  created in ArangoDB. The collections are not created automatically to allow service admins
  to specify sharding to their liking. Indexes are created automatically, assuming the collections
  exist.
* The environment variables listed in
  [collections_config.toml.jinja](collections_config.toml.jinja)
  must be provided to the Docker container, unless their default values are acceptable.
  In particular, database access and credential information must be provided.

## File structure

* `/src/service` - service code
* `/src/loaders/[collection ID]` - loader code for collections, e.g. `/loaders/gtdb`
* `/src/common` - shared loader and service code
* `/src/common/storage` - data connection and access methods
* `/test/src` - test code. Subdirectories should mirror the folder structure above, e.g.
  `/test/src/service` contains service test code

## Development

### Adding code

* In this alpha / prototype stage, we will be PRing (do not push directly) to `main`. In the
  future, once we want to deploy beyond CI, we will add a `develop` branch.
* The PR creator merges the PR and deletes branches (after builds / tests / linters complete).
* To add new data products, see [Adding data products](/docs/adding_data_products.md)

#### Timestamps

* Timestamps visible in the API must be fully qualified ISO8601 timestamps in the format
  `2023-01-29T21:41:48.867140+00:00`.
* Timestamps may be stored in the database as either the above format or as Unix epoch
  milliseconds, depending on the use case.
* If timestamps are stored as epoch ms, they must be converted to the ISO8601 format prior to
  returning them via the API.

### Versioning

* The code is versioned according to [Semantic Versioning](https://semver.org/).
* The version must be updated in
  * `/src/common/version.py`
  * `/RELEASE_NOTES.md`
  * any test files that test the version

### Code requirements for prototype code:

* Any code committed must at least have a test file that imports it and runs a noop test so that
  the code is shown with no coverage in the coverage statistics. This will make it clear what
  code needs tests when we move beyond the prototype stage.
* Each module should have its own test file. Eventually these will be expanded into unit tests
  (or integration tests in the case of app.py)
* Any code committed must have regular code and user documentation so that future devs
  converting the code to production can understand it.
* Release notes are not strictly necessary while deploying to CI, but a concrete version (e.g.
  no `-dev*` or `-prototype*` suffix) will be required outside of that environment. On a case by
  case basis, add release notes and bump the prototype version (e.g. 0.1.0-prototype3 ->
  0.1.0-prototype4) for changes that should be documented.

### Running tests

Python 3.11 must be installed on the system.

```
pipenv sync --dev  # only the first time or when Pipfile.lock changes
pipenv shell
PYTHONPATH=. pytest test
```

## TODO

* Logging ip properly (X-RealIP, X-Forwarded-For)
  * Add request ID to logs and return in errors
  * Compare log entries to SDK and see what we should keep
    * Take a look at the jgi-kbase IDmapper service

### Prior to declaring this a non-prototype

* Coverage badge in Readme
* Run through all code, refactor to production quality
* Add tests where missing (which is a lot) and inspect current tests for completeness and quality
  * E.g. don't assume existing tests are any good
  * Async testing help
    https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
* Build & push tool images in GHA
  * Consider using a base image for each tool with a "real" image that builds from the base image.
    The "real" image should just copy the files into the image and set the entry point. This will
    make GHA builds a lot faster
  * Alternatively use docker's GHA cache feature
  * Manual push only is probably fine, these images won't change that often
* JobRunner repo should be updated to push the callback server to a GHA KBase namespace
* Testing tool containers
  * DO NOT import the tool specific scripts and / or run them directly in tests, as that will
    require all their dependencies to be installed, creating dependency hell.
  * Instead
    * Test as a black box using `docker run`
      * This won't work for gtdb_tk, probably. Automated testing for that is going to be
        problematic.
    * If necessary, add a `Dockerfile.test` dockerfile to build a test specific image and run
      tests in there.
      * Either mount a directory in which to save the coverage info or `docker cp` it when the
        run is complete
      * Figure out how to merge the various coverage files.
