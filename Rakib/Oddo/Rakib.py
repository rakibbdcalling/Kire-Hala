import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time

# Setup
custom_path = os.path.join(os.getcwd(), "chromedriver")  # Save in the script directory
os.makedirs(custom_path, exist_ok=True)

chromedriver_autoinstaller.install(path=custom_path)

# Load data
data = pd.read_excel("data.xlsx", dtype={'incoming_date': str, 'delivery_last_date': str})

# Start WebDriver
driver = webdriver.Chrome()
driver.get("https://www.bdcallingit.com/web/login")
driver.find_element(By.ID, "login").send_keys("rakib.bdcalling@gmail.com")
driver.find_element(By.ID, "password").send_keys("smtechnology")
driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()
time.sleep(1)

wait = WebDriverWait(driver, 5)  # Wait up to 5 seconds for elements

# Log file
with open("log_results.txt", "a") as log_file:
    for _, row in data.iterrows():
        driver.get("https://www.bdcallingit.com/portal/sales/create")
        
        # Fill form fields
        driver.find_element(By.ID, "sales_employee_id").send_keys(str(row["sales_employee_id"]))
        driver.find_element(By.ID, "platform_source").send_keys(str(row["platform_source"]))
        driver.find_element(By.NAME, "order_source_id").send_keys(row["order_source_id"])
        driver.find_element(By.ID, "profile_name").send_keys(row["profile_name"])
        
        driver.find_element(By.ID, "tags").click()
        driver.find_element(By.XPATH, f'//*[@data-value="{row["tags"]}"]').click()
        driver.find_element(By.ID, "tags").click()
        
        driver.find_element(By.ID, "btn_add_new_client").click()
        driver.find_element(By.ID, "a_client_user_name").send_keys(row["client_user_id"])
        driver.find_element(By.ID, "a_country_id").send_keys("United States")
        driver.find_element(By.ID, "btn_create_new_client").click()
        
        driver.find_element(By.CSS_SELECTOR, ".btn.btn-danger").click()
        time.sleep(1)
        
        driver.find_element(By.ID, "client_user_id").clear()
        driver.find_element(By.ID, "client_user_id").send_keys(row["client_user_id"])
        
        # Handle order number uniqueness check
        order_number = row["order_number"]
        driver.find_element(By.NAME, "order_number").send_keys(order_number)
        
        try:
            # Wait for the error message to appear (or timeout)
            error_element = wait.until(EC.visibility_of_element_located((By.ID, "order_number_error")))
            if "Already Exists" in error_element.text:
                order_number += "_1"
                driver.find_element(By.NAME, "order_number").clear()
                driver.find_element(By.NAME, "order_number").send_keys(order_number)
                
                # Wait again to see if error still appears
                time.sleep(2)
                error_element = driver.find_element(By.ID, "order_number_error")
                if "Already Exists" in error_element.text:
                    order_number = row["order_number"] + "_2"
                    driver.find_element(By.NAME, "order_number").clear()
                    driver.find_element(By.NAME, "order_number").send_keys(order_number)
        except:
            pass  # No error message, continue
        
        driver.find_element(By.ID, "order_link").send_keys(row["order_link"])
        driver.find_element(By.NAME, "instruction_sheet_link").send_keys(row["instruction_sheet_link"])
        driver.find_element(By.ID, "service_type_id").send_keys(row["service_type_id"])

        # Convert dates to strings
        incoming_date = f"{int(row['incoming_date']):08d}"
        delivery_last_date = f"{int(row['delivery_last_date']):08d}"

        # Input dates
        driver.find_element(By.NAME, "incoming_date").send_keys(incoming_date)
        driver.find_element(By.NAME, "delivery_last_date").send_keys(delivery_last_date, Keys.TAB, "1111p")

        # Fill in the other fields
        driver.find_element(By.ID, "amount").clear()
        driver.find_element(By.ID, "amount").send_keys(str(row["amount"]))
        driver.find_element(By.ID, "percentage").send_keys(str(row["percentage"]))
        driver.find_element(By.CSS_SELECTOR, ".button.button-primary.px-5.py-2").click()
        time.sleep(1)

        if driver.current_url != "https://www.bdcallingit.com/portal/sales/create/status":
            log_message = f"{order_number} incomplete\n"
            log_file.write(log_message)

driver.quit()
