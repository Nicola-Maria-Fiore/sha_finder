import os
import pandas as pd
from bs4 import BeautifulSoup
import re

source = "dirs/"
provisions = "provisions.csv"
results = "pacts/"
months = {"gennaio":"01", "febbraio":"02", "marzo":"03", "aprile":"04", "maggio":"05", "giugno":"06",
         "luglio":"07", "agosto":"08", "settembre":"09", "ottobre":"10", "novembre":"11", "dicembre":"12"}
months_n = ["01","02","03","04","05","06","07","08","09","10","11","12"]
provisions_separator = ","
csv = "results.csv"

date_nf = 1

def getSaveDir(folder, fname):
    dir_ = os.path.join(folder, fname)
    base_name = fname
    n = 1
    while os.path.exists(dir_):
       n += 1
       base_name = base_name.replace("_sha.html","")
       fname = base_name+"_("+str(n)+")_sha.html"
       dir_ = os.path.join(folder, fname)
    
    return fname

def getPacts(html):
    start_index = 0
    min_words = 50
    pacts = []

    soup = BeautifulSoup(html, "html.parser")
    content = str(soup)
    for el in re.finditer(r"\[(.*)\.(.*)\.(.*)\.(.*)\]",content):
        pos =  el.span()
        pact = content[start_index:pos[1]]
        if len(pact.split(" "))>=min_words:
            pacts.append(pact)
        start_index = pos[1]+1

    return pacts

def getDate(pact): 
    global date_nf
    global months
    global months_n

    date = ""
    soup = BeautifulSoup(pact, "html.parser")
    content = soup.text.replace("\xa0"," ")
    content_s = soup.text.replace("\xa0"," ")
    content = content.split("\n")
    i = len(content)-1
    found = False
    while i>=0 and found==False:
        content[i] = content[i].replace("  "," ")

        content_temp = content[i].strip()
        if len(content_temp)>2 and content_temp[len(content_temp)-1]==".":
            content[i] = content_temp[:len(content_temp)-1]

        first_comma = content[i].find(",")
        if first_comma>=0:
            content[i] = (content[i])[first_comma+1:]
            
        temp = content[i].replace(".","/").replace("°","").strip().split(" ")
        if len(temp)==3 and temp[1].lower() in months:
            temp[1] = months[temp[1].lower()]
            day = temp[0]
            if len(day)==1:
                day = "0"+day
            temp[0] =  temp[2]
            temp[2] = day
            if len(temp[1])==1:
                temp[1] = "0"+temp[1]
            date = "/".join(temp)
            found = True
        elif len(temp)==1 and len(temp[0].split("/"))==3:
            temp = temp[0].split("/")
            day = temp[0]
            temp[0] =  temp[2]
            temp[2] = day
            if len(temp[1])==1:
                temp[1] = "0"+temp[1]
            date = "/".join(temp)
            found = True
        i -= 1

    if found:
        check_month = date.split("/")
        if len(check_month)<2 or check_month[1] not in months_n or (not check_month[0].isdigit() or not check_month[1].isdigit() or not check_month[2].isdigit()): 
            found = False
            date = ""
    
    if found==False:
        print("Date not found: "+str(date_nf))
        date_nf += 1

    return date

def parseFolder(folder):
    pacts_res = []
    pact_num = 0
    os.mkdir(os.path.join(results,folder)) 
    out_path = os.path.join(results,folder)
    path = os.path.join(source,folder)
    for file in os.listdir(path):
        file_path = os.path.join(path,file)
        with open(file_path, "r", encoding='utf-8') as f:
            pacts = getPacts(f.read())
        for p in pacts:
            date = getDate(p)
            pact_name = folder + "_isin_" + date.replace("/","_") + "_sha.html"
            pact_name = getSaveDir(out_path, pact_name)
            pact_dir = os.path.join(out_path,pact_name)
            pact_num += 1 
            with open(pact_dir, "w", encoding='utf-8') as f:
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
        df[w[0]] = 0

    for index, row in df.iterrows():
        company = row["Company"]
        for column in df:
            if "Date" in column and str(row[column])!="nan":
                fname = company + "_isin_" + str(row[column]).replace("/","_") + "_sha.html"
                fpath = results+company+"/"+fname
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding='utf-8') as f:
                        content = f.read().lower()
                    for provision in words:
                        for w in provision[1:]:
                            if w.lower() in content:
                                df.loc[index,provision[0]] = 1
                
    return df


if __name__ == "__main__":
    pacts_list = []
    clauses = []

    with open(provisions, 'r', encoding='utf-8') as file_in:
        for line in file_in:
            clauses.append(line.strip().replace('\n',"").split(provisions_separator))
    
    for _, dirs, _ in os.walk(source):
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
    df = find_words(df, clauses)
    df = df.replace({"---/--/---": '.'}, regex=True)
    df = df.replace({"---": '.'}, regex=True)
    df.to_csv(csv)
    
    print("Done!")
