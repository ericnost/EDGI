#requirements
import csv
import numpy
from bs4 import BeautifulSoup

page_count=0 # count of pages that had available snapshots

# build outgoing link matrix
file = 'urls.csv' #this is a special set of urls (without http://www.epa.gov in order to compare with how the urls are coded on EPA's website)
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
    thisPage = row[0] #for urls_shortened.csv use: 'http://www.epa.gov'+row[0]
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