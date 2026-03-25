import chromedriver_autoinstaller
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import os
import time
import pyautogui
import keyboard


# Setup ChromeDriver
custom_path = os.path.join(os.getcwd(), "chromedriver")
os.makedirs(custom_path, exist_ok=True)
chromedriver_autoinstaller.install(path=custom_path)

# Load data
data = pd.read_excel("data.xlsx", dtype={'incoming_date': str, 'delivery_last_date': str})
total_rows = len(data)

# Start WebDriver
driver = webdriver.Chrome()
driver.maximize_window()
driver.get("https://erp.betopiagroup.com/web/login")

# Login
driver.find_element(By.NAME, "login").send_keys("smtechnology@gmail.com")
driver.find_element(By.NAME, "password").send_keys("betopia2025")
button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In')]"))
)

button.click()
wait = WebDriverWait(driver, 5)

# Log file setup
with open("log_results.txt", "a") as log_file:
    remaining_rows = total_rows

    for index, row in data.iterrows():
        print(f"Remaining: {remaining_rows}")

        driver.get("https://erp.betopiagroup.com/odoo/orders/new")
        time.sleep(2)

        # Platform Source
        driver.find_element(By.ID, "platform_source_id_0").send_keys(str(row["Platform Source"]))
        driver.find_element(By.ID, "platform_source_id_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Profile Name
        driver.find_element(By.ID, "profile_id_0").send_keys(str(row["Profile Name"]))
        driver.find_element(By.ID, "profile_id_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Order Source
        driver.find_element(By.ID, "order_source_id_0").send_keys(str(row["Order Source"]))
        driver.find_element(By.ID, "order_source_id_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Order Number
        driver.find_element(By.ID, "order_number_0").send_keys(str(row["Order Number"]))
        driver.find_element(By.ID, "order_number_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Order Link
        driver.find_element(By.ID, "order_link_0").send_keys(str(row["Order Link"]))
        driver.find_element(By.ID, "order_link_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Instruction Sheet Link
        driver.find_element(By.ID, "instruction_sheet_link_0").send_keys(str(row["Instruction Sheet Link"]))
        driver.find_element(By.ID, "instruction_sheet_link_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Delivery Last Date
        driver.find_element(By.ID, "delivery_last_date_0").send_keys(str(row["Delivery Last Date"]))
        driver.find_element(By.ID, "delivery_last_date_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # CRM Tag
        driver.find_element(By.ID, "crm_tag_id_0").send_keys(str(row["CRM Tag"]))
        driver.find_element(By.ID, "crm_tag_id_0").send_keys(Keys.ENTER)

        # Service Line
        driver.find_element(By.ID, "service_line_0").send_keys(str(row["Service Line"]))
        driver.find_element(By.ID, "service_line_0").send_keys(Keys.ENTER)
        time.sleep(1)

        # Add a Service
        add_service = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//td[contains(@class,'o_field_x2many_list_row_add')]//a[normalize-space()='Add a Service']"
            ))
        )
        add_service.click()

        search_box = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//input[@placeholder='Search a product']"
            ))
        )

        search_box.click()
        search_box.clear()

        value = str(row["Search a Product"])
        search_box.send_keys(value)
        time.sleep(1)

        search_box.send_keys(Keys.TAB)
        search_box.send_keys(Keys.TAB)
        time.sleep(1)

        # Price
        price_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@inputmode='decimal' and contains(@class,'o_input')]"))
        )

        price_input.click()
        price_input.send_keys(Keys.CONTROL, "a")
        price_input.send_keys(Keys.BACKSPACE)

        price_value = str(row["Price"])
        price_input.send_keys(price_value)
        price_input.send_keys(Keys.TAB)

        # Discount
        discount_input = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//td[@name='discount']//input[contains(@class,'o_input')]"
            ))
        )

        discount_input.click()
        discount_input.send_keys(Keys.CONTROL, "a")
        discount_input.send_keys(Keys.BACKSPACE)
        discount_input.send_keys("20")
        time.sleep(1)

        # Customer
        driver.find_element(By.ID, "partner_id_0").send_keys(str(row["Customer"]))
        time.sleep(1)
        driver.find_element(By.ID, "partner_id_0").send_keys(Keys.ENTER)
        time.sleep(1)

        save_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(@class,'o_form_button_save')]"
            ))
        )

        save_btn.click()
        time.sleep(3)

        # ✅ UPDATED LOGIC
        current_url = driver.current_url

        if "/odoo/orders/new" in current_url:
            log_file.write(f"FAILED Order Number: {row['Order Number']}\n")

        elif "/odoo/orders/" in current_url:
            try:
                order_id = current_url.rstrip("/").split("/")[-1]

                if not order_id.isdigit():
                    log_file.write(f"INVALID ID | Order Number: {row['Order Number']}\n")
            except:
                log_file.write(f"ERROR PARSING | Order Number: {row['Order Number']}\n")

        else:
            log_file.write(f"UNKNOWN ERROR | Order Number: {row['Order Number']}\n")

        remaining_rows -= 1
        time.sleep(2)
