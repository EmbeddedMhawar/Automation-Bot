import asyncio
import csv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def Apply(page, csv_file, output_csv):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file, open(output_csv, 'w', newline='', encoding='utf-8') as output_file:
        csv_reader = csv.DictReader(file)
        fieldnames = ['USDOT Number', 'MCS-150 Form Date', 'MCS-150 Mileage', 'Operating Authority Status', 'Power Units', 'Phone', 'Mailing Address', 'Physical Address']
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()

        for row in csv_reader:
            usdot_number = row['usdot_number']
            if usdot_number:  # Check if USDOT number exists
                # Find the input field by CSS selector and fill it with the USDOT number from the CSV
                await page.fill('input[id="4"]', usdot_number)
                # You may need to adjust the selector according to your HTML structure
                await page.click('input[type="SUBMIT"]')

                # Check if the page indicates that the record is inactive
                if await page.inner_text('font[color="#0000C0"]') == 'INACTIVE':
                    print(f"USDOT Number {usdot_number} is INACTIVE")
                    await page.reload()  # Reload the page
                    continue  # Skip to the next USDOT number

                # Selecting the table using its XPath
                table_xpath = "//td[contains(text(), 'USDOT INFORMATION')]/ancestor::table[1]"
                table_html = await page.inner_html(table_xpath)
                
                # Parse the HTML content
                soup = BeautifulSoup(table_html, 'html.parser')

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
                    'MCS-150 Mileage': mcs_150_mileage,
                    'Operating Authority Status': operating_authority_status,
                    'Power Units': power_units,
                    'Phone': phone,
                    'Mailing Address': mailing_address,
                    'Physical Address': physical_address
                })

async def main():
    # Path to the CSV file containing data
    csv_file = 'Carriers.csv'
    # Path to the output CSV file
    output_csv = 'output.csv'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://safer.fmcsa.dot.gov/CompanySnapshot.aspx")

        # You can perform other actions here, such as filling forms, clicking buttons, etc.
        print(await page.title())
        
        # Fill form with CSV data and write extracted information to output CSV file
        await Apply(page, csv_file, output_csv)

        # Take a screenshot for verification
        await page.screenshot(path="pic.png")     
        await browser.close()

asyncio.run(main())
