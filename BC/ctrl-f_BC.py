#requirements
import csv
import numpy
import nltk
from nltk.corpus import stopwords
from nltk.collocations import *
import requests
from bs4 import BeautifulSoup 
import caffeine
import re
from web_monitoring import internetarchive
from datetime import datetime
from archivenow import archivenow

default_stopwords = set(nltk.corpus.stopwords.words('english'))
all_stopwords = default_stopwords

keywords = {}
final_urls={}

# Archive a set of scraped URLs
def archiver(file):
    #file = 'BC_URLs_11-15-18.csv' | 'ACS_NCI_urls_2018-12-19.csv'

    with open(file) as csvfile:
        read=csv.reader(csvfile)
        data=list(read)
    csvfile.close()

    final={} # the final set of archived URLs

    # Go through each URL and try to push its live state to the Wayback Machine. If that's not possible, we'll try to look up previous versions of it. Otherwise, we give up.
    for each in data:
        url=each[0]
        final[url]=url
        res=archivenow.push(url, "ia")[0] # try archiving to the Internet Archive's Wayback Machine
        if "Error (The Internet Archive)" in res: # If we couldn't push the url to the Wayback Machine, try accessing previous versions
            try:
                with internetarchive.WaybackClient() as client:
                       dump = client.list_versions(url, from_date=datetime(2018, 5,15), to_date=datetime(2018, 11, 15)) # list_versions calls the CDX API from internetarchive.py from the webmonitoring repo
                       versions = reversed(list(dump))
                       print("internet archiving for: "+url)
                       for version in versions: # for each version in all the snapshots
                           if version.status_code == '200' or version.status_code == '-': # if the IA snapshot was viable
                               wmurl=version.raw_url
                               final[url]=wmurl
                               break
                           else:
                               pass
            except:
                print("couldn't access previous versions for: "+url)
                final[url]=url #if we can't access previous versions, give up
        else:
            final[url]=res #if we got a successful push to WM, log it

    with open('output/urlsWM.csv','w') as output:
        writer=csv.writer(output)
        for key, value in final.items():
            writer.writerow([key, value])
    output.close()       

#text count functions
def count(term, visible_text): # this function counts single word terms from the decoded HTML
    term = term.lower()  # normalize so as to make result case insensitive
    tally = 0
    for section in visible_text:
    	##bigram here. instead of section.split, bigram the section
        for token in section.split():
            token = re.sub(r'[^\w\s]','',token)#remove punctuation
            tally += int(term == token.lower()) # instead of in do ==
    #print("count",term, tally)
    return tally

def two_count(term, visible_text):
    tally=0
    length=len(term)
    for section in visible_text:
        tokens=nltk.word_tokenize(section)
        tokens=[x.lower() for x in tokens]
        tokens=[re.sub(r'[^\w\s]','',x) for x in tokens]
        grams=nltk.ngrams(tokens,length)
        try:
            fdist=nltk.FreqDist(grams)
            tally+=fdist[term[0].lower(),term[1].lower()]
        except:
            pass
    return tally

def three_count(term, visible_text):
    tally=0
    length=len(term)
    for section in visible_text:
        tokens=nltk.word_tokenize(section)
        tokens=[x.lower() for x in tokens]
        tokens=[re.sub(r'[^\w\s]','',x) for x in tokens]
        grams=nltk.ngrams(tokens,length)
        try:
            fdist=nltk.FreqDist(grams)
            tally+=fdist[term[0].lower(),term[1].lower(),term[2].lower()]
        except:
            pass
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
        
