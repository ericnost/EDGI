#requirements for both term and link analyses
import requests
import csv


###TERM COUNT SCRIPTS
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

###LINK ANALYSIS
#specific reqs for this
import numpy
from bs4 import BeautifulSoup

page_count=0 # count of pages that had available snapshots

# build outgoing link matrix
file = 'urls test.csv' #this is a special set of urls (without http://www.epa.gov in order to compare with how the urls are coded on EPA's website)
with open(file) as csvfile: 
    read = csv.reader(csvfile)
    data = list(read) #put the csv data in an array
    row_count = len(data)
    matrix = numpy.zeros((row_count, row_count)) #create matrix
    urls = []
    for row in data:
        urls.append(row[0]) #compile list of all urls to check against later
csvfile.close()


#loop through data, call CDX API, populate matrix
for pos, row in enumerate(data):
    thisPage = 'http://www.epa.gov'+row[0]
    try:
        dump = list_versions(thisPage, datetime(2016, 11, 1), datetime(2017, 1, 19)) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
        versions = reversed(list(dump)) # start from the most recent snapshots
        for version in versions: # for each version in all the snapshots 
            if version.status_code != '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                pass
            else: #if the IA snapshot represents a page, try to decode it
                try:
                    wayback_url=version.raw_url
                    contents = requests.get(wayback_url).content.decode() #decode the url's HTML
                    page_count += 1 # count the page so we know how many pages we actually looked at
                    soup = BeautifulSoup(contents, 'lxml') 
                    links = soup.find_all('a') #find all outgoing links
                    thisPageLinksTo = []
                    for link in links:
                        thisPageLinksTo.append(link['href']) #for each outgoing link, strip away the name etc. to just the href
                    #use keys/columns and check against links. is x key/column in links? does this page link to another? if so, add 1
                    for i, url in enumerate(urls):
                        if url in thisPageLinksTo: #if this page links to another subdomain url
                            #print(thisPage, url, wayback_url, pos, i) #print what this page is, what it links to, and IA url
                            matrix[pos][i] = 1  #put a 1 at the right position. matrix[row][column]
                    break
                except:
                    print('decoding error', version.status_code, row[0])# this will capture errors in decoding a page
                    break
    except:
        print('IA error', row[0]) # this will capture errors where IA has no records.

#quick output of matrix (you will need to transpose to columns with a space delimiter)
with open('output.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for row in matrix:
        writer.writerow(row)
csvfile.close()