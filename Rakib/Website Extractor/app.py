import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
import pandas as pd
import os
import time

# Setup ChromeDriver
custom_path = os.path.join(os.getcwd(), "chromedriver")
os.makedirs(custom_path, exist_ok=True)
chromedriver_autoinstaller.install(path=custom_path)

# Load data
data = pd.read_excel("data.xlsx", dtype={'incoming_date': str, 'delivery_last_date': str})
total_rows = len(data)

# Start WebDriver
driver = webdriver.Chrome()
driver.get("https://www.bdcallingit.com/web/login")

# Login
driver.find_element(By.ID, "login").send_keys("officesmtsales@gmail.com")
driver.find_element(By.ID, "password").send_keys("smtechnology")
driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()
time.sleep(2)

wait = WebDriverWait(driver, 5)

# Function to handle unexpected alerts
def handle_alert():
    try:
        alert = driver.switch_to.alert
        print("Alert detected:", alert.text)
        alert.dismiss()
    except NoAlertPresentException:
        pass  

# Log file setup
with open("log_results.txt", "a") as log_file:
    remaining_rows = total_rows  # Initialize remaining rows count

    for index, row in data.iterrows():
        print(f"Remaining: {remaining_rows}")

        driver.get("https://www.bdcallingit.com/portal/sales/create")
        
        # Ensure sales_employee_id is not empty
        sales_employee_id = str(row.get("sales_employee_id", "")).strip()
        if not sales_employee_id:
            log_file.write(f"{row['order_number']} - Missing Sales Employee ID\n")
            remaining_rows -= 1  # Update remaining count
            print(f"Remaining rows after processing: {remaining_rows}")
            continue  

        # Fill form fields
        driver.find_element(By.ID, "sales_employee_id").send_keys(sales_employee_id)
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

        order_number = row["order_number"]
        driver.find_element(By.NAME, "order_number").send_keys(order_number)

        try:
            error_element = wait.until(EC.visibility_of_element_located((By.ID, "order_number_error")))
            if "Already Exists" in error_element.text:
                order_number += "_1"
                driver.find_element(By.NAME, "order_number").clear()
                driver.find_element(By.NAME, "order_number").send_keys(order_number)
                time.sleep(2)
                error_element = driver.find_element(By.ID, "order_number_error")
                if "Already Exists" in error_element.text:
                    order_number = row["order_number"] + "_2"
                    driver.find_element(By.NAME, "order_number").clear()
                    driver.find_element(By.NAME, "order_number").send_keys(order_number)
        except:
            pass  

        driver.find_element(By.ID, "order_link").send_keys(row["order_link"])
        driver.find_element(By.NAME, "instruction_sheet_link").send_keys(row["instruction_sheet_link"])
        driver.find_element(By.ID, "service_type_id").send_keys(row["service_type_id"])

        try:
            incoming_date = f"{int(row['incoming_date']):08d}"
            delivery_last_date = f"{int(row['delivery_last_date']):08d}"
        except ValueError:
            log_file.write(f"{order_number} - Invalid date format\n")
            remaining_rows -= 1  
            print(f"Remaining rows after processing: {remaining_rows}")
            continue  

        driver.find_element(By.NAME, "incoming_date").send_keys(incoming_date)
        driver.find_element(By.NAME, "delivery_last_date").send_keys(delivery_last_date, Keys.TAB, "1111p")

        driver.find_element(By.ID, "amount").clear()
        driver.find_element(By.ID, "amount").send_keys(str(row["amount"]))
        driver.find_element(By.ID, "percentage").send_keys(str(row["percentage"]))

        driver.find_element(By.CSS_SELECTOR, ".button.button-primary.px-5.py-2").click()
        time.sleep(1)

        handle_alert()

        try:
            wait.until(EC.url_contains("/portal/sales/create/status"))
        except:
            log_file.write(f"{order_number} - Submission failed\n")

        remaining_rows -= 1  # Update remaining count after successful row processing
        print(f"Remaining rows after processing: {remaining_rows}")

driver.quit()
print("Processing completed for all rows.")
