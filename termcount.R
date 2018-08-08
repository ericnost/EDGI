library(readr) #if not already installed, install.packages("readr")
library(openxlsx) #if not already installed, install.packages("openxlsx")

first <- read_csv("input/R/term_count_output_obama_r.csv", col_names = FALSE) #load in the first timeframe's data - in this case, Obama era counts
second <- read_csv("input/R/term_count_output_trump_r.csv", col_names = FALSE) #load in the second timeframe's data - in this case, Trump era counts
combined<-second-first #this does matrix math to calculate, for each page and term, the change (positive, negative, or zero) in usage

terms<-read_csv("input/R/term_count_output_trump.csv") #load in a CSV that has the list of terms - this is for formatting outputs
ts<-terms[,-c(1:2, 25,26,27)] #keep only the terms
ts<-colnames(ts)
urls <- read_csv("input/R/term_count_output_obama.csv", col_names = FALSE) #load in a CSV that has a list of the URLs - could draw from the previous load...
urls<- urls[1]
output<-urls
colnames(output)<-c("site") #final list of URLs

wb <- createWorkbook("term-counts") #go ahead and set up the Excel file we'll send the output to

#below is the main function of the script: to go through each term and pull out only the URLs an available Wayback Machine snapshot in both timeframes AND there was no change but the term was used in both timeframes (e.g. 11 to 11) OR there was change (e.g. 0 to 1, 12 to 0, etc.)
for (i in 1:length(first)){
  #the first thing we'll do is set up the data for this term
  print(ts[i]) #the term we're working on right now
  col<-first[i] #from the first timeframe, the term count
  tcol<-second[i] #from the second teimframe, the term count
  colcombined<-combined[i] #second - first count, for this term
  urlsDump<-urls # a temporary variable for our URLs
  
  #shed NAs - We won't count pages where no snapshot was found in either first or second timeframe or both
  nas<-which(is.na(colcombined))
  col<-col[-c(nas),]
  tcol<-tcol[-c(nas),]
  colcombined<-colcombined[-c(nas),]
  urlsDump<-urlsDump[-c(nas),]
  
  #shed zeros - We won't count pages where the term count was 0 in BOTH the first and second timeframes
  zeros<-which(col==0 & tcol==0) #colcombined==0 <- no change
  colcombined<-data.frame(colcombined)
  col<-col[-c(zeros),]
  tcol<-tcol[-c(zeros),]
  urlsDump<-urlsDump[-c(zeros),1]
  colcombined<-colcombined[-c(zeros),]
  
  #Here we bring together, for the current term, the first era, second era, and combined counts, for outputting as a CSV
  combo<-cbind(urlsDump, col, tcol, colcombined)
  colnames(combo)<-c("site", paste(c("first", ts[i]), collapse = " "), paste(c("second", ts[i]), collapse = " "), paste(c("combined", ts[i]), collapse = " "))
  
  #debugging
  #output<-merge(combo, output, by="site", all=TRUE)
  #print(sum(colcombined, na.rm=TRUE)/sum(col, na.rm=TRUE))
  
  #write output to an Excel workbook sheet
  addWorksheet(wb, ts[i])
  writeData(wb, sheet = ts[i], combo)
}

#print the Excel file
saveWorkbook(wb, "output/term_count_output_R.xlsx", overwrite = TRUE)