# def test_get_good_status(client_with_authorization):
#     # sw.start({"module_name": "StaticNarrative", "version": "beta"})
#
#     # rv = {
#     #     "git_commit_hash": "64df4dc3c09b225a9468a73e7129f1cf1631ae4e",
#     #     "status": "active",
#     #     "version": "0.0.15",
#     #     "hash": "64df4dc3c09b225a9468a73e7129f1cf1631ae4e",
#     #     "release_tags": ["beta", "dev"],
#     #     "url": "https://ci.kbase.us:443/dynserv/64df4dc3c09b225a9468a73e7129f1cf1631ae4e.StaticNarrative",
#     #     "module_name": "StaticNarrative",
#     #     "health": "healthy",
#     #     "up": 1,
#     # }
#
#     # sw.start({"module_name": "NarrativeService", "version": "release"})
#
#     # rv = {
#     #     "git_commit_hash": "8a9bb32f9e2ec5169815b984de8e8df550699630",
#     #     "status": "active",
#     #     "version": "0.5.2",
#     #     "hash": "8a9bb32f9e2ec5169815b984de8e8df550699630",
#     #     "release_tags": ["release", "beta", "dev"],
#     #     "url": "https://ci.kbase.us:443/dynserv/8a9bb32f9e2ec5169815b984de8e8df550699630.NarrativeService",
#     #     "module_name": "NarrativeService",
#     #     "health": "healthy",
#     #     "up": 1,
#     # }
#
#     with client_with_authorization() as client:
#         response = client.get("/get_service_status?module_name=NarrativeService&version=beta")
#         assert response.json() != []
#         assert response.json() == [123]
#         assert response.status_code == 200
