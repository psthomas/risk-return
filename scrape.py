import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import subprocess
import os
import random
import csv
import json
import time
import traceback

## If you want to scrape semi-anonymously, use these steps:
# https://stackoverflow.com/questions/1096379
# Using Tor:
# $ brew update
# $ brew install tor
# $ pip install -U requests requests[socks]
# Run tor:
# $ tor
# Then tell requests to use port 9050:

proxies = {
    'http': 'socks5://localhost:9050',
    'https': 'socks5://localhost:9050'
}

def get_page(url, tor=True):
    '''Returns a response object, filtered through tor network
    if tor=True'''
    if tor:
        response = requests.get(url, proxies=proxies)
    else:
        response = requests.get(url)
    return response 


def get_parsed_page(url, tor=True):
    '''Returns a soup object, filtered through tor network
    if tor=True'''
    if tor:
        response = requests.get(url, proxies=proxies)
    else:
        response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def get_wa_data():
    '''Scrapes and parses data at url, outputs results to
    data/wa_data.csv'''
    url = 'http://www.wsipp.wa.gov/BenefitCost'
    soup = get_parsed_page(url, tor=False)
    rows = soup.find_all('tr')
    results = []

    for row in rows:
        col = []
        for column in row.find_all("td"):
            col.append(column.get_text().strip())
        if len(col) == 9:
            results.append(col)

    labels = ['program_name', 'date_last_literature_review', 'total_benefits', 'taxpayer_benefits',
              'non-taxpayer_benefits', 'costs', 'benefits_minus_costs_NPV', 'benefit_cost_ratio',
              'chance_benefits_exceed_costs']

    df = pd.DataFrame.from_records(results, columns=labels)
    df = df[df['benefit_cost_ratio'] != 'n/a']
    df['program_name'].replace({'\r\n                \nUPDATED':'', '\r\n                \nNEW':''}, 
                               inplace=True, regex=True)
    #df.drop('empty', axis=1, inplace=True)
    df.replace({'[\$,)]': '', '[(]' : '-', ',': '', ' %': ''}, inplace=True, regex=True)
    df = df.apply(pd.to_numeric, errors='ignore')
    df['chance_costs_exceed_benefits'] = 100 - df['chance_benefits_exceed_costs']

    df.to_csv('./data/wa_data.csv', index=False)


def parse_soup(soup, base_result):
    '''Returns a list of papers and citations from a soup object'''
    rows = soup.find_all('tr', class_="gsc_a_tr")
    records = []
    for row in rows:
        temp = base_result.copy()
        title = row.find('td', class_="gsc_a_t").a.get_text(strip=True)
        citations = row.find('td', class_="gsc_a_c").get_text(strip=True)
        year = row.find('td', class_="gsc_a_y").get_text(strip=True)
        temp.update({'title': title, 'citations': citations, 'year': year})
        records.append(temp)
    return records

def generate_eco_links():
    '''Selects a sample of 150 researchers from the google ecology list:
    https://github.com/weecology/bibliometrics/blob/master/Google_ecology.csv'''
    eco_df = pd.read_csv('./data/google_ecology.csv')
    eco_df.reset_index(inplace=True)
    eco_df.rename(columns={'index': 'id', 'google': 'name'}, inplace=True)

    #Use anyone that's not a student, data was taken 5 years ago so postdocs should be established
    eco_df = eco_df[(eco_df['Rank'] != 'student') & (pd.isnull(eco_df['Rank']) != True)]

    #Maybe leave the ID off the eco_df and the sample, 
    #Look, people don't need to be able to re-create the entire analysis including data gathering.
    #Just include the anonymized data you scraped, include the entire google_ecology.csv dataset,
    #and .gitignore the eco_sample.csv?  That way they know you took a random sample, and how you did
    #it, and can take a random, but different sample if they really want to, 

    #Select a random sample of 150 researchers
    sample_df = eco_df.sample(150)
    print(sample_df['Rank'].value_counts())
    sample_df.to_csv('./data/eco_sample.csv', index=False)

def get_ecodata():
    '''Downloads multi-page profiles from 100 google scholars and parses 
    papers, citation counts, and years.  Outputs CSVs with body HTML 
    and parsed data.'''

    links_df = pd.read_csv('./data/eco_sample.csv')   
    links_list = links_df.values.tolist()
    #random.shuffle(links_list) #Not needed
    count = 0

    with open('./data/eco_pages.csv', "w") as page_file, open('./data/eco_citations.csv', "w") as record_file:
        csv.field_size_limit(500 * 1024 * 1024)
        writer = csv.writer(page_file, delimiter=',')
        writer.writerow(['id', 'name', 'url', 'body'])

        fieldnames = ['id', 'name', 'citations', 'year', 'title', 'url']
        dictwriter = csv.DictWriter(record_file, fieldnames=fieldnames)
        dictwriter.writeheader()

        while count < 100:
            try:
                researcher = links_list.pop()
                rid = researcher[0]
                name = researcher[1]
                base_url = researcher[2]
                start = 0
                url = base_url + '&cstart={0}&pagesize=100'.format(start)
                base_result = {'id':rid, 'name':name, 'url':url}
                response = get_page(url, tor=True)

                if response.status_code == 200 and 'There are no articles in this profile.' not in response.text:
                    print(response.status_code, name, url)
                    body = BeautifulSoup(response.content, 'html.parser').find('body')
                    writer.writerow([rid, name, url, body])  
                    count += 1 # Increment once per researcher
                    records = parse_soup(body, base_result)
                    dictwriter.writerows(records)

                    while 'There are no articles in this profile.' not in response.text:
                        time.sleep(1)
                        start += 100
                        url = base_url + '&cstart={0}&pagesize=100'.format(start)
                        response = get_page(url, tor=True)
                        print(response.status_code, name, url)

                        if 'There are no articles in this profile.' not in response.text:
                            body = BeautifulSoup(response.content, 'html.parser').find('body')
                            writer.writerow([rid, name, url, body])  
                            records = parse_soup(body, base_result)
                            dictwriter.writerows(records)
                else:
                    print("Error: ", response.status_code, name, url)
            except Exception as e:
                traceback.print_exc()


def generate_gwdata():
    '''Runs the monte carlo simulation from danwahl/stochastic-altruism 
    to generate samples for analysis. Source:  
    $ git clone https://github.com/danwahl/stochastic-altruism
    '''
    cwd = os.path.join(os.getcwd(), 'stochastic-altruism')

    #Runs synchronously
    subprocess.run(['python', 'gw_params.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd) 
    subprocess.run(['python', 'lead_params.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    subprocess.run(['python', 'gw_test.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    subprocess.run(['python', 'lead_test.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)

    gw_data = pd.read_pickle('./stochastic-altruism/gw_data.pickle')
    #ace_data = pd.read_pickle('ace_data.pickle') #Leave out for now
    lead_data = pd.read_pickle('./stochastic-altruism/lead_data.pickle')
    data = pd.concat([gw_data, lead_data], axis=1)
    data.to_csv('./data/gw_data.csv', index=False)




if __name__ == '__main__':
    # Uncomment as needed:
    #get_wa_data()
    #generate_eco_links()
    #get_ecodata()
    #generate_gwdata()



