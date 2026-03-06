import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Path where 'chromium' and 'chromium-driver' are installed on Streamlit Cloud
    service = Service("/usr/bin/chromedriver") 
    options.binary_location = "/usr/bin/chromium"
    
    return webdriver.Chrome(service=service, options=options)
