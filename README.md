#EDGI

A set of Python functions extending the Environmental Data and Governance Intitiative's web monitoring project - specifically, their API into the CDX archive of Wayback Machine snapshots. `counter()` counts the number of times a term or phrase occurs across a set of pages within a specified timeframe. `linker()` builds a matrix describing how a set of pages links to each other. 

##Requirements

There are a few requirements to get started. Create an environment with Python 3.6 You may need to install several requirements: requests, numpy, nltk, and BeautifulSoup. You will want to install this component from [the dev team](https://github.com/edgi-govdata-archiving/web-monitoring-processing) (be sure to follow their instructions about installation):

`pip install https://github.com/edgi-govdata-archiving/web-monitoring-processing/zipball/master`

##Example usage

###counter()

`counter(file, term, datesA, datesB=[])`

See `inputs/test.csv` for an example set of pages to examine.

Variables:
- `file` should be a CSV containing a set of URLs in the form "http://www.epa.gov"
- `term` should be in the format ["term"] or ["climate", "change"]. Currently only supports two word phrases.
- `datesA` describes the timeframe for which you want to capture Wayback Machine snapshots. It should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]. `counter()` defaults to searching _backwards_ - it takes the most recently available (status code = 200) snapshot within the timeframe.
- `datesB` = For comparing with the `datesA` timeframe. Optional. Should be in same format as `datesA`

###linker()

`linker (file, domain, datesA, datesB=[])`

See `inputs/test_links.csv` for an example set of pages to examine.

Variables:
- `file` should be a CSV containing a set of URLs in the form "/subdomain/page.html"
- `domain` should be a string of the domain that is being searched e.g. `"https://www.epa.gov"`
- `datesA` describes the timeframe for which you want to capture Wayback Machine snapshots. It should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]. `counter()` defaults to searching _backwards_ - it takes the most recently available (status code = 200) snapshot within the timeframe.
- `datesB` = For comparing with the `datesA` timeframe. Optional. Should be in same format as `datesA`

##Limits

- `linker()` is currently limited to examining only one set of URLs to one another (producing a square matrix). These should probably be in the same domain (e.g. epa.gov).
- There is currently pretty much no debugging, so you're on your own.