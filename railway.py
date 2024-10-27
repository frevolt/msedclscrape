# Required Libraries
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

# Initialize Flask app
app = Flask(__name__)

# Define the scraping function as an endpoint
@app.route('/get_consumer_data', methods=['POST'])
def get_consumer_data():
    consumer_number = request.json.get('consumer_number')  # Receive data as JSON

    # Start WebDriver (headless mode recommended for servers)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://wss.mahadiscom.in/wss/wss?uiActionName=getViewPayBill")

        # Input consumer number
        consumer_number_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "inp_field"))
        )
        consumer_number_field.send_keys(consumer_number)

        # Extract captcha and submit form (simplified here)
        captcha_scripts = driver.find_elements(By.TAG_NAME, "script")
        captcha_code = None
        for script in captcha_scripts:
            match = re.search(r"createCaptcha\('(\w+)'\);", script.get_attribute("innerHTML"))
            if match:
                captcha_code = match.group(1)
                break

        if not captcha_code:
            return jsonify({"error": "Captcha code not found!"}), 500

        captcha_field = driver.find_element(By.ID, "txtInput")
        captcha_field.send_keys(captcha_code)
        driver.find_element(By.ID, "lblSubmit").click()

        # Wait for data to load and extract
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "datagrid_container")))
        view_bill_img = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "img[title='View Bill']"))
        )
        view_bill_img.click()

        consumer_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "consumerName"))
        ).text
        consumer_address = driver.find_element(By.ID, "consumerAddress").text
        village = driver.find_element(By.ID, "village").text if driver.find_elements(By.ID, "village") else ""
        tariff = driver.find_element(By.ID, "tariff").text
        category = driver.find_element(By.ID, "category").text
        BillUnit = driver.find_element(By.ID, "billingUnit").text
        SubD = driver.find_element(By.ID, "Bu1").text
        Load = driver.find_element(By.ID, "sanctionLoad").text

        full_address = f"{consumer_address}, {village}"
        BillingUnit = f"{BillUnit},{SubD}"
        Tariff = f"{tariff},{category}"

        # Compile results
        extracted_data = {
            "name": consumer_name,
            "address": full_address,
            "tariff": Tariff,
            "BUnit": BillingUnit,
            "load": Load
        }

        return jsonify(extracted_data)  # Return JSON response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
