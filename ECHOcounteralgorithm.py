#!/usr/bin/env python
# coding: utf-8

# In[1]:


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 29 11:11:56 2019

@author: Eric Nost, Environmental Data and Governance Initiative (EDGI)
"""

import requests
import time
import csv
import json
from statistics import *
from collections import Counter
import datetime


# In[2]:


# Prep the data
f = [] # save inspection data by facility name


# In[3]:


# The main script
# Loop through each of the 10 EPA regions and get the ECHO results for compliance information
x=1
while x < 11:
    region=str(x)
    if len(region)<2:
        region = "0"+region
    print("R"+region+"....") # Print out which region we're currently working on
    
    # call up ECHO
    url="https://ofmpub.epa.gov/echo/echo_rest_services.get_facility_info?output=json&p_reg="+region+"&p_act=Y&p_maj=Y&p_med=W"
    contents = requests.get(url).content.decode()
    obj = json.loads(contents) # Get the results from ECHO and turn them into something Python can work with
    
    facilities = obj['Results']['Facilities'] # Grab the information on the facilities
    
    for facility in facilities:
        f.append(facility['RegistryID'])
        # Go to the next facility...
        
    x+=1 # Go to the next EPA region


# In[4]:


# Python3 program for Naive Pattern 
# Searching algorithm
flagged=[]
def search(pat, txt): 
	M = len(pat) 
	N = len(txt) 

	# A loop to slide pat[] one by one */ 
	for i in range(N - M + 1): 
		j = 0
		
		# For current index i, check 
		# for pattern match */ 
		for j in range(0, M): 
			if (txt[i + j] != pat[j]): 
				break

		if (j == M - 1): 
			print("Pattern found at index ", i)
			flagged.append(fid)

# This code is contributed 
# by PrinciRaj1992 


# In[ ]:

seconds = 15

#look up each facility's CWA monthly violations
allstatuses = ""

flagged=[]

for fid in f[30:300]: #test on one or a few facilities eg 110032893661 110006618810
    # call up ECHO
    url="https://ofmpub.epa.gov/echo/dfr_rest_services.get_cwa_eff_compliance?output=JSON&p_id="+fid
    contents = requests.get(url, time.sleep(seconds)).content.decode() #try to avoid being detected as a robot
    obj = json.loads(contents) # Get the results from ECHO and turn them into something Python can work with
    try:
        if obj['Results']["CWAEffluentCompliance"]["Sources"]:

        #go through parameters
            for s in obj['Results']["CWAEffluentCompliance"]["Sources"]: #Not sure why there would be multiple sources. multiple pipes/sources of discharge?
                for p in s['Parameters']:
                    print(fid + ": " + p['ParameterName'])
                    x=1
                    nums=[]
                    statuses=""
                    while x<40: #loop through 39 months of data
                        code="Mnth"+str(x)+"Value"
                        if p[code] is not None and "%" in p[code]: #based on how ECHO is structured, need to find where there is a % over limit indicated
                            statuses = statuses + "V" #if over the limit, indicate a violation #statuses.append(x) 
                            # find the % of the limit that was exceeded by extracting the number from the string
                            pindex=p[code].find("%")
                            #find space
                            sindex=p[code].find(" ")
                            #splice to get numebr, convert to number
                            num=int(p[code][sindex:pindex])
                            nums.append(num)
                            print("V " + str(num) + "% above limit")
                        else: # facility did not exceed permit limit
                            statuses = statuses + "C"
                            num = 0
                            nums.append(num)
                            print("C")
                        if x % 3 == 0 and x >= 6: #check for suspicious patterns over last six months
                            #pattern: just 3 above limit - avoiding 4 month rule
                            xindex = x - 6
                            count = len([i for i in nums[xindex:x] if i > 0]) # number of times facility was over the limit
                            TRCcount = len([i for i in nums[xindex:x] if i > 39]) # number of times facility was over the 1.4 TRC threshold. #TO DO: change from 39 depending on pollutant group.
                           #print(nums[xindex:x], count, TRCcount)
                            if count == 3 and TRCcount <= 1:
                                print("suspicious? just 3 months above limit, only one or less of which was above TRC")
                                #count how many times this occurs for this facility/pollutant....
                                flagged.append({"fac": fid, "pollutant": p['ParameterName'], "range": [xindex, x]})
                        x+=1
                    allstatuses = allstatuses + statuses + " " #create a combo of all statuses for clustering and analysis later
                    #check for suspicious patterns here and send to flagged
                    # pattern: > 40% once every six months
# =============================================================================
#                     w1=nums[0:6]
#                     w2=nums[3:9]
#                     w3=nums[6:12]
#                     w4=nums[9:15]
#                     w5=nums[12:30]
#                     w6=nums[30:36]
#                     count1 = len([i for i in w1 if i > 40])
#                     count2= len([i for i in w2 if i > 40])
#                     count3= len([i for i in w3 if i > 40])
#                     count4= len([i for i in w4 if i > 40])
#                     count5= len([i for i in w5 if i > 40])
#                     count6= len([i for i in w6 if i > 40])
#                     counts = [count1, count2, count3, count4, count5, count6]
#                     sumcount = len([i for i in counts if i == 1])
#                     if sumcount > 2:
#                         print ("suspicious? 40% once every six months over at least 3 semesters")
# =============================================================================
                    #search("CCCCCVC", statuses) 
    except:
        print(fid+": failed")
        pass



# In[ ]:

#Various means of clustering status trends
        
#affinity propagation: https://stats.stackexchange.com/questions/123060/clustering-a-long-list-of-strings-words-into-similarity-groups
import numpy as np
import sklearn.cluster
import distance

words = allstatuses.split(" ")
words = np.asarray(words) #So that indexing with a list will work
lev_similarity = -1*np.array([[distance.levenshtein(w1,w2) for w1 in words] for w2 in words])

affprop = sklearn.cluster.AffinityPropagation(affinity="precomputed", damping=0.5)
affprop.fit(lev_similarity)
for cluster_id in np.unique(affprop.labels_):
    exemplar = words[affprop.cluster_centers_indices_[cluster_id]]
    cluster = np.unique(words[np.nonzero(affprop.labels_==cluster_id)])
    cluster_str = ", ".join(cluster)
    print(" - *%s:* %s" % (exemplar, cluster_str))


#kmeans clustering https://pythonprogramminglanguage.com/kmeans-text-clustering NOT SO APPROPRIATE given data structure
# =============================================================================
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.cluster import KMeans
# from sklearn.metrics import adjusted_rand_score
# 
# documents = allstatuses.split(" ")
# 
# vectorizer = TfidfVectorizer(stop_words='english')
# X = vectorizer.fit_transform(documents)
# 
# true_k = 2 #or another num
# model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)
# model.fit(X)
# 
# print("Top terms per cluster:")
# order_centroids = model.cluster_centers_.argsort()[:, ::-1]
# terms = vectorizer.get_feature_names()
# for i in range(true_k):
#     print("Cluster %d:" % i),
#     for ind in order_centroids[i, :10]:
#         print(' %s' % terms[ind]),
#     print
# 
# print("\n")
# =============================================================================

#BETTER KMEANS CLUSTERING
from sklearn.cluster import KMeans
words = allstatuses.split(" ")
matrix = np.zeros((len(words), 39), dtype=int)
for pos, status in enumerate(words):
    for m, month in enumerate(status):
        if month == "V":
            matrix[pos, m] = 1
model = KMeans(n_clusters=3)
model.fit(matrix)
labels = model.labels_
c0=list(np.where (labels==0))[0].tolist()
c1=list(np.where (labels==1))[0].tolist()
c2=list(np.where (labels==2))[0].tolist()
for c in [c0,c1,c2]:
    print("cluster:")
    for s in c:
        print(matrix[s].tolist()) #pretty formatting