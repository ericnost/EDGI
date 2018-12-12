library(readr) #if not already installed, install.packages("readr")
library(openxlsx) #if not already installed, install.packages("openxlsx")
library(dplyr) # etc.
library(ggplot2)
library(ggrepel)
setwd("~/OneDrive - University of Guelph/research/webmon_workspace/EDGI") # Set your own working directory here e.g. "~/My files/EDGI/"

first <- read_csv("outputs/main/term count obama1-7/obama_count_r.csv", col_names = FALSE) #load in the first timeframe's data - in this case, Obama era counts
second <- read_csv("outputs/main/term count trump1-7/trump_count_r.csv", col_names = FALSE) #load in the second timeframe's data - in this case, Trump era counts

#convert missing values (999) due to WM error to NAs
first[first==999] <- NA
second[second==999] <- NA

terms<-read_csv("inputs/terms.csv", col_names = FALSE) #load in a CSV that has the list of terms - this is for formatting outputs
terms<-tolower(terms)
#ts<-grep('clean energy', terms) #test
colnames(first)<-terms
colnames(second)<-terms

urls <- read_csv("inputs/counted_urls.csv") #load in a CSV that has a list of the URLs, organizations, etc.

## RECOUNTS
# add in recounts - OBAMA
recounts <- read_csv("outputs/dump/2016BLM-DOE-OSHA_counts.csv", col_names = FALSE)
tt<-append(terms, "index", after=0)
colnames(recounts)<-tt
for (org in c("DOE", "BLM", "OSHA")){
  urls_recounts<-which(urls$org==org)
  recounts_selected<-recounts[recounts$index %in% urls_recounts,] #subset to selected org
  first[c(urls_recounts),]<-recounts_selected[,2:57]
}
# Do a manual recount for selected DOE pages and term ('efficiency'). Extra 4 uses on many DOE pages in Obama era.
# find urls that include "energy.gov/eere"
urls.manual<-grep('energy.gov/eere', urls$`url - o`)
# subtract 4 for navbar and footer counts
first[c(urls.manual),'efficiency']<-first[c(urls.manual),'efficiency']-4

# add in recounts - TRUMP
recounts <- read_csv("outputs/dump/2018BLM-DOE-OSHA_counts.csv", col_names = FALSE)
tt<-append(terms, "index", after=0)
colnames(recounts)<-tt
for (org in c("DOE", "BLM", "OSHA")){
  urls_recounts<-which(urls$org==org)
  recounts_selected<-recounts[recounts$index %in% urls_recounts,] #subset to selected org
  second[c(urls_recounts),]<-recounts_selected[,2:57]
}

combined<-second-first #this does matrix math to calculate, for each page and term, the change (positive, negative, or zero) in usage

#### PROCESSING
## Handle duplicated URLs - find their "index"....
duplicates<-which(duplicated(urls$`url - o`) | duplicated(urls$`url - o`, fromLast = TRUE)) #url duplicates
duplicates.short<-which(duplicated(urls$`shortened url - o`) | duplicated(urls$`shortened url - o`, fromLast = TRUE))#shortened url duplicates
duplicates<-c(duplicates, duplicates.short)
duplicates<-unique(duplicates)

#....and then filter away
first<-first[-c(duplicates),]
second<-second[-c(duplicates),]
combined<-combined[-c(duplicates),]
urls<-urls[-c(duplicates),]

## Handle pages we don't want (e.g. Jan 2017 snapshots, blogs, Spanish-language pages)
pages.snapshots<-grep('snapshot', urls$`url - o`)
pages.edu<-grep('edu/', urls$`url - o`)
pages.news<-grep('news', urls$`url - o`)
pages.blog<-grep('blog', urls$`url - o`)
pages.News<-grep('News', urls$`url - o`)
pages.espanol<-grep('espanol', urls$`url - o`)

pages.length<-sapply(gregexpr("/", urls$`url - o`), length) # gets the number of slashes in each url (a proxy for importance/relevance)
pages.length<-which(pages.length > 6) # remove pages greater than 6 slashes. arbitrary, but remember that every url will have at least 3 slashes - http://wwww.epa.gov/....
#http://www.epa.gov/theme/subtheme/page/

dump<-c(pages.snapshots,pages.edu, pages.news,pages.blog, pages.News, pages.espanol, pages.length)
dump<-unique(dump)

