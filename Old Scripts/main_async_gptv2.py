import asyncio
import csv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError

# Asynchronous function that waits for USDOT information
async def wait_for_usdot_information_table(page, timeout=500):
    try:
        await page.wait_for_selector("//td[contains(text(), 'USDOT INFORMATION')]/ancestor::table[1]", timeout=timeout)
        return True
    except TimeoutError:
        return False

async def Apply(page, csv_file, output_csv, processed_csv, inactive_csv):
    # Processed USDOT numbers added to a set to ensure uniqueness
    processed_usdot_numbers = set()

    # Read the processed CSV file if it exists
    try:
        with open(processed_csv, 'r') as processed_file:
            reader = csv.reader(processed_file)
            for row in reader:
                processed_usdot_numbers.add(row[0])
    except FileNotFoundError:
        pass

    # Open CSV files
    with open(csv_file, 'r', newline='', encoding='utf-8') as file, \
         open(output_csv, 'a', newline='', encoding='utf-8') as output_file, \
         open(processed_csv, 'a', newline='', encoding='utf-8') as processed_file, \
         open(inactive_csv, 'a', newline='', encoding='utf-8') as inactive_file:

        # CSV readers and writers
        csv_reader = csv.DictReader(file)
        output_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        processed_writer = csv.writer(processed_file)
        inactive_writer = csv.writer(inactive_file)

        # Write header if output file is empty
        if output_file.tell() == 0:
            output_writer.writeheader()

        # Loop through each row in input file
        for row in csv_reader:
            usdot_number = row['usdot_number']

            # Check if USDOT number exists and is not processed
            if usdot_number and usdot_number not in processed_usdot_numbers:
                await page.fill('input[id="4"]', usdot_number)
                try:
                    await page.click('input[type="SUBMIT"]', timeout=60000)  # Increased timeout
                except TimeoutError:
                    print(f"Timeout occurred while clicking on SUBMIT button for USDOT number {usdot_number}. Skipping to the next USDOT number.")
                    await asyncio.sleep(5)  # Add a delay of 5 seconds before navigating back
                    await page.go_back()
                    continue

                is_table_found = await wait_for_usdot_information_table(page, timeout=500)
                if is_table_found:
                    # Process active USDOT numbers
                    # Your existing code for processing active USDOT numbers

                    # Write the processed USDOT number to the processed CSV file
                    processed_writer.writerow([usdot_number])
                else:
                    # Write inactive USDOT numbers to the inactive CSV file
                    inactive_writer.writerow([usdot_number])

                await asyncio.sleep(1)  # Add a delay before navigating back
                await page.go_back()

async def main():
    # Paths to CSV files
    csv_file = 'Carriers.csv'
    output_csv = 'output.csv'
    processed_csv = 'processed.csv'
    inactive_csv = 'inactive.csv'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://safer.fmcsa.dot.gov/CompanySnapshot.aspx")

        await Apply(page, csv_file, output_csv, processed_csv, inactive_csv)

        # Take a screenshot for verification
        await page.screenshot(path="end.png")
        await browser.close()

asyncio.run(main())
