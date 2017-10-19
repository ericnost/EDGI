# EDGI

There are a few requirements to get started. Create an environment with Python 3.6 Also, install "requests" (a Python package). Finally, you will want to install this component developed by the team:

https://github.com/edgi-govdata-archiving/web-monitoring-processing (be sure to follow their instructions about installation)

pip install https://github.com/edgi-govdata-archiving/web-monitoring-processing/zipball/master

This will enable the word count function (seen here) and the IA API. The key file is internetarchive.py, which is the API the team developed to access the CDX archive of Internet Archive snapshots.

In my repo, there are two spreadsheets representing the list of URLs to check.

To run my term_counter.py script you will need to run internetarchive.py and then either figure out a way to run term_counter.py within that shell or just copy/paste line by line into the shell. :(