first<-first[-c(dump),]
second<-second[-c(dump),]
combined<-combined[-c(dump),]
urls<-urls[-c(dump),]

##compare only on snapshots in both timeframes
snaps<-which(!is.na(urls$`captured url - 0`) & !is.na(urls$`final captured url - t`))
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


## Optional filter to only climate-related pages
#filter our list to only those pages concerning the "climate" topic - that is, where the Obama version mentioned "climate" "climate change" or "GHG"
cc<-which(first[,'climate']>0 | first[,'climate change']>0 | first[,'greenhouse gases']>0) # page indices where Obama used these terms
first<-first[c(cc),]
second<-second[c(cc),]
combined<-combined[c(cc),]
urls<-urls[c(cc),]

## load in document length information where we have it
obamaDocLength <- read_csv("outputs/main/term count obama1-7/obama_doc-length.csv")
colnames(obamaDocLength)<-c("url", "obama_text_length", "obama_link_count")
trumpDocLength <- read_csv("outputs/main/term count trump1-7/trump_doc-length.csv")
colnames(trumpDocLength)<-c("url", "trump_text_length", "trump_link_count")

#### DEBUG
##verify obama and trump urls match
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

by.org<-urls%>% group_by(org) %>%summarise(num_of_pages=n()) # summarize all URLs by org

