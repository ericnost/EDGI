# EDGI

There are a few requirements to get started. Create an environment with Python 3.6 Also, install "requests" (a Python package). Finally, you will want to install this component from the dev team:

https://github.com/edgi-govdata-archiving/web-monitoring-processing (be sure to follow their instructions about installation)

pip install https://github.com/edgi-govdata-archiving/web-monitoring-processing/zipball/master

This will enable you to perform the word count and link retrieval functions, by building the CDX Internet Archive API. The key file is internetarchive.py, which is the API the team developed to access the CDX archive of Internet Archive snapshots.

In this repo, there are two spreadsheets representing the list of URLs to check - one from State Local Climate ("urls.csv") and one for State Local Energy ("energyurls.csv"). Anastasia Aizman crawled these URLs.

To run the blocks in scripts.py you will need to run internetarchive.py and then either figure out a way to run scripts.py within that shell or just copy/paste line by line into the shell. :( I am not a programmer!

Contribute to the analysis here! https://docs.google.com/document/d/18xX5nz2HIkjZPssOT0XcSC_zPDRiShovgUz6wwEfugg/edit
