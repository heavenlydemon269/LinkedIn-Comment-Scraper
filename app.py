import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Optimized function for Streamlit Cloud
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # This part is crucial for Streamlit Cloud to find the binary
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )

st.title("LinkedIn Comment Scraper")
post_url = st.text_input("Enter LinkedIn Post URL:")

if st.button("Scrape Comments"):
    with st.spinner("Initialising headless browser..."):
        driver = get_driver()
        try:
            driver.get(post_url)
            # Add your scraping logic here (as shared in previous turn)
            st.success("Page loaded successfully!")
            st.write(driver.title)
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            driver.quit()
