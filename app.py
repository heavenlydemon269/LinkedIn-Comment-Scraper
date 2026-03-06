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

                # 4. The "Deep Scroll" Maneuver
                st.info("Scrolling to locate comments...")
                # Scroll down in increments to mimic a human reading
                for i in range(3):
                    driver.execute_script(f"window.scrollTo(0, {500 + (i*500)});")
                    time.sleep(2)

                # 5. Extraction Logic (Updated Selectors for 2026)
                # We target the specific 'comment-item' class used in the modern feed
                selectors = [
                    ".comments-comment-item", 
                    "article.comments-comment-item",
                    "div[data-test-id='comment-item']"
                ]
                
                comment_elements = []
                for selector in selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 0:
                        comment_elements = elements
                        break
                
                # Check for "Load more comments" button if only a few are found
                try:
                    load_more = driver.find_element(By.CSS_SELECTOR, "button.comments-comments-list__load-more-comments-button")
                    if load_more:
                        driver.execute_script("arguments[0].click();", load_more)
                        time.sleep(3)
                        # Re-scan for elements after loading more
                        comment_elements = driver.find_elements(By.CSS_SELECTOR, selectors[0])
                except:
                    pass # No "load more" button found
                # 5. Extraction Logic
                # Using a list of selectors in case LinkedIn updates their UI
                selectors = [".comments-comment-item", "article.comments-comment-item", ".main-content-card"]
                comment_elements = []
                
                for selector in selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        comment_elements = elements
                        break
                
                comments_list = []
                for el in comment_elements:
                    try:
                        author = el.find_element(By.CSS_SELECTOR, ".comments-post-meta__name-text").text.strip()
                        text = el.find_element(By.CSS_SELECTOR, ".comments-comment-item__main-content").text.strip()
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
