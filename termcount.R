library(readr) #if not already installed, install.packages("readr")
library(openxlsx) #if not already installed, install.packages("openxlsx")
library(dplyr) #if not already installed, install.packages("dplyr")
library(ggplot2) #etc.
library(ggrepel)
library(gridExtra)

setwd("~/My files/EDGI/") # Set your own working directory here

first <- read_csv("input/R/first.csv", col_names = FALSE) #load in the first timeframe's data
second <- read_csv("input/R/second.csv", col_names = FALSE) #load in the second timeframe's data

# Convert missing values (999) due to WM error to NAs
first[first==999] <- NA
second[second==999] <- NA

terms<-read_csv("input/R/terms.csv", col_names = FALSE) #load in a CSV that has the list of terms - this is for formatting outputs
terms<-tolower(terms)
colnames(first)<-terms
colnames(second)<-terms

urls <- read_csv("input/R/counted_urls.csv") #load in a CSV that has a list of the URLs, organizations, etc. 

combined<-second-first #this does matrix math to calculate, for each page and term, the change (positive, negative, or zero) in usage

#### PROCESSING
## Handle duplicated URLs - find their "index"....
duplicates<-which(duplicated(urls$`url - o`) | duplicated(urls$`url - o`, fromLast = TRUE)) # URL duplicates. In this case the main URL column is 'url - o'
duplicates.short<-which(duplicated(urls$`shortened url - o`) | duplicated(urls$`shortened url - o`, fromLast = TRUE))#shortened url duplicates
duplicates<-c(duplicates, duplicates.short)
duplicates<-unique(duplicates)

#....and then filter away
first<-first[-c(duplicates),]
second<-second[-c(duplicates),]
combined<-combined[-c(duplicates),]
urls<-urls[-c(duplicates),]

## Handle pages we don't want (e.g. Jan 2017 snapshots, blogs, Spanish-language pages)
# example:
pages.snapshots<-grep('snapshot', urls$`url - o`)

pages.length<-sapply(gregexpr("/", urls$`url - o`), length) # gets the number of slashes in each url (a proxy for importance/relevance)
pages.length<-which(pages.length > 6) # remove pages greater than 6 slashes. arbitrary, but remember that every url will have at least 3 slashes - http://wwww.epa.gov/....
# example: http://www.epa.gov/theme/subtheme/page/

dump<-c(pages.snapshots, pages.length)
dump<-unique(dump)
first<-first[-c(dump),]
second<-second[-c(dump),]
combined<-combined[-c(dump),]
urls<-urls[-c(dump),]

##compare only on snapshots in both timeframes
snaps<-which(!is.na(urls$`captured url - o`) & !is.na(urls$`final captured url - t`)) # In this case captured url-o is the first time frame, final captured url - t is the second
first<-first[c(snaps),]
second<-second[c(snaps),]
combined<-combined[c(snaps),]
urls<-urls[c(snaps),]

##compare only on available counts (disregard NAs/999s)
nas<-which(is.na(first[,1])|is.na(second[,1]))
first<-first[-c(nas),]
second<-second[-c(nas),]
combined<-combined[-c(nas),]
urls<-urls[-c(nas),]

#### DEBUG
## verify URLs in each timeframe match
errors=0
for (i in 1:nrow(urls)) {
  if (tolower(urls$`shortened url - o`[i]) != tolower(urls$`shortened url - t`[i])){
    errors<-errors+1
    print(i)
  }
}

#### STATS
sb<- createWorkbook("term-counts-full") # print out all the counts
wb <- createWorkbook("term-counts") # print out counts by term
wb2 <- createWorkbook("term-counts-agency") # print out counts by agency
fish <- createWorkbook("fishy-check") # check for repeated use of terms

by.org<-urls%>% group_by(org) %>%summarise(num_of_pages=n()) # summarize all URLs by their host org

