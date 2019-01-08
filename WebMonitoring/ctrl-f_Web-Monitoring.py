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
    #print(term, tally)
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
		tally += fdist[term[0].lower(), term[1].lower()] #change for specific terms
	#print(term, tally)    
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
    #print(keydump)
    return keydump
       
def counter(file, terms, dates):
    #terms = ['adaptation', ['Agency', 'Mission'], ['air', 'quality'], 'anthropogenic', 'benefits', 'Brownfield', ['clean', 'energy'], 'Climate', ['climate', 'change'], 'Compliance', 'Cost-effective', 'Costs', 'Deregulatory', 'deregulation', 'droughts', ['economic', 'certainty'], ['economic', 'impacts'], 'economic', 'Efficiency', 'Emissions', ['endangered', 'species'], ['energy', 'independence'], 'Enforcement', ['environmental', 'justice'], ['federal', 'customer'], ['fossil', 'fuels'], 'Fracking', ['global', 'warming'], 'glyphosate', ['greenhouse', 'gases'], ['horizontal', 'drilling'], ['hydraulic', 'fracturing'], 'Impacts', 'Innovation', 'Jobs', 'Mercury', 'Methane', 'pesticides', 'pollution', 'Precautionary', ['regulatory', 'certainty'], 'regulation', 'Resilience', 'Risk', 'Safe', 'Safety', ['sensible', 'regulations'], 'state', 'storms', 'sustainability', 'Toxic', 'transparency', ['Unconventional', 'gas'], ['unconventional', 'oil'], ['Water', 'quality'], 'wildfires']
    #file = 'all Versionista URLs 10-16-18.csv'

    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read)
    csvfile.close()
  
    row_count = len(data)
    column_count = len(terms)
    matrix = numpy.zeros((row_count, column_count),dtype=numpy.int16) 
    print(row_count, column_count)
    
    for pos, row in enumerate(data):
          thisPage = row[0] #change for specific CSVs
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
                          d=[s.extract() for s in body('footer')]
                          d=[s.extract() for s in body('header')]
                          d=[s.extract() for s in body('nav')]
                          d=[s.extract() for s in body('script')]
                          d=[s.extract() for s in body('style')]
                          d=[s.extract() for s in body.select('div > #menuh')] #FWS
                          d=[s.extract() for s in body.select('div > #siteFooter')] #FWS
                          d=[s.extract() for s in body.select('div.primary-nav')] #DOE
                          d=[s.extract() for s in body.select('div > #nav-homepage-header')] #OSHA
                          d=[s.extract() for s in body.select('div > #footer-two')] #OSHA
                          del d
                          body=[text for text in body.stripped_strings]
                          for p, t in enumerate(terms):
                                if type(t) is list:
                                    page_sum = two_count(t, body)
                                else:
                                    page_sum = count(t, body)
                                matrix[pos][p]=page_sum #put the count of the term in the matrix
                          keywords[url] = keyword_function(body)
                          final_urls[thisPage]=[url, row[3]]
                          print(pos)
                          break
                       else:
                          pass
          except:
              print("fail")
              final_urls[thisPage]=["", row[3]]
              matrix[pos]=999
         
    unique, counts = numpy.unique(matrix, return_counts=True)
    results = dict(zip(unique, counts))
    print (results)
    
    #for writing term counts to a csv. you will need to convert delimited text to columns and replace the first column with the list of URLs
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

    #print out keywords in separate file
    with open("outputs/keywords.csv", "w", encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        for key, value in keywords.items():
            try:
                writer.writerow([key, value[0], value[1], value[2]])
            except IndexError:
                writer.writerow([key, "ERROR"])
    outfile.close()

    print("The program is finished!")