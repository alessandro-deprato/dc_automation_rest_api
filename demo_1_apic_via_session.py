import sys
import requests
from pprint import pprint
from libs import variables
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()

apic_address = "10.50.129.241"
payload = {"aaaUser": {"attributes": 
    {"name": "admin",
     "pwd": variables.apic_credentials["password"]
    }
  }
}
response = session.post(f"https://{apic_address}/api/aaaLogin.json", json=payload, verify=False)

if not (199 < response.status_code < 300):
    print(f"Error Authenticating - {response.text}")
    sys.exit(1)
else:
    print(session.cookies)


response = session.get(f"https://{apic_address}/api/class/fvTenant.json", verify=False)
tn_result = (response.json())

print(f"\n\nTotal Tenants: {tn_result['totalCount']}")

for fvTenant in tn_result["imdata"]:
    this_tenant_name = fvTenant["fvTenant"]["attributes"]["name"]
    print(f'\n\nTenant: {this_tenant_name}')
    response = session.get(f'https://{apic_address}/api/class/fvTenant.json?query-target-filter=eq\
                            (fvTenant.name,"{this_tenant_name}")&rsp-subtree=children&rsp-subtree-class=fvBD&', verify=False)
    
    bd_result = (response.json())
    for fvBD in bd_result["imdata"][0]["fvTenant"]["children"]:
        print(f'{fvBD["fvBD"]["attributes"]["name"]}')