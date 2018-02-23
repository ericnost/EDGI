import requests
import csv
from web_monitoring.differs import _get_visible_text as gvt # import Dan Allan's page content decoder
def count(term, content): # this function counts terms from the decoded HTML
    visible_text = gvt(content)
    term = term.lower()  # normalize so as to make result case insensitive
    tally = 0
    for section in visible_text:
        for token in section.split():
            tally += int(term in token.lower())
    return tally

sum=0 # total count of term
page_count=0 # count of pages that had available snapshots
page_sum=0 # sum of term for a specific page
term = 'climate' # the term to count

# The below block of code is for looping through State Local Climate URLs to grab the term
file = 'urls.csv' # the first file to open
with open(file) as csvfile: 
    read = csv.reader(csvfile)
    for row in read:
        try:
            dump = list_versions(row[0], datetime(2016, 11, 1), datetime(2017, 1, 19)) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
            versions = reversed(list(dump)) # start from the most recent snapshots
            for version in versions: # for each version in all the snapshots 
                if version.status_code != '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                    pass
                else: #if the IA snapshot represents a page, try to decode it
                    try:
                        url=version.raw_url
                        contents = requests.get(url).content.decode() #decode the url's HTML
                        page_sum = count(term, contents) # count the term 
                        sum += page_sum # add the page's sum to the overall sum
                        page_count += 1 # count the page
                        print(row[0], page_sum)
                        break
                    except:
                        print('decoding error', version.status_code, row[0])# this will capture errors in decoding a page
                        break
        except:
            print('IA error', row[0]) # this will capture errors where IA has no records.
csvfile.close()

# The below block of code is for looping through State Local Climate URLs to grab outgoing links
from bs4 import BeautifulSoup
with open(file) as csvfile: 
    read = csv.reader(csvfile)
    for row in read:
        try:
            dump = list_versions(row[0], datetime(2016, 11, 1), datetime(2017, 1, 19)) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
            versions = reversed(list(dump)) # start from the most recent snapshots
            for version in versions: # for each version in all the snapshots 
                if version.status_code != '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                    pass
                else: #if the IA snapshot represents a page, try to decode it
                    try:
                        url=version.raw_url
                        contents = requests.get(url).content.decode() #decode the url's HTML
                        soup = BeautifulSoup(contents, 'lxml')
                        links = soup.find_all('a')
                        print(row[0], links)
                        break
                    except:
                        print('decoding error', version.status_code, row[0])# this will capture errors in decoding a page
                        break
        except:
            print('IA error', row[0]) # this will capture errors where IA has no records.
csvfile.close()

# The below block of code is for looping through State Local Energy URLs to grab the term
with open('energyurls.csv') as csvfile:
    read = csv.reader(csvfile)
    for row in read:
        try:
            dump = list_versions(row[0])
            versions = reversed(list(dump))# start from the most recent snapshots
            statuses = [row[0]]
            for version in versions:
                statuses.append(version.status_code)
                print(statuses)
                if version.status_code != '200':
                    pass
                else:
                    try:
                        url=version.raw_url
                        contents = requests.get(url).content.decode()
                        sum += count(term, contents)
                        page_count += 1
                        break
                    except:
                        print('decoding error', version.status_code, row[0])# this will capture decoding errors
                        break
        except:
            print('IA error', row[0])# this will capture errors where IA has no records.