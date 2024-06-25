import asyncio
import csv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError

# Asynchronus Function that wait for usdot information (Take the page, wait for USDOT INFORMATION if USDOT INFORMATION is being selected within the timeout it will return True, if not it will returm False).
async def wait_for_usdot_information_table(page, timeout=500):
    try:
        await page.wait_for_selector("//td[contains(text(), 'USDOT INFORMATION')]/ancestor::table[1]", timeout=timeout)
        return True
    except TimeoutError:
        return False


async def Apply(page, csv_file, output_csv, processed_csv, inactive_csv):
    #The processed usdot number added to set, that ensures that each usdot number is unique.
    processed_usdot_numbers = set()

    # Read the processed CSV file if it exists
    try:
        with open(processed_csv, 'r') as processed_file:
            reader = csv.reader(processed_file)
            for row in reader:
                processed_usdot_numbers.add(row[0])
    except FileNotFoundError:
        pass

    # Open csv_file [determined in main function] as read mode, open output_csv and processed_csv as append mode.
    with open(csv_file, 'r', newline='', encoding='utf-8') as file, \
         open(output_csv, 'a', newline='', encoding='utf-8') as output_file, \
         open(processed_csv, 'a', newline='', encoding='utf-8') as processed_file, \
         open(inactive_csv, 'a', newline='', encoding='utf-8') as inactive_file:
        
        #The csv_reader reads the Input file.
        csv_reader = csv.DictReader(file)
        #Adding fieldnames if the output csv is empty.
        fieldnames = ['USDOT Number', 'MCS-150 Form Date', 'MCS-150 Mileage (Year)', 'Operating Authority Status', 'Power Units', 'Phone', 'Mailing Address', 'Physical Address', 'Prefix', 'Docket Number', 'Legal Name', 'DBA Name', 'City', 'State']
        #The writer write the fieldnames if there not already written.
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        #Initializes processed writer to write to processed file.
        processed_writer = csv.writer(processed_file)
        #Initializes inactive writer to write to processed file.
        inactive_writer = csv.writer(inactive_file)

        #If there's no header in output_file this statement will write the header.
        if output_file.tell() == 0:
            writer.writeheader()

        #Loop for each row in Input file
        for row in csv_reader:
            #Take the usdot_number from the input file
            usdot_number = row['usdot_number']
            # Check if USDOT number exists and is not processed.
            if usdot_number and usdot_number not in processed_usdot_numbers:  
                # Fill the usdot number and press submit
                # Await page.fill('input[id="4"]', usdot_number)
                # Await page.click('input[type="SUBMIT"]')
                if usdot_number and usdot_number not in processed_usdot_numbers:
                    await page.fill('input[id="4"]', usdot_number)
                    try:
                        await page.click('input[type="SUBMIT"]', timeout=60000)  # Increased timeout
                    except TimeoutError:
                        print(f"Timeout occurred while clicking on SUBMIT button for USDOT number {usdot_number}. Skipping to the next USDOT number.")
                        await asyncio.sleep(5)  # Add a delay of 5 seconds before navigating back
                        await page.go_back()
                        continue
                                                   
                # Wait for the USDOT information table to appear
                is_table_found = await wait_for_usdot_information_table(page, timeout=500)
                if is_table_found:
                    # Selecting the table using its XPath
                    table_xpath = "//td[contains(text(), 'USDOT INFORMATION')]/ancestor::table[1]"
                    # Take the html of the table
                    table_html = await page.inner_html(table_xpath)
                    
                    # Parse the HTML content
                    soup = BeautifulSoup(table_html, 'html.parser')

                    # Extract additional information from the CSV file
                    prefix = row['prefix']
                    docket_number = row['docket_number']
                    legal_name = row['legal_name']
                    dba_name = row['dba_name']
                    city = row['city']
                    state = row['state']

                    # Extract From the parsed html

                    # Extract MCS-150 Form Date
                    mcs_150_form_date = soup.find('th', text='MCS-150 Form Date:').find_next_sibling('td').get_text(strip=True)
                    # Extract MCS-150 Mileage
                    mcs_150_mileage = soup.find('th', text='MCS-150 Mileage (Year):').find_next_sibling('td').get_text(strip=True)
                    # Extract Operating Authority Status
                    operating_authority_status = soup.find('th', text='Operating Authority Status:').find_next_sibling('td').get_text(strip=True)
                    # Extract Power Units
                    power_units = soup.find('th', text='Power Units:').find_next_sibling('td').get_text(strip=True)
                    # Extract Phone
                    phone = soup.find('th', text='Phone:').find_next_sibling('td').get_text(strip=True)
                    # Extract Mailing Address
                    mailing_address = soup.find('th', text='Mailing Address:').find_next_sibling('td').get_text(strip=True)
                    # Extract Physical Address
                    physical_address = soup.find('th', text='Physical Address:').find_next_sibling('td').get_text(strip=True)

                    # Write the extracted information to the CSV file
                    writer.writerow({
                        'USDOT Number': usdot_number,
                        'MCS-150 Form Date': mcs_150_form_date,
                        'MCS-150 Mileage (Year)': mcs_150_mileage,
                        'Operating Authority Status': operating_authority_status,
                        'Power Units': power_units,
                        'Phone': phone,
                        'Mailing Address': mailing_address,
                        'Physical Address': physical_address,
                        'Prefix': prefix,
                        'Docket Number': docket_number,
                        'Legal Name': legal_name,
                        'DBA Name': dba_name,
                        'City': city,
                        'State': state

                    })

                    # Write the processed USDOT number to the processed CSV file
                    processed_writer.writerow([usdot_number])
                    print(f"USDOT number {usdot_number} information table is found within the timeout.")

                else:
                    # Write inactive USDOT numbers to the inactive CSV file
                    inactive_writer.writerow([usdot_number])
                    print(f"USDOT number {usdot_number} information table not found within the timeout.")
                    await asyncio.sleep(2)
                    await page.go_back()
                    

async def main():
    # Path to the CSV file containing data
    csv_file = 'Carriers.csv'
    # Path to the output CSV file
    output_csv = 'output.csv'
    # Path to the processed CSV file
    processed_csv = 'processed.csv'
    # Path to the inactive CSV file
    inactive_csv = 'inactive.csv'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        # Navigate to the Firefox web extension store
        await page.goto("https://addons.mozilla.org/en-US/firefox/")
        
        # Search for the VPN extension
        await page.fill('#AutoSearchInput-q', 'free vpn')
        await page.click('button[type="submit"]')

        # Wait for the search results to load
        await page.wait_for_selector('#react-view > div > div > div > div.Search > div > section > div > ul > li:nth-child(2)')

        # Click on the first search result (assuming it's the desired VPN extension)
        await page.click('#react-view > div > div > div > div.Search > div > section > div > ul > li:nth-child(2)')

        # Wait for the VPN extension page to load
        await page.wait_for_selector('css=.AMInstallButton-button')

        # Click on the install button to add the extension
        await page.click('css=.AMInstallButton-button')


        # Print a message indicating that the extension is installed
        print("VPN extension installed successfully.")
        # Wait for the installation to complete
        await asyncio.sleep(15)

        await page.goto("https://safer.fmcsa.dot.gov/CompanySnapshot.aspx")
        
        # Fill form with CSV data and write extracted information to output CSV file
        await Apply(page, csv_file, output_csv, processed_csv, inactive_csv)

        # Take a screenshot for verification
        await page.screenshot(path="end.png")     
        await browser.close()

asyncio.run(main())