
# coding: utf-8

# # Extracting author names

# Predicting author genders from OSP "text" table using the gender.py library, which is a python extension of genderize.io (https://genderize.io/)
# 
# Update: ranked by top authors by top text (there are repeats of authors) because there is no separate author table


from v1_db import session, Text, Citation

from sqlalchemy.sql import functions as func
from collections import Counter
import pandas as pd
import requests
from gender import getGenders


# IMPORT RPY2 PACKAGES

import rpy2.robjects as robjects
import rpy2.robjects.packages as rpackages
from rpy2.robjects.packages import importr
base = importr('base')
utils = importr('utils')
utils = rpackages.importr('utils')
utils.chooseCRANmirror(ind=1)
wiki = importr('WikidataR')


# R Wikidata lookup function:
# - approach: lookup keyword id's in search result to identify id's and necessary properties (author and gender)
# - function uses Wikidata id's (P1006 = National Thesaurus for Author Names ID, Q6581097 = male, Q6581072 = female)
# - tryCatch to prevent program crash when running an invalid name
# - function is made global so it can be accessed later on in the program
# - function f performs lookup, function g (which will be used later in the program) calls f and handles exceptions


robjects.r('''
    f <- function(name){
        all_results <- find_item(name)
        
        for(i in 1:length(all_results)){
            temp <- get_item(all_results[[i]]$id)
            if(regexpr('P1006', toString(temp)) != -1){
                break
            }
            
        }
        str = toString(temp)
  
        x = regexpr('Q6581097', str)
  
        if (regexpr('Q6581097', str) != -1){
            return("male")          
        }
        else if(regexpr('Q6581072', str) != -1){
            return("female")
        }
        else{
            return("other")
        }
    }
    
    g <- function(n){
        tryCatch(f(n), error=function(e) return("unknown"))
    }
''')


#make r functions global
r_f = robjects.globalenv['f']
getGender = robjects.globalenv['g']


# Query V1 data for authors of top titles 


count = func.count(Citation.text_id)

authors = (session
          .query(Text.authors)
          .join(Citation)
          .filter(Text.valid==True)
          .filter(Text.display==True)
          .group_by(Text.id)
          .order_by(count.desc())
          .limit(300))



# Create dataFrames to store author/gender data into, this can later be converted to csv file if necessary

header = ['first', 'last', 'gender', 'proportion']
df = pd.DataFrame(columns=header)

df_lt90 = pd.DataFrame(columns=header)


# Function that further formats the names with odd formats (names in parenthases, multiple names in first name string)

def format_name(name):
    
    #if alternate name in parenthases, take that name
    if "(" in name:
        temp = name.replace(")", "").split("(")
        name = temp[1]
    
    if " " in name:
        temp = name.split(" ")
        name = temp[0]
    
    
    return name
    


# Format name, find gender, add to table

x = 0
for a in authors.all():
    
    #format entry 
    entry = str(a)
    split_entry = entry.replace(".'],)", "").replace("(['", "").replace("'],)", "").split(", ")
    
    #separate first and last name
    if len(split_entry)== 1:
        first = split_entry[0]
        test_name = first.replace("'", "")
        last = ""
    else:
        first = split_entry[1]
        last = split_entry[0]
        test_name = format_name(first).replace("'", "")
           
    
    #get gender 
    g = getGenders(test_name)
    gender = g[0][0]
    p = g[0][1]
    
    #input data into temporary dataframe 
    df1 = pd.DataFrame({'first': first, 'last': last, 'gender': gender, 'proportion': p}, index = [x])
    
    #add to necessary tables 
    #frames = [df, df1]
    #df = pd.concat(frames)
    
    #add to correct proportion table
    if float(p) >= .90:
        frames = [df, df1]
        df = pd.concat(frames)
    else:
        name = test_name + " " + last
        gender = getGender(name)[0]
        if gender == "unknown":
            name = first + " " + last
            gender = getGender(name)[0]
        df1 = pd.DataFrame({'first': first, 'last': last, 'gender': gender, 'proportion': p}, index = [x])
        frames2 = [df_lt90, df1]
        df_lt90 = pd.concat(frames2)
        
    
    x += 1
    


#export data to csv
df.to_csv('top300_above90.csv')
df_lt90.to_csv('top300_below90.csv')

