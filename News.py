from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# Specify the path to your driver
driver_path = "/path/to/your/driver" 

# Create a new instance of the browser driver
driver = webdriver.Chrome(executable_path=driver_path)

# Go to the website
driver.get("https://newsweb.oslobors.no/")

try:
    # Wait for the input field to be present and click it to open the dropdown menu
    company_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-activedescendant="react-select-8--value"]'))
    )
    company_input.click()
    
    # Wait for the dropdown menu to be present and select the company
    company_option = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.Select-option[aria-label="2020 Bulkers Ltd."]'))
    )
    company_option.click()

    # Wait for the submit button to be clickable
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.sc-dnqmqq.jbWdyo'))
    )
    # Click the submit button
    submit_button.click()

    # Wait for the table to be loaded
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'a.sc-jnlKLf.gguAuF'))
    )

    # Add a pause
    time.sleep(2)

    # Now that the page is fully loaded, get the source HTML
    html = driver.page_source

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all links in the table
    links = soup.select('a.sc-jnlKLf.gguAuF')

    # Do something with the links...
    for link in links:
        # Go to the link
        driver.get(link['href'])

        # Add a pause
        time.sleep(2)

        # Get the source HTML of the new page
        html = driver.page_source

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract the date, header, and content
        date = soup.select_one('span.sc-dqBHgY.cUmcwC').text
        header = soup.select_one('h1.sc-kIPQKe.RdGFo').text
        content = soup.select_one('div.sc-esjQYD.garOWd').text

        # Print the information
        print(f"Company: {company_name}")
        print(f"Date: {date}")
        print(f"Header: {header}")
        print(f"Content: {content}")
        print("-----")
        
except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    # Quit the driver
    driver.quit()
