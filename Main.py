# -*- coding: utf-8 -*-
import sys
import json
import requests
import logging
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

class Company:
    def __init__(self, name, orgnumber, liquidity, profitability, solidity, revenue, operatingProfit, revenueBeforeTax, assets, equity, valuecode):
        self.name = name
        self.orgnumber = orgnumber
        self.profitability = profitability
        self.solidity = solidity
        self.liquidity = liquidity
        self.revenue = revenue
        self.operatingProfit = operatingProfit
        self.revenueBeforeTax = revenueBeforeTax
        self.assets = assets
        self.equity = equity
        self.valuecode = valuecode

def parse_arguments():
    parser = ArgumentParser(description='Grabs information located at Proff.no.')
    parser.add_argument('--company', help='Use --company and the name of the company. Company names with spaces need underscores _', required=True)
    args = parser.parse_args()
    complete_url = f"http://data.brreg.no/enhetsregisteret/enhet.json?$filter=startswith(navn,'{args.company}')"
    return complete_url

def get_content(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except RequestException as e:
        logging.error(f'An error occured fetching {url} \n {str(e)}')
        return None

    return resp.text

def create_company(name, orgNumber):
    getProffURL = f'http://www.proff.no/bransjesøk?q={str(orgNumber)}'
    content = get_content(getProffURL)
    if not content:
        return None

    linkSoup = BeautifulSoup(content, 'html.parser')

    y = linkSoup.find(class_='addax-cs_hl_hit_company_name_click')
    if y is None:
        return None

    proffURL = y.get('href').rsplit('/', 2)[-2]
    profflink = f'http://www.proff.no/selskap/afwfwaf/afwfafwf/asfjawgj/{proffURL}'

    content = get_content(profflink)
    if not content:
        return None

    proffSoup = BeautifulSoup(content, 'html.parser')

    table = proffSoup.find(class_='total-account-table ui-wide')
    if table is None:
        return None

    infoFromHeader = []
    topstatistics = proffSoup.find_all(class_='chart-value', limit=3)
    for i in topstatistics:
        span = i.span
        if span is not None:
            infoFromHeader.append(span.get_text().strip().replace("(","").replace(")",""))
        elif i.get_text() == "Kan ikke beregnes":
            infoFromHeader.append(0)

    table_data = parse_rows(table)

    if len(table_data) >= 5:
        company = Company(name, orgNumber, infoFromHeader[0], infoFromHeader[1], infoFromHeader[2], table_data[0], table_data[1], table_data[2], table_data[3], table_data[4], table_data[5])
        return company
    else:
        return None

def main():
    url = parse_arguments()
    companies = []

    content = get_content(url)
    if not content:
        return []

    x = json.loads(content)

    for index, company_data in enumerate(x["data"]):
        name = company_data["navn"]
        orgNo = company_data["organisasjonsnummer"]
        company = create_company(name, orgNo)
        if company is not None:
            companies.append(company)

    return companies

if __name__ == '__main__':
    logging.basicConfig(filename='scraper.log', level=logging.ERROR)
    companies = main()
    print(json.dumps([ob.__dict__ for ob in companies], sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
