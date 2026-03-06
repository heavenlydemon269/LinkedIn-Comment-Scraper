import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def get_driver():
    options = Options()
    # "headless=new" is the modern way to run Chrome without a GUI
    options.add_argument("--headless=new") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Bypassing common bot detection flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    # Path for Streamlit Cloud (ensure packages.txt has chromium & chromium-driver)
    service = Service("/usr/bin/chromedriver") 
    options.binary_location = "/usr/bin/chromium"
    
    driver = webdriver.Chrome(service=service, options=options)
    
    # Masking the navigator.webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

st.set_page_config(page_title="LinkedIn Scraper", page_icon="🌐")
st.title("LinkedIn Comment Scraper")

post_url = st.text_input("Enter LinkedIn Post URL:")

# Ensure your .streamlit/secrets.toml has: LI_AT_COOKIE = "your_value"
if "LI_AT_COOKIE" not in st.secrets:
    st.error("Missing LI_AT_COOKIE in Streamlit Secrets!")
    st.stop()

li_at_cookie = st.secrets["LI_AT_COOKIE"]

if st.button("Scrape Comments"):
    if not post_url:
        st.warning("Please enter a URL first!")
    else:
        with st.spinner("Initializing browser and authenticating..."):
            driver = get_driver()
            try:
                # 1. Visit LinkedIn to set the domain context
                driver.get("https://www.linkedin.com")
                time.sleep(2)
                
                # 2. Inject the Session Cookie
                driver.add_cookie({
                    "name": "li_at",
                    "value": li_at_cookie,
                    "domain": ".www.linkedin.com"
                })
                
                # 3. Navigate to the Post
                driver.get(post_url)
                st.info(f"Navigating to post...")
                time.sleep(7) # Increased wait for JS rendering

                # 4. Scroll to trigger lazy-loaded comments
                # driver.execute_script("window.scrollTo(0, 800);")
                # time.sleep(3)

                # 4. Deep Scroll & Wait
                st.info("Hydrating comment section...")
                driver.execute_script("window.scrollTo(0, 1200);")
                time.sleep(5) # Give it plenty of time to load the dynamic content

                # 5. Extraction Logic (The '2026 Resilient' Version)
                # We search for several potential patterns that LinkedIn uses
                comment_elements = []
                
                # Priority 1: Modern data-test attributes
                # Priority 2: Generic article tags within the comments list
                # Priority 3: The standard class names
                search_queries = [
                    "//article[contains(@class, 'comment')]",
                    "//div[@data-test-id='comment-item']",
                    "//*[contains(@class, 'comments-comment-item')]"
                ]

                for query in search_queries:
                    elements = driver.find_elements(By.XPATH, query)
                    if elements:
                        comment_elements = elements
                        st.write(f"Match found using: {query}")
                        break
                
                comments_list = []
                for el in comment_elements:
                    try:
                        # Using relative XPaths to find name and text inside each comment
                        # This is much safer than fixed class names
                        author = el.find_element(By.XPATH, ".//span[contains(@class, 'name-text')] | .//span[contains(@class, 'actor__name')]").text.strip()
                        text = el.find_element(By.XPATH, ".//*[contains(@class, 'main-content')] | .//*[contains(@class, 'text-body')]").text.strip()
                        
                        if author and text:
                            comments_list.append({"Author": author, "Comment": text})
                    except:
                        continue

                # 6. Results
                if comments_list:
                    df = pd.DataFrame(comments_list)
                    st.success(f"Successfully scraped {len(df)} comments!")
                    st.dataframe(df, use_container_width=True)
                    
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="linkedin_comments.csv",
                        mime="text/csv",
                    )
                else:
                    # Debugging view: Show what the bot sees if it fails
                    driver.save_screenshot("debug.png")
                    st.image("debug.png", caption="Bot's Current View (Debug Screenshot)")
                    st.error("No comments found. Check the screenshot above to see if a login/captcha appeared.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                driver.quit()
