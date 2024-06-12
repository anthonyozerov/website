#!/bin/bash

cd ~/projects/morning-report
. bin/activate
echo -ne "\x1B\x67" #switch to 15cpi
python3 log-report.py > log-report
python3 weather-report.py > weather-report
paste log-report weather-report | column -s $'\t' -tn
python3 news-report.py > news-report
cat news-report
