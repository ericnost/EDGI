#requirements
import csv
import nltk
from nltk.collocations import *
from web_monitoring.differs import _get_visible_text as gvt # import Dan Allan's page content decoder
import numpy
from bs4 import BeautifulSoup # for link analysis
import internetarchive
import requests

#ancillary count functions
def count(term, content): # this function counts single word terms from the decoded HTML
    visible_text = gvt(content)
    term = term.lower()  # normalize so as to make result case insensitive
    tally = 0
    for section in visible_text:
    	##bigram here. instead of section.split, bigram the section
        for token in section.split():
            tally += int(term in token.lower())
    return tally

def multiterm_count (term, content): #this function counts phrases from the decoded HTML
	visible_text = gvt(content)
	tally = 0
	length = len(term)
	for section in visible_text:
		tokens = nltk.word_tokenize(section)
		tokens = [x.lower() for x in tokens] #standardize to lowercase
		grams=nltk.ngrams(tokens,length)
		fdist = nltk.FreqDist(grams)
		tally += fdist[term[0], term[1]]
	return tally

def counter(file, term, datesA, datesB=[]):
    #datesA should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]
    #datesB = optional (for comparing two time periods). should be in same format as datesA
    #term should be in the format ["term"] or as a phrase: ["climate", "change"] currently only supporting two word phrases

    dates = {'first': datesA, 'second': datesB}
    
    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read)
    csvfile.close()

    # counter("test.csv", ["climate"], [2016, 1,1,2017,1,1], [2017,1,2,2018,1,1])
    
    row_count = len(data)
    column_count = 2
    if len(dates['second']) > 0:
        column_count=3
    matrix = numpy.zeros((row_count, column_count)) #we will store our data in a matrix with positions for the url, datesA count, datesB count
    
    col_pos=1 # the column of the matrix we start in (datesA count)
    while col_pos <= column_count-1:
        sum=0 # total count of term
        page_count=0 # count of pages that had available snapshots
        page_sum=0 # sum of term for a specific page
        if col_pos == 1:
            theseDates = dates['first']
        else:
            theseDates = dates['second']
        for pos, row in enumerate(data):
            try:
                dump = internetarchive.list_versions(row[0], internetarchive.datetime(theseDates[0], theseDates[1],theseDates[2]), internetarchive.datetime(theseDates[3], theseDates[4], theseDates[5])) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
                versions = reversed(list(dump)) # start from the most recent snapshots
                for version in versions: # for each version in all the snapshots 
                    if version.status_code != '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                        pass
                    else: #if the IA snapshot captures a page live, try to decode it
                        try:
                            url=version.raw_url
                            contents = requests.get(url).content.decode() #decode the url's HTML
                            if len(term) == 1:
                                page_sum = count(term[0], contents) #multiterm_count(contents) #count(term, contents) #count the term on the page.
                            else:
                                page_sum += multiterm_count(term, contents)
                            sum += page_sum # add the page's sum to the overall sum
                            page_count += 1 # count the page
                            matrix[pos][col_pos]=page_sum #put the count of the term in the matrix
                            break
                        except:
                            matrix[pos][col_pos]=999 #code for capturing errors in decoding a page - PDFs, GIFs, and other formats WM has archived but which we can't count terms on
                            break
            except:
                matrix[pos][col_pos]=998 # code to capture errors where WM has no snapshots or only redirect/404 snapshots
        col_pos = col_pos + 1

    #for writing term count to a csv. you will need to convert delimited text to columns and replace the first column with the list of URLs
    with open('output/output.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in matrix:
            writer.writerow(row)
    csvfile.close()
    print("The program is finished!")



def linker (file, domain, datesA, datesB=[]):
    #currently only accepts looking at how a set of URLs point to each other (a square matrix)
    #currently is meant to look at links in a single domain e.g. "http://www.epa.gov" File should be a csv of links like: "/cleanpowerplan/page"
    #datesA should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]
    #datesB = optional (for comparing two time periods). should be in same format as datesA

    page_count=0 # count of pages that had available snapshots

    dates = {'first': datesA, 'second': datesB}

    # build outgoing link matrix
    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read) #put the csv data in an array
        row_count = len(data)
        matrix = numpy.zeros((row_count, row_count)) #create matrix
        urls = []
        for row in data:
            urls.append(row[0]) #compile list of all urls to check against later
    csvfile.close()

    times = 1
    if len(dates['second'])>0:
        times = 2
    position = 1

    #loop through data, call CDX API, populate matrix
    while position <= times:
        if position == 1:
            theseDates = dates['first']
            connection = 1
            decoding_error = 8
            WM_error = 9
        else:
            theseDates = dates['second']
            connection = 3
            decoding_error = 14
            WM_error = 16
        for pos, row in enumerate(data):
            thisPage = domain+row[0] # row[0] #for urls_shortened.csv use: 'http://www.epa.gov'+row[0]
            try:
                dump = internetarchive.list_versions(thisPage, internetarchive.datetime(theseDates[0], theseDates[1],theseDates[2]), internetarchive.datetime(theseDates[3], theseDates[4], theseDates[5])) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
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
                            for i, url in enumerate(data):
                                if url in thisPageLinksTo: #if this page links to another domain url
                                   matrix[pos][i] = connection  #put a 1 at the right position. matrix[row][column]
                            break
                        except:
                            matrix[pos] = decoding_error # code for indicating decoding error
                            break
            except:
                matrix[pos] = WM_error # code for indicating IA/WM error
        if position == 1:
            matrixA = matrix
            matrix = numpy.zeros((row_count, row_count)) #reset matrix
        else:
            matrixB = matrix        
        position = position + 1

    if len(dates['second']) > 0:
        final_matrix = numpy.add(matrixA, matrixB)
    else:
        final_matrix = matrixA

    with open('output/output.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in final_matrix:
            writer.writerow(row)
    csvfile.close()
    print("The program is finished!")
