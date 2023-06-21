import re
import sys
import datetime
from pprint import pprint
from libs import ndfc,variables,nxapi
from influxdb import InfluxDBClient
client = InfluxDBClient(host='localhost', port=8086, username="admin", password=variables.influx_password)

client.switch_database('aci_db_stable')
ndfc_conn = ndfc.Ndfc("10.50.129.123",api_key=variables.ndfc_api_key)
vxlan_nodes = {node["hostName"]:node for node in ndfc_conn.get_all_nodes_by_fabric("AMS-CML-VXLAN")}


push_data = []

current_time = datetime.datetime.utcnow()
for node_name,node_data in vxlan_nodes.items():
    for port in ndfc_conn.get_all_interfaces_by_node(node_serial=node_data["serialNumber"]):
        if not "Eth" in port["ifName"]:
            continue
        push_data.append({"measurement":"total_ports",
                      "tags":{
                          "pod":"1",
                          "node":node_data["hostName"],
                          "port":port["ifName"],
                          "fabric": "NDFC-AMS"
                        },
                        "time":current_time,
                        "fields": {
                            "status":port["adminStatusStr"]
                        }
                      })
print(f"{(client.write_points(push_data))} -- {len(push_data)}")       
#print(client.write_points(push_data))
