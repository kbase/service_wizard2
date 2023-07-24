import os

from dotenv import load_dotenv

from CatalogClient import Catalog

load_dotenv()
# cc = Catalog(url="https://ci.kbase.us/services/catalog", token=os.environ.get("CATALOG_ADMIN_TOKEN"))
# # print(cc.get_secure_config_params({"module_name": "NarrativeService", "version": "beta"}))
# print(cc.list_volume_mounts(filter={"module_name": "StaticNarrative", "version": "beta"}))

from ServiceWizardClient import ServiceWizard
# sw = ServiceWizard(url="https://ci.kbase.us/services/service_wizard", token=os.environ.get("CATALOG_ADMIN_TOKEN"))
# a = sw.start({"module_name" : "NarrativeService", "version": "0.3.13"})

sw2 = ServiceWizard(url="http://localhost:5002/rpc/", token=os.environ.get("CATALOG_ADMIN_TOKEN"))
b = sw2.start({"module_name" : "NarrativeService", "version": "beta"})

# print(a)
print(b)