# Create worksheets in the term counts spreadsheet
addWorksheet(wb, "overall")
for (o in 1:nrow(by.org)){
  addWorksheet(wb2, by.org[o,]$org)
}
# Go through each term and do the math!
for (i in 1:length(terms)){
  addWorksheet(sb, terms[i])
  addWorksheet(wb, terms[i])
  addWorksheet(fish, terms[i])

  # Limit most of our analysis to those pages that actually used the term
  pc<-which(is.na(combined[i]/first[i])) # percent change
  combined.url<-cbind(urls[c(1,3,6,8)], first[i], second[i], combined[i]) #combined.url is only the urls that aren't NA. In other words, we exclude 0/0 (0 first, 0 second) 
  combined.url<-combined.url[-c(pc),]
  colnames(combined.url)<-c("url", "first", "second", "org", "before", "after","diff")
  
  # debug/fishy check
  #fishy.before<-combined.url%>%group_by(before,org)%>%mutate(pages=n())%>%distinct(before,org,pages)
  #fishy.before<-merge(fishy.before, by.org, by='org')
  #writeData(fish, sheet = terms[i], fishy.before)
  
  # Do overall count of the term
  listOfCounts<-cbind(terms[i],sum(combined.url$before), sum(combined.url$after), sum(combined.url$diff), 100*(sum(combined.url$diff)/sum(combined.url$before)), nrow(combined.url))
  writeData(wb, sheet = "overall", listOfCounts, startRow = i+1, colNames = FALSE)
  
  # Do stats for changes of the term by org
  stats<-combined.url%>% group_by(org) %>%summarise(FirstSum=sum(before), SecondSum=sum(after), overall_pct_chg = 100*(sum(diff)/sum(before)), num_of_pages=n())
  stats<-merge(stats, by.org, by = "org")
  stats$pct<-(stats$num_of_pages.x/stats$num_of_pages.y)*100
  
  # Put together the full term count including 0s
  full<-cbind(urls[c(1,3,6,8)], first[i], second[i], combined[i], 100*(combined[i]/first[i]))
  colnames(full)<-c("url", "first", "second", "org", "before", "after","diff","pctdiff")
  
  writeData(wb, sheet = terms[i], stats, startRow = 1, colNames = TRUE)
  writeData(wb, sheet = terms[i], combined.url, startRow = nrow(stats)+2, colNames = TRUE)
  writeData(sb, sheet = terms[i], full, colNames = TRUE)
  
  # do the stats by organization/agency
  for (o in 1:nrow(by.org)){
    thisAgency<-stats[stats$org == by.org[o,]$org,]
    if (nrow(thisAgency)==0){
      thisAgency<-cbind(terms[i], 0,0,0,0,0,0)
    } else{
      thisAgency<-cbind(terms[i], thisAgency[2:7])
    }
    writeData(wb2, sheet=by.org[o,]$org, thisAgency, startRow=i, colNames=FALSE)
  }
}
saveWorkbook(wb, "outputs/stats_by_term.xlsx", overwrite = TRUE)
saveWorkbook(wb2, "outputs/stats_by_agency.xlsx", overwrite = TRUE)
#saveWorkbook(fish, "outputs/repeated_term_use.xlsx", overwrite = TRUE)
saveWorkbook(sb, "outputs/term_counts_full.xlsx", overwrite = TRUE)

#####TERM PAIRINGS AND PLOTS
#for each term, plot its use overall and by agency
for (i in 1:length(terms)){
  df<-data.frame(first[,i], second[,i], urls$org)
  colnames(df)<-c("first", "second", "org")
  change<-which(df$first != 0 | df$second != 0) #remove zeros - optional, but we probably don't want to plot pages that went from 0....to....0
  df<-df[c(change),]
  
  if(nrow(df)>0){
    df.unique<-df %>% group_by(first, second) %>%mutate(count = n()) # count of unique count pairings by URLs. (1,2 | 1,4 | 3,1 | etc.) How many of each change 1->2, 1->4, 3->1 are there?
    df.unique<-unique(df.unique) # Unique pairings reduced
    
    file<-paste("outputs/figures/byterm/",terms[i],".png", sep="") # Create and output the plot
    png(file = file, bg = "white")
    with(df.unique, symbols(x=first, y=second, circles=sqrt(count), inches=1/3, bg="steelblue2", fg=NULL, main=terms[i], xlab="2016", ylab="2018")) #sqrt for normalizing big values
    abline(0,1)
    dev.off()
  }
  
  for (o in 1:nrow(by.org)){
    df.filter<-filter(df, org==by.org[o,]$org) # Filter by organization
    if (nrow(df.filter)>0){
      df.filter.unique<-df.filter %>% group_by(first, second) %>%mutate(count = n())
      df.filter.unique<-unique(df.filter.unique)
      title<-paste(terms[i], by.org[o,]$org)
      
      file<-paste("outputs/figures/by agency/",title,".png", sep="") # Create and output the plot
      png(file = file, bg = "white")
      with(df.filter.unique, symbols(x=first, y=second, circles=sqrt(count), inches=1/3, bg="steelblue2", fg=NULL, main=title, xlab="2016", ylab="2018")) #sqrt for normalizing big values
      abline(0,1)
      dev.off()
    }
  }
}  