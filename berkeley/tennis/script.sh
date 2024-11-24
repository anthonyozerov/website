rm -rf scraper.log
killall firefox
killall geckodriver
TZ=America/Los_Angeles timeout 1200 /home/aozerov/.miniconda3/condabin/conda run -n scrape python scrape-tennis.py tennis-courts.yaml
killall firefox
killall geckodriver
