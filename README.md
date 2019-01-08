# EDGI

A set of Python and R scripts extending the Environmental Data and Governance Intitiative's web monitoring project - specifically, their [API](https://github.com/edgi-govdata-archiving/web-monitoring-processing) into the CDX archive of Wayback Machine snapshots. 

## `CTRL-F.py`

`counter()` counts the number of times a set of one or two word terms (e.g. "climate", "climate change", "energy independence", etc.) was used across pages during a single timeframe (e.g. between June and August 2018). The output is a matrix of URLs, terms, and counts in CSV format. Run `counter()` twice on the same URLs in order to make a comparison between two timeframes (e.g. June-August 2018 and June-August 2016). This comparison is facilitated by the R script `termcount.R`, which ingests two CSV outputs of `counter()` representing two timeframes and returns an analysis of their differences.

`linker()` builds a matrix describing how a set of pages links to each other. 

## Requirements

There are a few requirements to get started with term and link *scraping*. Create an environment with Python 3.6 You may need to install several requirements: requests, numpy, nltk, and BeautifulSoup. You will want to install this component from [the dev team](https://github.com/edgi-govdata-archiving/web-monitoring-processing) (be sure to follow their instructions about installation):

`pip install https://github.com/edgi-govdata-archiving/web-monitoring-processing/zipball/master`

There are also a few requirements to get started with term *analysis*. You will need to install the R software environment on your computer. I recommend the [open source version](https://www.rstudio.com/products/rstudio/#Desktop) of R Studio, a graphical interface for implementing analysis in R. Furthermore, there are two packages you will want to install: `install.packages("readr")` for reading CSV files and `install.packages("openxlsx")` for writing multiple sheets of an XLSX file.

## Example usage

- `CTRL-F_BC.py` is a customized instance of `CTRL-F.py` for assessing breast cancer advocacy organizations' websites.
- `CTRL-F_Web-Monitoring.py` is a customized instance of CTRL-F for assessing US federal environmental agencies' websites.
- `termcount-webmonitoring.R` is a customized instance of `termcount.R` for assessing changes in the use of terms by US federal environmental agencies on their websites.

### counter()
`counter(file, terms, dates)`

See `inputs/test.csv` for an example set of pages to examine.

Variables:
- `file` should be a CSV containing a set of URLs in the form "http://www.epa.gov"
- `terms` should be in the format ["climate", ["climate", "change"], "energy", ["endangered", "species"]]. Currently only supports one or two word phrases.
- `dates` describes the timeframe for which you want to capture Wayback Machine snapshots. It should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]. `counter()` defaults to searching _backwards_ - it takes the most recently available (status code = 200 or "-") snapshot within the timeframe.

`counter("input/test.csv", ["climate", ["endangered", "species"]], [2016, 1,1,2017,1,1])` would report on the usage of these terms on a sample of US Fish and Wildlife Service pages during 2016.

### termcount.R

The output(s) of `counter()` are directly applicable to `termcount.R` Specifically, the former produces a matrix CSV (or two, if you run on different timeframes) that can be loaded into R. 

The purpose of this script is to compare changes in the use of a set of terms, on a given set of pages, over time. It focuses specifically on those pages where there was an available Wayback Machine snapshot in both timeframes AND there was no change but the term was used in both timeframes (e.g. 11 to 11) OR there was change (e.g. 0 to 1, 12 to 0, etc.) In other words, it ignores pages where only one snapshot in the two timeframes was available and pages with 0 counts for both timeframes.

The example CSV is for comparing term usage between the Obama era and a timeframe during the Trump administration.

Assumptions: the script assumes row position refers to the same URL in both CSVs.

### linker()

`linker (file, domain, datesA, datesB=[])`

See `inputs/test_links.csv` for an example set of pages to examine.

Variables:
- `file` should be a CSV containing a set of URLs in the form "/subdomain/page.html"
- `domain` should be a string of the domain that is being searched e.g. `"https://www.epa.gov"`
- `datesA` describes the timeframe for which you want to capture Wayback Machine snapshots. It should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]. `counter()` defaults to searching _backwards_ - it takes the most recently available (status code = 200) snapshot within the timeframe.
- `datesB` = For comparing with the `datesA` timeframe. Optional. Should be in same format as `datesA`

`linker ("inputs/fws.csv", "https://www.fws.gov", [2016,1,1,2017,1,1], [2017,1,2,2018,1,1])` would examine the linking structure of a sample of US Fish and Wildlife Service URLs as they exised in 2016 compared to 2017.

## Limits

- `linker()` is currently limited to examining only one set of URLs to one another (producing a square matrix). These should probably be in the same domain (e.g. epa.gov).
- There is currently pretty much no debugging, so you're on your own.
