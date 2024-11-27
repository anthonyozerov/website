rm -rf scraper.log
TZ=America/Los_Angeles timeout 120 /home/aozerov/.miniconda3/condabin/conda run -n scrape python scrape-tennis.py tennis-courts.yaml
