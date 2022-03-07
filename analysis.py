#!/usr/bin/python3

import json
from datetime import datetime
from datetime import timedelta

with open("log.json", "r") as f:
    data = json.load(f)

log = data["log"]

def message_type_parsing(log):
    message_types = []
    for (i, entry) in enumerate(log):
        type_id = entry['type_id']
        if type_id != 'LTE_RRC_OTA_Packet':
            message_types.append((i, type_id))
            continue
        cell_id = entry['Physical Cell ID']
        msg = entry['Msg']['msg']['packet']['proto'][5]['field']['field']
        if msg[1]['field'].__class__ != list: # paging messages
            message_types.append((i, type_id, cell_id, "paging"))
            continue
        msg_type = msg[1]['field'][1]['@showname']
        #rrc_types.append(msg_type)
        if msg_type == "c1: systemInformation (0)":
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
    if (
        msg_type == "c1: rrcConnectionRelease (5)"
        or msg_type == "c1: rrcConnectionSetupComplete (4)"
    ):
        temp = dict(
            (k, entry[k]) for k in ["timestamp", "Physical Cell ID"] if k in entry
        )
        temp["msg_type"] = msg_type
        temp["index"] = i
        releaseNsetup.append(temp)

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





