from libs import ndfc,variables
from pprint import pprint


ndfc_conn = ndfc.Ndfc("10.50.129.123",api_key=variables.ndfc_api_key)
fabric_result = ndfc_conn.get_all_fabrics()

for fabric in fabric_result:
    fabric_name = fabric["fabricName"]
    print(f"Fabric: {fabric_name}")
    nodes = ndfc_conn.get_all_nodes_by_fabric(fabric_name)
    for node in nodes:
        print(f'Hostname: {node["hostName"]} -- Serial: {node["serialNumber"]} -- ManagementIP: {node["ipAddress"]}')