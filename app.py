import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import pandas as pd

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

st.title("LinkedIn Comment Scraper")
post_url = st.text_input("Enter LinkedIn Post URL:")



if st.button("Scrape Comments"):
    if not post_url:
        st.warning("Please enter a URL first!")
    else:
        with st.spinner("Extracting comments..."):
            driver = get_driver()
            try:
                driver.get(post_url)
                # Give the page a moment to render JavaScript
                time.sleep(5) 

                # 1. Logic to find the comment items
                # LinkedIn often uses 'comments-comment-item' or specific data attributes
                comment_elements = driver.find_elements(By.CSS_SELECTOR, ".comments-comment-item")
                
                comments_list = []
                
                for el in comment_elements:
                    try:
                        # Extract Author
                        author = el.find_element(By.CSS_SELECTOR, ".comments-post-meta__name-text").text.strip()
                        # Extract Comment Text
                        text = el.find_element(By.CSS_SELECTOR, ".comments-comment-item__main-content").text.strip()
                        
                        comments_list.append({"Author": author, "Comment": text})
                    except:
                        continue # Skip if an element is missing (like a deleted comment)

                # 2. Display Results
                if comments_list:
                    df = pd.DataFrame(comments_list)
                    st.success(f"Found {len(df)} comments!")
                    st.dataframe(df, use_container_width=True)
                    
                    # 3. Download Button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download comments as CSV",
                        data=csv,
                        file_name="linkedin_comments.csv",
                        mime="text/csv",
                    )
                else:
                    st.error("No comments found. The post might be private or require a login.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                driver.quit()
