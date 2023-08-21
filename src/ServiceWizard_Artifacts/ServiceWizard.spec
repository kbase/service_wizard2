

module ServiceWizard {

    typedef int boolean;

    /* Get the version of the deployed service wizard endpoint. */
    funcdef version() returns (string version);

    /*
        module_name - the name of the service module, case-insensitive
        version     - specify the service version, which can be either:
                        (1) full git commit hash of the module version
                        (2) semantic version or semantic version specification
                            Note: semantic version lookup will only work for
                            released versions of the module.
                        (3) release tag, which is one of: dev | beta | release

        This information is always fetched from the Catalog, so for more details
        on specifying the version, see the Catalog documentation for the
        get_module_version method.
    */
    typedef structure {
        string module_name;
        string version;
    } Service;

    /*
        module_name     - name of the service module
        version         - semantic version number of the service module
        git_commit_hash - git commit hash of the service module
        release_tags    - list of release tags currently for this service module (dev/beta/release)

        url             - the url of the service

        up              - 1 if the service is up, 0 otherwise
        status          - status of the service as reported by rancher
        health          - health of the service as reported by Rancher

        TODO:
          add something to return: string last_request_timestamp;
    */
    typedef structure {
        string module_name;
        string version;
        string git_commit_hash;

        list <string> release_tags;

        string hash;

        string url;

        boolean up;
        string status;
        string health;
    } ServiceStatus;


    /*
        Try to start the specified service; this will generate an error if the
        specified service cannot be started.  If the startup did not give any
        errors, then the status of the running service is provided.
    */
    funcdef start(Service service) returns (ServiceStatus status);

    /*
        Try to stop the specified service; this will generate an error if the
        specified service cannot be stopped.  If the stop did not give any
        errors, then the status of the stopped service is provided.
    */
    funcdef stop(Service service) returns (ServiceStatus status);

    /* not yet implemented
    funcdef pause(Service service) returns (ServiceStatus status);
    */


    typedef structure {
        boolean is_up;
        list <string> module_names;
    } ListServiceStatusParams;

    funcdef list_service_status(ListServiceStatusParams params) returns (list<ServiceStatus>);

    /*
        For a given service, check on the status.  If the service is down or
        not running, this function will attempt to start or restart the
        service once, then return the status.

        This function will throw an error if the specified service cannot be
        found or encountered errors on startup.
    */
    funcdef get_service_status(Service service) returns (ServiceStatus status);


    funcdef get_service_status_without_restart(Service service) returns (ServiceStatus status);


    typedef structure {
        string instance_id;
        list <string> log;
    } ServiceLog;

    /* optional instance_id to get logs for a specific instance.  Otherwise logs from all instances
    are returned, TODO: add line number constraints. */
    typedef structure {
        Service service;
        string instance_id;
    } GetServiceLogParams;

    funcdef get_service_log(GetServiceLogParams params) returns (list<ServiceLog> logs) authentication required;


    typedef structure{
        string instance_id;
        string socket_url;
    } ServiceLogWebSocket;

    /* returns connection info for a websocket connection to get realtime service logs */
    funcdef get_service_log_web_socket(GetServiceLogParams params) returns (list <ServiceLogWebSocket> sockets) authentication required;

};
