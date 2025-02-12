import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller

# Install and configure ChromeDriver
chromedriver_autoinstaller.install()
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Load Excel file
excel_file_path = "Nawsher.xlsx"  # Ensure this file is in the same directory or provide full path
data = pd.read_excel(excel_file_path, dtype=str)  # Force all columns to be read as strings
total_links = len(data)  # Total product links

# Shopify login details
shopify_url = "https://cnsvmp-9z.myshopify.com/admin"
username = "hello@mototitans.com"
password = "DPuJus1LU%"

# Initialize error log file
error_file = "error.txt"
with open(error_file, "w") as f:
    f.write("")

# Login to Shopify
def login_to_shopify():
    driver.get(shopify_url)
    time.sleep(3)

    # Enter the email and click submit
    email_field = driver.find_element(By.ID, "account_email")
    email_field.send_keys(username)

    # Wait for the submit button and click it
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    ).click()
    time.sleep(5)

    # Enter the password and click submit
    password_field = driver.find_element(By.ID, "account_password")
    password_field.send_keys(password)

    # Handle overlays or loaders if present
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element((By.CSS_SELECTOR, "div[data-bind-show='!showShopLoader']"))
    )

    # Scroll into view and click submit
    submit_button = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
    submit_button.click()
    time.sleep(5)

# Function to convert line breaks from Excel to HTML
def format_description(text):
    """Convert Excel line breaks into proper HTML formatting."""
    return text.replace("\n", "<br>")

# Update product details
def update_product_details():
    for index, row in data.iterrows():
        product_url = row['URL']
        new_title = str(row['Title']).strip()
        new_description = str(row['Description']).strip()

        # Preserve formatting from Excel (convert \n to <br>)
        formatted_description = format_description(new_description)

        try:
            # Visit product URL
            driver.get(product_url)
            time.sleep(3)

            # Update the title field
            title_field = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "title"))  # Adjust with the correct selector
            )
            title_field.click()
            title_field.send_keys(Keys.CONTROL + "a")  # Select all content
            title_field.send_keys(Keys.DELETE)  # Clear the existing content
            title_field.send_keys(new_title)  # Enter new title

            # Switch to the iframe containing the description field
            iframe = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "product-description_ifr"))
            )
            driver.switch_to.frame(iframe)

            # Interact with the contenteditable element
            description_body = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body#tinymce"))
            )
            description_body.click()

            # Clear the existing content using JavaScript
            driver.execute_script("arguments[0].innerHTML = '';", description_body)

            # Set new content using JavaScript with proper formatting
            driver.execute_script("arguments[0].innerHTML = arguments[1];", description_body, formatted_description)

            # Switch back to the main page content
            driver.switch_to.default_content()

            # Click on the dropdown and select "Active"
            dropdown = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.NAME, "status"))
            )
            select = Select(dropdown)
            select.select_by_value("ACTIVE")  # Selects "Active" option
            time.sleep(1)
            # Try to find and click the save button
            try:
                save_button = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
                save_button.click()
                time.sleep(3)  # Short sleep after saving
            except Exception as save_exception:
                # Log the problematic URL to the error file
                with open(error_file, "a") as f:
                    f.write(f"{product_url}\n")

        except Exception as e:
            # Log the problematic URL to the error file
            with open(error_file, "a") as f:
                f.write(f"{product_url}\n")

        # Print remaining links count
        remaining_links = total_links - (index + 1)
        print(f"Remaining links: {remaining_links}")

# Main script execution
try:
    login_to_shopify()
    update_product_details()
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()
