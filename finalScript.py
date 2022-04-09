#!/usr/bin/python3

import os
import sys

"""
Offline analysis by replaying logs
"""

# Import MobileInsight modules
from mobile_insight.monitor import OfflineReplayer
from mobile_insight.analyzer import MsgLogger, LteRrcAnalyzer, WcdmaRrcAnalyzer, LteNasAnalyzer, UmtsNasAnalyzer, LteMacAnalyzer, LteMeasurementAnalyzer

# Initialize a monitor
src = OfflineReplayer()
src.set_input_path("./logs/")
# src.enable_log_all()

src.enable_log("LTE_PHY_Serv_Cell_Measurement")
src.enable_log("5G_NR_RRC_OTA_Packet")
src.enable_log("LTE_RRC_OTA_Packet")
src.enable_log("LTE_NB1_ML1_GM_DCI_Info")

logger = MsgLogger()
logger.set_decode_format(MsgLogger.JSON)
logger.set_dump_type(MsgLogger.FILE_ONLY)
logger.save_decoded_msg_as("./mobileinsight.log")
logger.set_source(src)

# # Analyzers
# nr_rrc_analyzer = NrRrcAnalyzer()
# nr_rrc_analyzer.set_source(src)  # bind with the monitor

lte_rrc_analyzer = LteRrcAnalyzer()
lte_rrc_analyzer.set_source(src)  # bind with the monitor

# wcdma_rrc_analyzer = WcdmaRrcAnalyzer()
# wcdma_rrc_analyzer.set_source(src)  # bind with the monitor

# lte_nas_analyzer = LteNasAnalyzer()
# lte_nas_analyzer.set_source(src)

# umts_nas_analyzer = UmtsNasAnalyzer()
# umts_nas_analyzer.set_source(src)

# lte_mac_analyzer = LteMacAnalyzer()
# lte_mac_analyzer.set_source(src)

# lte_meas_analyzer = LteMeasurementAnalyzer()
# lte_meas_analyzer.set_source(src)

# print lte_meas_analyzer.get_rsrp_list()
# print lte_meas_analyzer.get_rsrq_list()

# Start the monitoring
src.run()

#The code above uses the mobile insight packages to decode the logs into a readable JSON-like format


#These system calls correct the formatting within the log so the python JSON decoder is able to interpret it correctly

os.system("echo \"{\" > log.json")
os.system("echo '\"log\": [' >> log.json")
os.system("sed -i 's/$/,/g' mobileinsight.log")  # add commas to the end of each line
os.system("sed -i '$ s/.$//' mobileinsight.log")  # remove the last comma
os.system("cat mobileinsight.log >> log.json")
os.system("echo \"]\" >> log.json")
os.system("echo \"}\" >> log.json")

import json
from datetime import datetime
from datetime import timedelta

with open("log.json", "r") as f:
    data = json.load(f)

log = data["log"]

def message_type_parsing(log):
    message_types = []
    for (i, entry) in enumerate(log): #iterate over each log entry
        type_id = entry['type_id']
        if type_id != 'LTE_RRC_OTA_Packet':
            message_types.append((i, type_id)) #only interested in parsing the LTE_RRC_OTA_Packets so skip the others
            continue
        cell_id = entry['Physical Cell ID']
        msg = entry['Msg']['msg']['packet']['proto'][5]['field']['field']
        if msg[1]['field'].__class__ != list: # paging messages
            message_types.append((i, type_id, cell_id, "paging"))
            continue
        msg_type = msg[1]['field'][1]['@showname']
        if msg_type == "c1: systemInformation (0)": #Handles SIB Info packets
            sib_types = msg[1]['field'][1]['field']['field'][1]['field']['field'][2]['field']
            if sib_types.__class__ != list:
                sib_types = [sib_type]
            sibs = []
            for sib_type in sib_types:
                sibs.append(sib_type['field'][2]['@showname'])
            message_types.append((i, type_id, cell_id, msg_type, sibs))
        else:
            message_types.append((i, type_id, cell_id, msg_type))
    return message_types



for line in message_type_parsing(log):
    print(line, file=open("message_types.txt", 'a'))

#The message_type_parsing function gives a high level overview of the type of information for each and every log entry
#This information is then stored in message_types.txt

rrcpackts = [entry for entry in log if entry["type_id"] == "LTE_RRC_OTA_Packet"]

releaseNsetup = []
for i, entry in enumerate(log):
    type_id = entry['type_id']
    if type_id != 'LTE_RRC_OTA_Packet':
        continue
    msg = entry["Msg"]["msg"]["packet"]["proto"][5]["field"]["field"]
    if msg[1]["field"].__class__ != list:  # paging messages
        continue
    msg_type = msg[1]["field"][1]["@showname"]
    if ( #want to extract only the connectionRelease and connectionSetupComplete log entries
        msg_type == "c1: rrcConnectionRelease (5)"
        or msg_type == "c1: rrcConnectionSetupComplete (4)"
    ):
        temp = dict(
            (k, entry[k]) for k in ["timestamp", "Physical Cell ID"] if k in entry
        )
        temp["msg_type"] = msg_type
        temp["index"] = i
        releaseNsetup.append(temp) 

#releaseNsetup is a list of all the connection setup and releases and their associated timestamps

sum = 0

for i in range(len(releaseNsetup) - 1):
    entry1 = releaseNsetup[i]
    entry2 = releaseNsetup[i + 1]

    ts1 = entry1["timestamp"]
    ts2 = entry2["timestamp"]

    d1 = datetime.strptime(ts1, "%Y-%m-%d %H:%M:%S.%f")
    d2 = datetime.strptime(ts2, "%Y-%m-%d %H:%M:%S.%f")

    difference = timedelta.total_seconds(d2 - d1)

    if i > 0:
        sum += difference


for line in releaseNsetup:
    print(line, file=open("setupAndReleases.txt", 'a'))

average = sum / (len(releaseNsetup) - 2)
s = f'The average time difference between the two events is {average} seconds'

print(s, file=open("setupAndReleases.txt", 'a'))

#The contents of releaseNsetup as well as the average difference in timestamp is stored in setupAndReleases.txt