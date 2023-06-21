import sys
import requests
import pynetbox
from pprint import pprint
from libs import variables
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def acquire_ipam_data(tenant_name:str) ->list:
    """Returns a list of networks associated to the tenant, if the tenant is know in the DB
        If tenant is not in Netbox it will return an empty string
    Args:
        tenant_name (str): tenant name that has to match with Netbox Tenant

    Returns:
        list: A list containing CIDR formatted prefixes
    """
    
    my_ipam = pynetbox.api('http://10.50.128.210', variables.ipam_token)
    # List of tenants that we will pull from the IPAM, it matching ACI tenants
    ipam_data = list()
    try:
        for prefix in list(my_ipam.ipam.prefixes.filter(tenant=tenant_name)):
            if prefix.custom_fields["gateway"]:
                ipam_data.append(prefix.custom_fields["gateway"])
    except pynetbox.core.query.RequestError:
        pass
    return ipam_data

def main():
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
    else:
        print(session.cookies)

    response = session.get(f"https://{apic_address}/api/class/fvTenant.json", verify=False)

    tn_result = (response.json())

    for fvTenant in tn_result["imdata"]:
        this_tenant_name = fvTenant["fvTenant"]["attributes"]["name"]
        ipam_subnets = acquire_ipam_data(this_tenant_name)
        if not ipam_subnets:
            print(f'\n\nTenant: {this_tenant_name} not in Netbox, skipping it')
            continue
        print(f'\n\nTenant: {this_tenant_name}')
        response = session.get(
            f'https://{apic_address}/api/mo/uni/tn-{this_tenant_name}.json?query-target=subtree&target-subtree-class=fvSubnet', verify=False)
        
        subnets_result = (response.json())
        aci_subnets = list()
        for fvSubnet in subnets_result["imdata"]:
            aci_subnets.append(f'{fvSubnet["fvSubnet"]["attributes"]["ip"]}')
            
        if set(aci_subnets) - set(ipam_subnets):
            print(f"The following subnets are not defined in IPAM: {set(aci_subnets) - set(ipam_subnets)}")
        else:
            print("All subnets are synchronized")


if __name__ == "__main__":
    # Catch CTRL-C
    try:
        main()

    except KeyboardInterrupt as e:
        print("\nCTRL-C caught, interrupting Demo\n")
        sys.exit(1)