# create worksheets
addWorksheet(wb, "overall")
for (o in 1:nrow(by.org)){
  addWorksheet(wb2, by.org[o,]$org)
}
# Go through each term and do the math!
for (i in 1:length(terms)){
  addWorksheet(sb, terms[i])
  addWorksheet(wb, terms[i])
  addWorksheet(fish, terms[i])
  #report by org and count
  #pctchg<-unlist(combined[i]/first[i])
  pc<-which(is.na(combined[i]/first[i])) 
  combined.url<-cbind(urls[c(1,3,6,8)], first[i], second[i], combined[i]) #combined.url is only the urls that aren't NA. In other words, we exclude 0/0 (0 obama, 0 change) 
  combined.url<-combined.url[-c(pc),]
  colnames(combined.url)<-c("url", "obama wm", "trump wm", "org", "before", "after","diff")
  
  # debug/fishy check
  #fishy.before<-combined.url%>%group_by(before,org)%>%mutate(pages=n())%>%distinct(before,org,pages)
  #fishy.before<-merge(fishy.before, by.org, by='org')
  #writeData(fish, sheet = terms[i], fishy.before)
  
  # print list of counts
  listOfCounts<-cbind(terms[i],sum(combined.url$before), sum(combined.url$after), sum(combined.url$diff), 100*(sum(combined.url$diff)/sum(combined.url$before)), nrow(combined.url)) #sum(first[i]), sum(second[i]), sum(combined[i]), 100*(sum(combined[i])/sum(first[i])))
  #diganostic<-cbind(first[i], second[i], combined[i], urls$`captured url - 0`, urls$`final captured url - t`)
  writeData(wb, sheet = "overall", listOfCounts, startRow = i+1, colNames = FALSE)
  
  # Do stats for changes by term
  stats<-combined.url%>% group_by(org) %>%summarise(ObamaSum=sum(before), TrumpSum=sum(after), overall_pct_chg = 100*(sum(diff)/sum(before)), num_of_pages=n())
  stats<-merge(stats, by.org, by = "org")
  stats$pct<-(stats$num_of_pages.x/stats$num_of_pages.y)*100
  
  # Put together the full term count including 0s
  full<-cbind(urls[c(1,3,6,8)], first[i], second[i], combined[i], 100*(combined[i]/first[i]))
  colnames(full)<-c("url", "obama wm", "trump wm", "org", "before", "after","diff","pctdiff")
  full<-merge(full, obamaDocLength, by="url", all.x=TRUE)
  full<-merge(full, trumpDocLength, by="url", all.x=TRUE)
  
  writeData(wb, sheet = terms[i], stats, startRow = 1, colNames = TRUE)
  writeData(wb, sheet = terms[i], combined.url, startRow = nrow(stats)+2, colNames = TRUE)
  writeData(sb, sheet = terms[i], full, colNames = TRUE)
  
  #visualize term data by agency - changes in average use
  #calculate obama rate of use, trump rate of use
  # stats.viz<-stats
  # stats.viz$Obamadensity<-stats.viz$ObamaSum/stats.viz$num_of_pages.y #rate of use across all agency pages
  # stats.viz$Obamaintensity<-stats.viz$ObamaSum/stats.viz$num_of_pages.x #rate of use across the pages it's used on
  # stats.viz$Trumpdensity<-stats.viz$TrumpSum/stats.viz$num_of_pages.y #rate of use across all agency pages
  # stats.viz$Trumpintensity<-stats.viz$TrumpSum/stats.viz$num_of_pages.x #rate of use across the pages it's used on
  # title<-paste(terms[i], "- use per page by agency")
  # file<-paste("outputs/figures/by term/",title,".png", sep="")  #save
  # p<-ggplot(stats.viz,aes(x = Obamadensity,y = Trumpdensity, label = stats.viz$org))+
  #   geom_point(aes(x = Obamadensity,y = Trumpdensity), size=2, color="black") +
  #   labs(x="2016", y="2018", title=title) +
  #   geom_text_repel(colour='dark grey')
  # 
  # p + theme(text=element_text(size=12), panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
  #           plot.background=element_rect(fill='white'), panel.background = element_rect(fill='white'), legend.position="none", axis.line = element_line(colour = "black", size=.1)) + geom_abline(intercept=0, slope=1, colour="grey", linetype=2, size=.2)   #+ scale_color_manual(values=c("#ef8a62", "#67a9cf"))#+  scale_color_brewer(palette="Paired")#+geom_text(aes(label=url),hjust=0, vjust=0, size = 2)
  # ggsave(file, plot=last_plot())
  
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
saveWorkbook(wb, "outputs/climate/stats_by_term.xlsx", overwrite = TRUE)
saveWorkbook(wb2, "outputs/climate/stats_by_agency.xlsx", overwrite = TRUE)
#saveWorkbook(fish, "outputs/repeated_term_use-Obama.xlsx", overwrite = TRUE)
saveWorkbook(sb, "outputs/climate/term_counts_full.xlsx", overwrite = TRUE)

#####TERM PAIRINGS AND PLOTS
library(ggplot2)
library(gridExtra)
library(dplyr)
#for each term, plot overall and by agency
for (i in 1:length(terms)){
  df<-data.frame(first[,i], second[,i], urls$org)
  colnames(df)<-c("obama", "trump", "org")
  #REMOVE ZEROS - we don't want to plot pages that didn't change
  change<-which(df$obama != 0 | df$trump != 0)
  df<-df[c(change),]
  
  if(nrow(df)>0){
    df.unique<-df %>% group_by(obama, trump) %>%mutate(count = n()) # count of unique count pairings by URLs. (1,2 | 1,4 | 3,1 | etc.) How many of each change 1->2, 1->4, 3->1 are there?
    df.unique<-unique(df.unique) #unique pairings reduced
    
    file<-paste("outputs/figures/by term/",terms[i],".png", sep="") # create and output the plot
    png(file = file, bg = "white")
    with(df.unique, symbols(x=obama, y=trump, circles=sqrt(count), inches=1/3, bg="steelblue2", fg=NULL, main=terms[i], xlab="2016", ylab="2018")) #sqrt for normalizing big values
    abline(0,1)
    dev.off()
  }
  
  for (o in 1:nrow(by.org)){
    df.filter<-filter(df, org==by.org[o,]$org) # filter by organization
    if (nrow(df.filter)>0){
      df.filter.unique<-df.filter %>% group_by(obama, trump) %>%mutate(count = n())
      df.filter.unique<-unique(df.filter.unique)
      title<-paste(terms[i], by.org[o,]$org)
      
      file<-paste("outputs/figures/by agency/",title,".png", sep="") # create and output the plot
      png(file = file, bg = "white")
      with(df.filter.unique, symbols(x=obama, y=trump, circles=sqrt(count), inches=1/3, bg="steelblue2", fg=NULL, main=title, xlab="2016", ylab="2018")) #sqrt for normalizing big values
      abline(0,1)
      dev.off()
    }
  }
}  
  


#### HERE BE DRAGONS - unhelpful or in-development analyses

#### CORRELATIONS
wbc <- createWorkbook("term-corrls") #workbook for correlations
for (i in 1:length(first)) {
  addWorksheet(wbc, terms[i])
  for (j in 2:length(first)){
    i=9
    j=43
    print(paste(terms[i],terms[j], sep=" + "))
    col<-first[i]
    corrcol<-first[j]
    combination<-col-corrcol
    urlsDump<-urls # a temporary variable for our URLs
    #shed nas
    nas<-which(is.na(combination))
    col<-col[-c(nas),]
    corrcol<-corrcol[-c(nas),]
    urlsDump<-urlsDump[-c(nas),]
    #shed zeros
    zeros<-which(col==0 & corrcol==0) #colcombined==0 <- no change
    col<-col[-c(zeros),]
    corrcol<-corrcol[-c(zeros),]
    urlsDump<-urlsDump[-c(zeros),1]
    #get correlation coeffcients
    col<-data.frame(col)
    corrcol<-data.frame(corrcol)
    model<-lm(corrcol[,1]~col[,1])
    r<-summary(model)$adj.r.squared
    intercept<-coefficients(model)[["(Intercept)"]]
    s<-coefficients(model)[["col[, 1]"]]
    listOfCorrls<-cbind(terms[i], terms[j], intercept,s,r)
    writeData(wbc, sheet = terms[i], listOfCorrls, startRow = j, colNames = FALSE)
  }
  
}
saveWorkbook(wbc, "outputs/term_corrl_output_R.xlsx", overwrite = TRUE)

#### LINKER
library(splitstackshape)
library (dplyr)
library (tidyr)
library(readr)
connections <- read_csv("outputs/main/linker output 1-7/linker_output_full.csv", col_names = FALSE) #load in the first timeframe's data - in this case, Obama era counts
# /Users/enost/OneDrive - University of Guelph/research/webmon_workspace/EDGI/
urls<-read_csv("inputs/epaURLs_polished.csv", col_names=FALSE)
redirects<-read_csv("missing r.csv", col_names=FALSE)
redirects<-redirects[,1]
cx<-separate(connections, X1, into=urls$X1, sep=" ", convert=TRUE)
#connections<-cSplit(connections, 1:ncol(connections), sep=" ", type.convert=TRUE)
#errors.both<-which(cx[,1]==22 | cx[,1] ==23, cx[,1]==24, cx[,1]==25)#etc.
keep<-which(cx[,1]==0 | cx[,1]==1 | cx[,1]==3 | cx[,1]==4)
#connect2WMerror<-which(cx[,1]==17)
#urls<-urls[connect2WMerror,]
cx<-cx[keep,keep]
urls<-urls[keep,]

nones<-data.frame(which(cx==0, arr.ind = TRUE))
removals<-data.frame(which(cx==1, arr.ind = TRUE))
added<-data.frame(which(cx==3, arr.ind = TRUE))
both<-data.frame(which(cx==4, arr.ind = TRUE))

added.graph<-data.frame(matrix(NA, nrow=nrow(added), ncol=2))
colnames(added.graph)<-c("from", "to")
for (i in 1:nrow(added)){
  from<-added[i,]$row
  to<-added[i,]$col
  added.graph$from[i]<-urls[from,]
  added.graph$to[i]<-urls[to,]
}
  
removals.graph<-data.frame(matrix(NA, nrow=nrow(removals), ncol=2))
colnames(removals.graph)<-c("from", "to")
for (i in 1:nrow(removals)){
  i=4
  from<-removals[i,]$row
  to<-removals[i,]$col
  removals.graph$from[i]<-urls[from,]
  removals.graph$to[i]<-urls[to,]
}

#exclude removals that were redirects
#remove row if to value is in redirects
rz<-which(removals.graph$to %in% redirects$X1 | removals.graph$to == "/" | removals.graph$from %in% redirects$X1)
removals.fixed<-removals.graph[-rz,]
removals.fixed <- apply(removals.fixed,2,as.character)
write.csv(removals.fixed, file="thingsNotLinkingAnymore.csv")
#filter removals to / - this suggests where pages may have been removed
r<-which(removals.graph$to=="/")
missing<-removals.graph[r,]
missing <- apply(missing,2,as.character)
write.csv(missing, file="missingmaybe.csv")

uniqueMissingTo<-removals.graph[!duplicated(removals.graph[,c('to')]),]
uniqueMissingTo <- apply(uniqueMissingTo,2,as.character)
write.csv(uniqueMissingTo, file="uniquemissingto.csv")

#what are the climate urls?
cc<-grep("/climatechange", names(cx))
cc<-cx[cc,cc]
  
