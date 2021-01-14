import os
import pandas as pd
from bs4 import BeautifulSoup
import re

res = "dirs/"
months = {"gennaio":"01", "febbraio":"02", "marzo":"03", "aprile":"04", "maggio":"05", "giugno":"06",
         "luglio":"07", "agosto":"08", "settembre":"09", "ottobre":"10", "novembre":"11", "dicembre":"12"}

def getPacts(html):
    start_index = 0
    pacts = []

    soup = BeautifulSoup(html, "html.parser")
    #content = str(soup.text)
    content = str(soup)
    for el in re.finditer(r"\[(.*)\.(.*)\.(.*)\.(.*)\]",content):
        pos =  el.span()
        pacts.append(content[start_index:pos[1]])
        start_index = pos[1]+1

    return pacts

def getDate(pact): 
    date = ""
    soup = BeautifulSoup(pact, "html.parser")
    content = soup.text.replace("\xa0"," ")
    content = content.split("\n")
    i = len(content)-1
    found = False
    while i>=0 and found==False:
        temp = content[i].strip().split(" ")
        if len(temp)==3 and temp[1].lower() in months:
            temp[1] = months[temp[1].lower()]
            day = temp[0]
            if len(day)==1:
                day = "0"+day
            temp[0] =  temp[2]
            temp[2] = day
            date = "/".join(temp)

            found = True
        i -= 1

    return date

def parseFolder(folder):
    pacts_res = []
    pact_num = 0
    path = os.path.join(res,folder)
    for file in os.listdir(path):
        if "_isin_" in file:
            continue
        file_path = os.path.join(path,file)
        with open(file_path, "r") as f:
            pacts = getPacts(f.read())
        for p in pacts:
            date = getDate(p)
            pact_name = folder + "_isin_" + date.replace("/","_") + "_sha.html"
            pact_dir = os.path.join(path,pact_name)
            pact_num += 1 
            with open(pact_dir, "w") as f: #azienda1_isin_2010_10_11_sha
                f.write(p)

            pacts_res.append((p,date))
    return pacts_res


def addDates(pacts_list):
    df = pd.DataFrame()
    idx = 0
    for company in pacts_list:
        all_years = company[1]
        
        for year in all_years:
            df.loc[idx,"Company"] = company[0]
            df.loc[idx,"Year"] = year

            date_count = 1
            for y in all_years[year]:
                date = y[0]
                pact = y[1]
                df.loc[idx,"Date"+str(date_count)] = date
                date_count += 1

            idx += 1
    return df


def find_words(df,words):
    for w in words:
        df[w] = 0

    for index, row in df.iterrows():
        company = row["Company"]
        for column in df:
            if "Date" in column and str(row[column])!="nan":
                fname = company + "_isin_" + str(row[column]).replace("/","_") + "_sha.html"
                fpath = "dirs/"+company+"/"+fname
                with open(fpath, "r") as f:
                    content = f.read().lower()
                for w in words:
                    if w.lower() in content:
                        df.loc[index,w] = 1
                
    return df


if __name__ == "__main__":
    pacts_list = []

    for _, dirs, _ in os.walk(res):
        for d in dirs:
            years = {}
            pacts = parseFolder(d)
            for p in pacts:
                t = p[1]
                if len(t)==0:
                    t = "---/--/---"
                y = (t.split("/"))[0]
                if y not in years:
                    years[y] = []
                years[y].append((t,"p"))
            pacts_list.append((d,years))

    df = addDates(pacts_list)
    df = find_words(df, ["a","bwdsadwewadwq","c"])
    print(df)
    print("Done!")