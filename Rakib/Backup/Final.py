import chromedriver_autoinstaller
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time

# =========================
# CHROME DRIVER SETUP
# =========================
custom_path = os.path.join(os.getcwd(), "chromedriver")
os.makedirs(custom_path, exist_ok=True)
chromedriver_autoinstaller.install(path=custom_path)

# =========================
# LOAD DATA
# =========================
data = pd.read_excel("data.xlsx", dtype={
    'incoming_date': str,
    'delivery_last_date': str
})
total_rows = len(data)

# =========================
# START DRIVER
# =========================
driver = webdriver.Chrome()
driver.maximize_window()
driver.get("https://erp.betopiagroup.com/web/login")

# =========================
# LOGIN
# =========================
driver.find_element(By.NAME, "login").send_keys("smtechnology@gmail.com")
driver.find_element(By.NAME, "password").send_keys("betopia2025")

WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign In')]"))
).click()

wait = WebDriverWait(driver, 15)

# =========================
# LOG FILE
# =========================
with open("log_results.txt", "a", encoding="utf-8") as log_file:
    remaining_rows = total_rows

    for index, row in data.iterrows():
        print(f"Remaining: {remaining_rows}")

        driver.get("https://erp.betopiagroup.com/odoo/orders/new")

        # =========================
        # WAIT FOR ODOO FULL LOAD
        # =========================
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body.o_web_client")))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".o_form_view, .o_list_view")))
        time.sleep(2)

        # =========================
        # BASIC FIELDS
        # =========================
        driver.find_element(By.ID, "platform_source_id_0").send_keys(str(row["Platform Source"]))
        driver.find_element(By.ID, "platform_source_id_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "profile_id_0").send_keys(str(row["Profile Name"]))
        driver.find_element(By.ID, "profile_id_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "order_source_id_0").send_keys(str(row["Order Source"]))
        driver.find_element(By.ID, "order_source_id_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "order_number_0").send_keys(str(row["Order Number"]))
        driver.find_element(By.ID, "order_number_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "order_link_0").send_keys(str(row["Order Link"]))
        driver.find_element(By.ID, "order_link_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "instruction_sheet_link_0").send_keys(str(row["Instruction Sheet Link"]))
        driver.find_element(By.ID, "instruction_sheet_link_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "delivery_last_date_0").send_keys(str(row["Delivery Last Date"]))
        driver.find_element(By.ID, "delivery_last_date_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "crm_tag_id_0").send_keys(str(row["CRM Tag"]))
        driver.find_element(By.ID, "crm_tag_id_0").send_keys(Keys.ENTER)

        driver.find_element(By.ID, "service_line_0").send_keys(str(row["Service Line"]))
        driver.find_element(By.ID, "service_line_0").send_keys(Keys.ENTER)

        # =========================
        # ADD SERVICE
        # =========================
        add_service = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//td[contains(@class,'o_field_x2many_list_row_add')]//a[normalize-space()='Add a Service']"
            ))
        )
        add_service.click()

        search_box = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search a product']"))
        )
        search_box.click()
        search_box.clear()
        search_box.send_keys(str(row["Search a Product"]))
        driver.switch_to.active_element.send_keys(Keys.TAB * 1)
        time.sleep(1)

        qty_field = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//td[@name='product_uom_qty']//input"))
        )
        qty_field.click()

        # Move to price field via TAB (Odoo-friendly way)
        qty_field.send_keys(Keys.TAB)
        time.sleep(0.5)

        # Now active element SHOULD be price field
        price_field = driver.switch_to.active_element
        price_field.clear()
        price_field.send_keys(str(row["Price"]))


        # =========================
        # CUSTOMER
        # =========================
        customer = wait.until(
            EC.element_to_be_clickable((By.ID, "partner_id_0"))
        )
        customer.send_keys(str(row["Customer"]))
        customer.send_keys(Keys.ENTER)
        time.sleep(1)
        # =========================
        # SAVE
        # =========================
        save_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'o_form_button_save')]"))
        )
        save_btn.click()

        time.sleep(4)

        # =========================
        # LOGGING
        # =========================
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
