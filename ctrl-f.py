#requirements
import csv
import numpy
import nltk
from nltk.corpus import stopwords
from nltk.collocations import *
from web_monitoring import db
from web_monitoring import internetarchive
from web_monitoring import differs
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import caffeine
import re

default_stopwords = set(nltk.corpus.stopwords.words('english'))
all_stopwords = default_stopwords

keywords = {}
final_urls={}
    
#text count functions
def count(term, visible_text): # this function counts single word terms from the decoded HTML
    term = term.lower()  # normalize so as to make result case insensitive
    tally = 0
    for section in visible_text:
        for token in section.split():
            token = re.sub(r'[^\w\s]','',token)#remove punctuation
            tally += int(term == token.lower()) # instead of in do ==
    return tally

def two_count (term, visible_text): #this function counts two word phrases from the decoded HTML
	tally = 0
	length = len(term)
	for section in visible_text:
		tokens = nltk.word_tokenize(section)
		tokens = [x.lower() for x in tokens] #standardize to lowercase
		tokens = [re.sub(r'[^\w\s]','',x) for x in tokens]
		grams=nltk.ngrams(tokens,length)
		fdist = nltk.FreqDist(grams)
		tally += fdist[term[0].lower(), term[1].lower()]   
	return tally

def keyword_function(visible_text):
    #based on https://www.strehle.de/tim/weblog/archives/2015/09/03/1569
    keydump=[]
    #visible_text = gvt(content)
    new_string = "".join(visible_text)
    words = nltk.word_tokenize(new_string)
    # Remove single-character tokens (mostly punctuation)
    words = [word for word in words if len(word) > 1]
    # Remove numbers
    words = [word for word in words if not word.isnumeric()]    
    # Lowercase all words (default_stopwords are lowercase too)
    words = [word.lower() for word in words]
    # Remove stopwords
    words = [word for word in words if word not in all_stopwords]
    # Calculate frequency distribution
    fdist = nltk.FreqDist(words)
    # Output top 50 words
    for word, frequency in fdist.most_common(3):
        keydump.append(word)
    return keydump
             
