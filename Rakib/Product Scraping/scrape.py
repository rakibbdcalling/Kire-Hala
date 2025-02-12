import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# Install and configure ChromeDriver
chromedriver_autoinstaller.install()
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Load Excel file with URLs
excel_file_path = "urls.xlsx"  # Ensure this file is in the same directory or provide full path
data = pd.read_excel(excel_file_path, dtype=str)  # Force all columns to be read as strings

# Shopify login details
shopify_url = "https://cnsvmp-9z.myshopify.com/admin"
username = "hello@mototitans.com"
password = "DPuJus1LU%"

# Initialize extracted data
extracted_data = []
output_file_path = "extracted.xlsx"  # Output file path
error_file_path = "error.txt"  # Error file path

# Clear any existing content in the error file
with open(error_file_path, "w") as f:
    f.write("")

# Login to Shopify
def login_to_shopify():
    driver.get(shopify_url)
    time.sleep(3)

    #print("Logging into Shopify...")
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
   # print("Successfully logged into Shopify!")
    time.sleep(5)

# Extract product description
def extract_product_details():
    total_links = len(data)
    for index, row in data.iterrows():
        product_url = row['URL']

        #print(f"Processing product: {product_url}")
        try:
            # Visit product URL
            driver.get(product_url)
            time.sleep(3)

            # Switch to the iframe containing the description field
            iframe = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "product-description_ifr"))
            )
            driver.switch_to.frame(iframe)

            # Extract the product description
            description_body = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body#tinymce"))
            )
            product_description = description_body.text  # Extract the text content
            #print(f"Description extracted: {product_description}")

            # Switch back to the main page content
            driver.switch_to.default_content()

            # Append the data to the list
            extracted_data.append({
                "URL": product_url,
                "Description": product_description
            })

        except Exception as e:
            print(f"Error with product: {product_url} - {e}")
            extracted_data.append({
                "URL": product_url,
                "Description": "Error"
            })

        # Save data and handle errors
        if not save_to_excel():
            # Log the problematic URL to the error file
            with open(error_file_path, "a") as f:
                f.write(f"{product_url}\n")

        remaining_links = total_links - (index + 1)
        print(f"Links remaining: {remaining_links}")

# Save extracted data to a new Excel file
def save_to_excel():
    try:
        df = pd.DataFrame(extracted_data)
        df.to_excel(output_file_path, index=False)
        return True
    except Exception as e:
        #print(f"Error saving data to Excel: {e}")
        return False

# Main script execution
try:
    login_to_shopify()
    extract_product_details()
    print("Product details extraction completed!")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()
