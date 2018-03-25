# EDGI

A set of Python add-ons to the Environmental Data and Governance Intitiative's web monitoring project - specifically, their API into the CDX archive of Wayback Machine snapshots. There are to main sets of tools here. One, term_scrpts.py, captures the count of terms like "climate" across a set of archived pages. 

There are a few requirements to get started. Create an environment with Python 3.6 You may need to install several requirements: requests, numpy, and BeautifulSoup. Finally, you will want to install this component from the dev team:

https://github.com/edgi-govdata-archiving/web-monitoring-processing (be sure to follow their instructions about installation)

pip install https://github.com/edgi-govdata-archiving/web-monitoring-processing/zipball/master

This will enable you to perform the word count and link retrieval functions, by building the CDX Internet Archive API. The key file is internetarchive.py, which is the API the team developed to access the CDX archive of Internet Archive snapshots.

In this repo, there are several spreadsheets representing lists of URLs to check - one is for State Local Climate ("urls.csv" and "urls_shortened.csv") and one is for State Local Energy ("energyurls.csv"). Anastasia Aizman crawled these URLs. Another ("epaURLs.csv"), represents all EPA URLs EDGI has monitored in the Verisonista software.

To run the blocks in term_scripts.py or link_scripts.py you will need to run internetarchive.py and then either figure out a way to run within that shell or just copy/paste line by line into the shell. :( I am not a programmer!

Contribute to the analysis here! https://docs.google.com/document/d/18xX5nz2HIkjZPssOT0XcSC_zPDRiShovgUz6wwEfugg/edit
