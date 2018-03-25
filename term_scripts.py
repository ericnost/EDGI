#requirements
import csv
import nltk
from nltk.collocations import *
from web_monitoring.differs import _get_visible_text as gvt # import Dan Allan's page content decoder
import numpy

#count functions
def count(term, content): # this function counts single word terms from the decoded HTML
    visible_text = gvt(content)
    term = term.lower()  # normalize so as to make result case insensitive
    tally = 0
    for section in visible_text:
    	##bigram here. instead of section.split, bigram the section
        for token in section.split():
            tally += int(term in token.lower())
    return tally

def multiterm_count (content): #this function counts phrases
	visible_text = gvt(content)
	tally = 0
	for section in visible_text:
		tokens = nltk.word_tokenize(section)
		tokens = [x.lower() for x in tokens] #standardize to lowercase
		bgs = nltk.bigrams(tokens)
		fdist = nltk.FreqDist(bgs)
		tally += fdist['climate', 'change']
	return tally


# The below block of code is for looping through State Local Climate URLs to grab the term(s)
sum=0 # total count of term
page_count=0 # count of pages that had available snapshots
page_sum=0 # sum of term for a specific page
term = 'climate' # the term to count

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
                        page_sum = multiterm_count(contents) #count(term, contents) #count the term on the page.
                        sum += page_sum # add the page's sum to the overall sum
                        page_count += 1 # count the page
                        #print(row[0], page_sum)
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
                #statuses.append(version.status_code)
                #print(statuses)
                if version.status_code != '200':
                    pass
                else:
                    try:
                        url=version.raw_url
                        contents = requests.get(url).content.decode()
                        page_sum = multiterm_count(contents) #count(term, contents) #count the term on the page.
                        sum += page_sum # add the page's sum to the overall sum
                        page_count += 1 # count the page
                        print(row[0], page_sum)
                        break
                    except:
                        print('decoding error', version.status_code, row[0])# this will capture decoding errors
                        break
        except:
            print('IA error', row[0])# this will capture errors where IA has no records.
csvfile.close()


# The below block of code is for looping through all EPA URLs to grab the term(s)
file = 'epaURLs.csv' # the first file to open
with open(file) as csvfile: 
    read = csv.reader(csvfile)
    data = list(read)
csvfile.close()

row_count = len(data)
matrix = numpy.zeros((row_count, 3)) #we will store our data in a matrix with positions for the url, obama count, trump count

sum=0 # total count of term
page_count=0 # count of pages that had available snapshots
page_sum=0 # sum of term for a specific page
term = 'climate' # the term to count

for pos, row in enumerate(data):
    try:
        dump = list_versions(row[0], datetime(2017, 9, 1), datetime(2018, 3, 1)) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
        versions = reversed(list(dump)) # start from the most recent snapshots
        for version in versions: # for each version in all the snapshots 
            if version.status_code != '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                pass
            else: #if the IA snapshot captures a page live, try to decode it
                try:
                    url=version.raw_url
                    contents = requests.get(url).content.decode() #decode the url's HTML
                    page_sum = count(term, contents) #multiterm_count(contents) #count(term, contents) #count the term on the page.
                    sum += page_sum # add the page's sum to the overall sum
                    page_count += 1 # count the page
                    matrix[pos][2]=page_sum #matrix[pos][1] = Obama count, matrix[pos][2] = Trump count
                    print (page_count)
                    break
                except:
                    matrix[pos][2]=999 #code for capturing errors in decoding a page
                    break
    except:
        matrix[pos][2]=998 # code to capture errors where IA has no snapshots or only redirect/404 snapshots

#for writing term count to a csv. you will need to convert delimited text to columns and replace the first column with the list of URLs
with open('epa_output.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for row in matrix:
        writer.writerow(row)
csvfile.close()
