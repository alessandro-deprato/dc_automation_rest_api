import requests
from pprint import pprint
from libs import variables
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()

ndfc_address = "10.50.129.123"

payload = ({
    "userName": "admin",
    "userPasswd": variables.ndfc_credentials["password"],
    "domain": "DefaultAuth"
    })

response = session.post(f"https://{ndfc_address}/login", json=payload, verify=False)

if not (199 < response.status_code < 300):
    print(f"Error Authenticating - {response.text}")
else:
    print(session.cookies)

response = session.get(f"https://{ndfc_address}/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics", verify=False)
fabric_result = response.json()

for fabric in fabric_result:
    fabric_name = fabric["fabricName"]
    print(f"Fabric: {fabric_name}")
    response = session.get(f"https://{ndfc_address}/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric_name}/inventory/switchesByFabric", verify=False)
    nodes = response.json()
    for node in nodes:
        print(f'Hostname: {node["hostName"]} -- Serial: {node["serialNumber"]} -- ManagementIP: {node["ipAddress"]}')

