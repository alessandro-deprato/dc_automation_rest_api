import re
import sys
import datetime
from pprint import pprint
from libs import apic,variables
from influxdb import InfluxDBClient

apic_conn = apic.Apic(variables.apic_host)
apic_conn.get_apic_token(variables.apic_credentials)
current_time = datetime.datetime.utcnow()
ports = apic_conn.get_aci_object("/class/ethpmPhysIf.json")


client = InfluxDBClient(host='localhost', port=8086, username="admin", password=variables.influx_password)
client.create_database('aci_db_demo_4')
client.switch_database('aci_db_demo_4')
push_data = []

for port in ports["imdata"]:
    #print(port["ethpmPhysIf"]["attributes"]["dn"])
    push_data.append({"measurement":"total_ports",
                      "tags":{
                          "pod":re.findall(r"/pod-(\d+)/",port["ethpmPhysIf"]["attributes"]["dn"])[0],
                          "node":re.findall(r"/node-(\d+)/",port["ethpmPhysIf"]["attributes"]["dn"])[0],
                          "port":re.findall(r"eth(\d+/\d+)]/",port["ethpmPhysIf"]["attributes"]["dn"])[0],
                          "fabric": "ACI-AMS"
                        },
                        "time":current_time,
                        "fields": {
                            "status":port["ethpmPhysIf"]["attributes"]["operSt"]
                        }
                      })
print(f"{(client.write_points(push_data))} -- {len(push_data)}")

