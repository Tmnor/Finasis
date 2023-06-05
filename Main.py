# -*- coding: utf-8 -*-
import sys
import json
import requests
import logging
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Company:
    def __init__(self, name, orgnumber, valuecode, financials=[], balancesheet=[], cash_flow=[]):
        self.name = name
        self.orgnumber = orgnumber
        self.valuecode = valuecode
        self.financials = financials
        self.balancesheet = balancesheet
        self.cash_flow = cash_flow


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

    driver = webdriver.Chrome()

    # Navigate to financials/balance sheet page
    fin_balance_link = proffSoup.find('a', class_='addax addax-cs_ip_keyfigures_click ss-dropdown')
    driver.get(fin_balance_link['href'])

    # Check if switchAccounting is present and click corporate link if so
    try:
        switchAccounting = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'switchAccounting')))
        corporate_link = switchAccounting.find_element_by_link_text('corporate')
        corporate_link.click()

        # Fetch financials and balance sheets from specific tables
        financials = parse_table(driver, 7)
        balancesheet = parse_table(driver, 8)
    except:
        # If switchAccounting was not present, fetch from different tables
        financials = parse_table(driver, 3)
        balancesheet = parse_table(driver, 4)

    # Navigate to cash flow page
    cash_flow_link = proffSoup.find('a', class_='addax addax-cs_ip_analysis_click ss-dropdown')
    driver.get(cash_flow_link['href'])

    # Check if switchAccounting is present and click corporate link if so
    try:
        switchAccounting = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'switchAccounting')))
        corporate_link = switchAccounting.find_element_by_link_text('corporate')
        corporate_link.click()

        # Fetch cash flow from specific table
        cash_flow = parse_table(driver, 4)
    except:
        # If switchAccounting was not present, fetch from different table
        cash_flow = parse_table(driver, 2)

    driver.quit()

    company = Company(name, orgNumber, financials, balancesheet, cash_flow)
    return company


def parse_table(driver, table_index):
    # Wait for the presence of tables in the page
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))

    # Get all tables in the page
    tables = driver.find_elements_by_tag_name('table')

    # If the table index is out of range, return an empty list
    if table_index >= len(tables):
        print(f'Error: table index {table_index} out of range. Only found {len(tables)} tables.')
        return []

    # Get the rows in the table
    rows = tables[table_index].find_elements_by_tag_name('tr')

    data = []

    # Get the header row and extract the years
    header = rows[0].find_elements_by_tag_name('th')
    years = [cell.find_element_by_tag_name('span').text for cell in header[1:]] # Skip the first cell (it's not a year)
    data.append(years)

    # Iterate over the remaining rows
    for row in rows[1:]:
        # Get the cells in the row
        cells = row.find_elements_by_tag_name('td')

        row_data = []
        # Iterate over the cells
        for cell in cells:
            # Append the cell text to the row_data list
            row_data.append(cell.text)
        # Append the row_data to the data list
        data.append(row_data)

    return data


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


def format_output(companies):
    output = {"companies": []}

    for company in companies:
        company_data = {
            "name": company.name,
            "orgnumber": company.orgnumber,
            "valuecode": company.valuecode,
            "financials": company.financials,
            "balancesheet": company.balancesheet,
            "cash_flow": company.cash_flow,
        }
        output["companies"].append(company_data)

    return output

if __name__ == '__main__':
    logging.basicConfig(filename='scraper.log', level=logging.ERROR)
    companies = main()
    output = format_output(companies)
    print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False))