def counter(file, terms, dates):
    #counts a set of one or two word terms during a single timeframe
    #dates should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]
    #terms should be in the format ["term"], as a phrase: ["climate", "change"], or as a set of terms and/or phrases: ["climate", ["climate", "change"]]
    
    #read the URLs
    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read)
    csvfile.close()

    #Start the matrix that we'll put term counts into
    row_count = len(data)
    column_count = len(terms)
    matrix = numpy.zeros((row_count, column_count),dtype=numpy.int16) 
    print(row_count, column_count)
    
    for pos, row in enumerate(data):
          thisPage = row[0]
          try:
              with internetarchive.WaybackClient() as client:
                   dump = client.list_versions(thisPage, from_date=datetime(dates[0], dates[1],dates[2]), to_date=datetime(dates[3], dates[4], dates[5])) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
                   versions = reversed(list(dump))
                   for version in versions: # for each version in all the snapshots
                       if version.status_code == '200' or version.status_code == '-': # if the IA snapshot was viable
                          url=version.raw_url
                          contents = requests.get(url).content.decode() #decode the url's HTML
                          contents = BeautifulSoup(contents, 'lxml')
                          body=contents.find('body')
                          # remove portions of the webpage we don't want to count
                          d=[s.extract() for s in body('footer')] 
                          d=[s.extract() for s in body('header')]
                          d=[s.extract() for s in body('nav')]
                          d=[s.extract() for s in body('script')]
                          d=[s.extract() for s in body('style')]
                          del d
                          body=[text for text in body.stripped_strings]
                          # Count terms:
                          for p, t in enumerate(terms):
                                if type(t) is list:
                                    page_sum = two_count(t, body)
                                else:
                                    page_sum = count(t, body)
                                matrix[pos][p]=page_sum # put the count of the term in the right spot in the matrix
                          keywords[url] = keyword_function(body)
                          final_urls[thisPage]=[url, row[3]]
                          print(pos)
                          break
                       else:
                          pass
          except:
              print("fail")
              final_urls[thisPage]=["", thisPage]
              matrix[pos]=999
 
    unique, counts = numpy.unique(matrix, return_counts=True)
    results = dict(zip(unique, counts))
    print (results)
    
    #for writing the term count to a CSV. You will then need to convert delimited text to columns and replace the first column with the list of URLs
    with open('outputs/counts.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in matrix:
            writer.writerow(row)
    csvfile.close()

    #print out urls in separate file
    with open('outputs/urls.csv','w') as output:
        writer=csv.writer(output)
        for key, value in final_urls.items():
            writer.writerow([key, value[0],value[1]])
    output.close()

    #print out top three keywords in separate file
    with open("outputs/keywords.csv", "w", encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        for key, value in keywords.items():
            try:
                writer.writerow([key, value[0], value[1], value[2]])
            except IndexError:
                writer.writerow([key, "ERROR"])
    outfile.close()

    print("The program is finished!")
  
def linker (file, domain, datesA, datesB=[]):
    #currently only accepts looking at how a set of URLs point to each other (a square matrix)
    #currently is meant to look at links in a single domain e.g. "http://www.epa.gov" File should be a csv of links like: "/cleanpowerplan/page"
    #datesA should be in the following form: [starting year, starting month, starting day, ending year, ending month, ending day]
    #datesB = optional (for comparing two time periods). should be in same format as datesA

    dates = {'first': datesA, 'second': datesB}

    finalURLs={}
    
    # build outgoing link matrix
    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read) #put the csv data in an array
        row_count = len(data)
        matrix = numpy.zeros((row_count, row_count),dtype=numpy.int8) #create matrix
        urls = []
        for row in data:
            finalURLs[domain+row[0]]=[]
            urls.append(row[0]) #compile list of all urls to check against later
    csvfile.close()

    times = 1
    if len(dates['second'])>0:
        times = 2
    position = 1

    #Loop through data, call CDX API, populate matrix
    while position <= times:
        if position == 1:
            theseDates = dates['first'] # These are the numeric codes used to ID link status in timeframe A, B, and combined (A+B)
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
                with internetarchive.WaybackClient() as client:
                    dump = client.list_versions(thisPage, from_date=datetime(theseDates[0], theseDates[1],theseDates[2]), to_date=datetime(theseDates[3], theseDates[4], theseDates[5])) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
                    versions = reversed(list(dump)) # start from the most recent snapshots
                    for version in versions: # for each version in all the snapshots
                        if version.status_code == '200': # if the IA snapshot was a redirect or page not found, move to the next snapshot version
                            try:
                                contents = requests.get(version.raw_url).content.decode() #decode the url's HTML
                                contents = BeautifulSoup(contents, 'lxml')
                                # remove portions of the webpage we don't want to count
                                d=[s.extract() for s in contents('script')]
                                d=[s.extract() for s in contents('style')]
                                del d
                                contents=contents.find("body")
                                links = contents.find_all('a') #find all outgoing links
                                thisPageLinksTo = []
                                for link in links:
                                    thisPageLinksTo.append(link['href']) #for each outgoing link, strip away the name etc. to just the href
                                #use keys/columns and check against links. is x key/column in links? does this page link to another? if so, add 1
                                for i, url in enumerate(urls):
                                    if url in thisPageLinksTo: #if this page links to another domain url
                                        #print(thisPage, url, wayback_url, pos, i) #print what this page is, what it links to, and IA url
                                       matrix[pos][i] = connection  #put a 1 at the right position. matrix[row][column]
                                finalURLs[thisPage].append(version.raw_url)
                                print(pos)
                                break
                            except:
                                finalURLs[thisPage].append("decoding error")
                                matrix[pos] = decoding_error # code for indicating decoding error
                                #print('decoding error', version.status_code, row[0])# this will capture errors in decoding a page
                                break
                        else:
                            pass
            except:
                finalURLs[thisPage].append("WM error")
                matrix[pos] = WM_error # code for indicating IA/WM error
        if position == 1:
            matrixA = matrix
            matrix = numpy.zeros((row_count, row_count),dtype=numpy.int8) #reset matrix
        else:
            matrixB = matrix        
        position = position + 1

    if len(dates['second']) > 0:
        final_matrix = numpy.add(matrixA, matrixB)
    else:
        final_matrix = matrixA

    with open('outputs/urls.csv','w') as output:
        writer=csv.writer(output)
        for key, value in finalURLs.items():
            try:
                writer.writerow([key, value[0], value[1]])
            except IndexError:
                writer.writerow([key, "ERROR"])
    output.close()
    with open('outputs/links.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in final_matrix:
            writer.writerow(row)
    csvfile.close()
    with open('outputs/linksA.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in matrixA:
            writer.writerow(row)
    csvfile.close()
    with open('outputs/linksB.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in matrixB:
            writer.writerow(row)
    csvfile.close()
    print("The program is finished!")

