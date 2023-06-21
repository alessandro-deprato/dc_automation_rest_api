import sys
import requests
from pprint import pprint
from libs import variables
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()

ndfc_address = "10.50.129.123/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/"

payload = ({
    "userName": "admin",
    "userPasswd": variables.ndfc_credentials["password"],
    "domain": "DefaultAuth"
    })

response = session.post(f"https://10.50.129.123/login", json=payload, verify=False)

if not (199 < response.status_code < 300):
    print(f"Error Authenticating - {response.text}")
    sys.exit(1)
else:
    print(session.cookies)

response = session.get(f"https://{ndfc_address}/top-down/fabrics/AMS-CML-VXLAN/vrfs", verify=False)

vrf_result = response.json()
for vrf in vrf_result:
    vrf_name = vrf["vrfName"]
    print(f'\n\nVRF: {vrf_name}')
    response = session.get(f"https://{ndfc_address}/top-down/v2/fabrics/AMS-CML-VXLAN/networks?vrf-name={vrf_name}", verify=False)
    networks = response.json()
    for network in networks:
        print(f'Name: {network["displayName"]} -- DAG: {network["displayName"]}')