def counter(file, terms):
    #terms = ['environmental', 'environment', 'chemical', 'chemicals', 'contaminant', 'contaminants', 'contamination', 'pollution', 'pollutants', 'pollutant', ['endocrine', 'disruptor'], ['endocrine', 'disruptors'], ['endocrine', 'disrupting', 'chemical'], ['endocrine', 'disrupting', 'chemicals'], 'prevention', 'toxic', 'toxics', 'toxin', 'toxins', 'pfoa', 'pfos', 'pfas', 'pfcs', 'pfc', ['perfluorinated', 'chemicals'], ['precautionary', 'principle'], ['hormone', 'disrupting', 'chemical'], ['hormone', 'disrupting', 'chemicals'], 'pesticide', 'pesticides', ['flame', 'retardant'], ['flame', 'retardants'], 'bpa', 'phthalates', 'phthalate', 'paraben', 'parabens', 'bisphenol', 'bisphenols', 'lead', 'oxybenzone', 'diet', 'exercise', 'genetics', ['family', 'history'], 'obese', 'overweight', ['pregnancy', 'history'], 'alcohol', ['dense', 'breasts'], ['physically', 'active'], ['oral', 'contraceptives'], ['birth', 'control'], 'des', 'diethylstilbestrol', ['hormone', 'therapy'], 'hrt', 'pah', 'pahs', ['air', 'pollution'], ['physical', 'activity'], ['breast', 'density'], 'black', ['african', 'american'], ['african', 'americans'], 'african-american', 'african-americans', 'latina', 'latinas', 'hispanic', 'latino', 'asian', 'disparity', 'disparities', 'brac1', 'brac2', 'native-american', 'native-americans', ['native', 'americans'], ['native', 'american'], 'ethnicity']
    #file = 'BC_URLs_WM_11-16-18.csv' # 'ACS-NCI_urlsWM_12-21-18.csv'

    #Load the URLs
    with open(file) as csvfile: 
        read = csv.reader(csvfile)
        data = list(read)
    csvfile.close()
    
    # Construct matrix for storing term counts  
    row_count = len(data)
    column_count = len(terms)
    matrix = numpy.zeros((row_count, column_count)) 
    print(row_count, column_count)

    for pos, row in enumerate(data):
        url = row[1] #or 0 depending on how the CSV is structured 
        final_urls[url]=""
        try:
            contents = requests.get(url, timeout=5).content.decode() # Decode the url's HTML. Set a timeout for 5 seconds in cases where the site is down.
            soup = BeautifulSoup(contents, 'lxml')
            #Remove the following elements from consideration:
            d=[s.extract() for s in soup('footer')]
            d=[s.extract() for s in soup('nav')]
            d=[s.extract() for s in soup('script')]
            d=[s.extract() for s in soup('style')]
            d=[s.extract() for s in soup("div", {"id" : re.compile('nav*')})] # Remove elements where the id includes nav (adelphi)
            d=[s.extract() for s in soup("div", {"class" : re.compile('nav*')})] # Remove elements where the class includes nav
            d=[s.extract() for s in soup.select('div.link-list')] #ACS navigation menu
            d=[s.extract() for s in soup.select('div.menu-block-wrapper')] #LBBC carousel
            d=[s.extract() for s in soup.select('div.nav-main')] #bcaction navigation menu
            d=soup.find('div',{'id': 'linkGroup'})
            del(d)
            body=soup.find('body')
            contents=[text for text in body.stripped_strings]
            # Count terms and keywords:
            for p,t in enumerate(terms):
                if type(t) is list:
                    if len(t)>2:
                        page_sum=three_count(t,contents)
                    else:
                        page_sum=two_count(t,contents)
                else:
                    page_sum=count(t, contents)
                matrix[pos][p]=page_sum #put the count of the term in the matrix at the right location
            keywords[url] = keyword_function(contents)
            final_urls[url]=url # store the URL we looked up
            print(pos)
        except:
            print("failed ", pos)
            final_urls[url]=""
            matrix[pos]=999

    unique, counts = numpy.unique(matrix, return_counts=True)
    results = dict(zip(unique, counts))
    print (results)
    
    #for writing the term count to a csv. you will need to convert delimited text to columns and replace the first column with the list of URLs
    with open('outputs/counts.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in matrix:
            writer.writerow(row)
    csvfile.close()

    #print out urls in separate file
    with open('outputs/urls.csv','w') as output:
        writer=csv.writer(output)
        for key, value in final_urls.items():
            writer.writerow([key, value])
    output.close()

    #print out the top three keywords in a separate file
    with open("outputs/keywords.csv", "w", encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        for key, value in keywords.items():
            try:
                writer.writerow([key, value[0], value[1], value[2]])
            except IndexError:
                writer.writerow([key, "ERROR"])
    outfile.close()

    print("The program is finished!")
