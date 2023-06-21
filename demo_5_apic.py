import re
import sys
import datetime
from pprint import pprint
from libs import apic,variables,nxapi
from influxdb import InfluxDBClient
client = InfluxDBClient(host='localhost', port=8086, username="admin", password=variable.influx_password)
#client.drop_database('aci_db_stable')
#client.create_database('aci_db_stable')
#sys.exit(1)
client.switch_database('aci_db_stable')
apic_conn = apic.Apic(variables.apic_host)
apic_conn.get_apic_token(variables.apic_credentials)

ports = apic_conn.get_aci_object("/class/ethpmPhysIf.json")
health = apic_conn.get_aci_object("/mo/topology/health.json")
vlans = apic_conn.get_aci_object("/class/vlanCktEp.json",query_target_filter='wcard(vlanCktEp.epgDn,"epg"')
faults = apic_conn.get_aci_object('/class/faultInfo.json?query-target-filter=ne(faultInfo.severity,"cleared")')
current_time = datetime.datetime.utcnow()
push_data = [{"measurement":"health",
                      "tags":{
                          "fabric": "ACI-AMS"
                        },
                        "time":current_time,
                        "fields": {
                            "health":int(health["imdata"][0]["fabricHealthTotal"]["attributes"]["cur"])
                        }
                      }]
for fault in faults["imdata"]:
    push_data.append({"measurement":"faults",
                      "tags":{
                          "ack":fault["faultInst"]["attributes"]["ack"],
                          "dn":fault["faultInst"]["attributes"]["dn"],
                          "severity":fault["faultInst"]["attributes"]["severity"],
                          "domain":fault["faultInst"]["attributes"]["domain"],
                          "fabric": "ACI-AMS"
                        },
                        "time":current_time,
                        "fields": {
                            "type":fault["faultInst"]["attributes"]["type"],
                            
                            "code":fault["faultInst"]["attributes"]["code"],
                            "lifecycle":fault["faultInst"]["attributes"]["lc"]
                        }
                      })
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
for vlan in vlans["imdata"]:
    push_data.append({"measurement":"aci_vlans",
                      "tags":{
                          "pod":re.findall(r"/pod-(\d+)/",vlan["vlanCktEp"]["attributes"]["dn"])[0],
                          "node":re.findall(r"/node-(\d+)/",vlan["vlanCktEp"]["attributes"]["dn"])[0],
                          "tenant":re.findall(r"tn-([a-zA-Z0-9_.:-]+)/",vlan["vlanCktEp"]["attributes"]["epgDn"])[0],
                          "ap":re.findall(r"ap-([a-zA-Z0-9_.:-]+)/",vlan["vlanCktEp"]["attributes"]["epgDn"])[0],
                          "epg":re.findall(r"epg-([a-zA-Z0-9_.:-]+)",vlan["vlanCktEp"]["attributes"]["epgDn"])[0],
                          "fabric": "ACI-AMS"
                        },
                        "time":current_time,
                        "fields": {
                            "vlan":re.findall(r"vlan-(\d+)",vlan["vlanCktEp"]["attributes"]["dn"])[0],
                        }
                      })
print(f"{(client.write_points(push_data))} -- {len(push_data)}")
#print(client.write_points(push_data))