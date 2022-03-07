#!/bin/bash

python3 mobileinsight_dump_to_json.py
#First we must fix the output format 

echo "{" > log.json
echo '"log": [' >> log.json
sed -i 's/$/,/g' mobileinsight.log #add commas to the end of each line
sed -i '$ s/.$//' mobileinsight.log #remove the last comma
cat mobileinsight.log >> log.json
echo "]" >> log.json
echo "}" >> log.json

python3 analysis.py