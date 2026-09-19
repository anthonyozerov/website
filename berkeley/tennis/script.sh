#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec timeout 120 /home/aozerov/.miniconda3/condabin/conda run -n scrape python scrape-tennis.py tennis-courts.yaml > scraper.log 2>&1
