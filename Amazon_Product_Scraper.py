from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    #chrome_options.add_argument('--headless=new')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'normal'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 1, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(3000)

    return driver


def scrape_Amazon(path):

    start = time.time()
    print('-'*75)
    print('Scraping Amazon.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()
    months = list(calendar.month_name[1:])

    # for running the scraper through parallel batches
    if path != '':
        df_links = pd.read_excel(path)
        name = path.split('\\')[-1][:-4]
        name =  'Amazon_data'+ path[-7:-5] + '.xlsx'
    else:
        df_links = pd.read_excel('Amazon_links.xlsx')
        name = 'Amazon_data.xlsx'

    # scraping resuming feature
    scraped = []
    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping titles Info...')
    print('-'*75)

    links = df_links['Paperback_url'].values.tolist()
    n = len(links)
    for i, link in enumerate(links):

        try:
            if link in scraped: continue
            driver.get(link.replace("?psc=1", ''))           
            details = {}
            print(f'Scraping the info for title {i+1}\{n}')

            # selecting the Paperpack or Hardcover formats if applicable
            try:
                try:
                    text = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//span[@class='a-button a-button-selected a-spacing-mini a-button-toggle format']"))).get_attribute('textContent').replace('\n', '')
                except:
                    text = ''
                if 'Paperback' not in text or 'Mass Market' in text:
                    lis = wait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[class*='swatchElement unselected']")))
                    paper = False
                    url = ''
                    for li in lis:
                        a = wait(li, 4).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        text = a.get_attribute('textContent').replace('\n', '')        
                        if 'Paperback' in text and 'Mass Market' not in text:
                            url = a.get_attribute('href')
                            driver.get(url)
                            paper = True
                            break                        
                        elif 'Paperback' in text and 'Mass Market' in text:
                            url = a.get_attribute('href')
                            driver.get(url)
                            paper = True
                        elif 'Hardcover' in text:
                            url = a.get_attribute('href')

                    if not paper and url != '':
                        driver.get(url)
            except:
                pass

            # scrolling across the page 
            try:
                htmlelement= wait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
                total_height = driver.execute_script("return document.body.scrollHeight")
                height = total_height/30
                new_height = 0
                for _ in range(30):
                    prev_hight = new_height
                    new_height += height             
                    driver.execute_script(f"window.scrollTo({prev_hight}, {new_height})")
                    time.sleep(0.1)
            except:
                pass
                
            # title and title link
            title_link, title = '', ''              
            try:
                title_link = link
                title = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//span[@id='productTitle']"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                print(f'Warning: failed to scrape the title for book: {link}')                             
            details['Title'] = title
            details['Title Link'] = title_link    
            
            # Author and author link
            author, author_link = '', ''
            try:
                spans = wait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.author")))
                if len(spans) > 1:
                    spans = spans[:-1]
                nauthor = 0
                for span in spans:
                    try:
                        a = wait(span, 4).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        author += a.get_attribute('textContent').replace('\n', '').strip().title() + ', '
                        nauthor += 1
                        if nauthor < 5:
                            author_link += a.get_attribute('href') + ', '
                    except:
                        pass
                author = author[:-2]
                author_link = author_link[:-2]
            except:
                try:
                    divs = wait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='a-column a-span4 _follow-the-author-card_style_authorNameColumn__1YFry']")))
                    nauthor = 0
                    for div in divs:
                        a = wait(div, 4).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        author += a.get_attribute('textContent').replace('\n', '').strip().title() + ', '
                        nauthor += 1
                        if nauthor < 5:
                            author_link += a.get_attribute('href') + ', '

                    author = author[:-2]
                    author_link = author_link[:-2]
                except:
                    pass
                    
            details['Author'] = author            
            details['Author Link'] = author_link            

            # other info
            try:
                try:
                    # all formats except audio
                    tag = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//div[@id='detailBulletsWrapper_feature_div']")))
                    lis = wait(tag, 4).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                    for li in lis:
                        try:
                            text = li.get_attribute('textContent').replace('\u200e', '').replace('\n', '').replace('\u200f', '')
                            if ':' not in text: continue
                            elif 'ASIN' in text:
                                details['ASIN'] = text.split(':')[-1].strip()
                            elif 'Publisher' in text:
                                details['Publisher'] = text.split(':')[-1].strip().split('(')[0].strip()
                                if '(' in text:
                                    details['Publication date'] = text.split(':')[-1].strip().split('(')[-1].strip()[:-1]
                            elif 'Language' in text and 'Language' not in details:
                                details['Language'] = text.split(':')[-1].strip()
                            elif 'File size' in text:
                                details['File size'] = text.split(':')[-1].strip()        
                                details['Format'] = 'Kindle'
                            elif 'Paperback' in text or 'Hardcover' in text:
                                details['Format'] = text.split(':')[0].strip()
                                details['# Pages'] = text.split(':')[-1].split()[0]
                            elif 'ISBN-10' in text:
                                details['ISBN-10'] = text.split(':')[-1].strip()                            
                            elif 'ISBN-13' in text:
                                details['ISBN-13'] = text.split(':')[-1].strip()
                            elif 'Reading age' in text:
                                details['Reading Age'] = text.split(':')[-1].split()[0]                            
                            elif 'Lexile measure' in text:
                                details['Lexile'] = text.split(':')[-1].strip()                            
                            elif 'Item Weight' in text:
                                details['Weight'] = text.split(':')[-1].strip()                            
                            elif 'Dimensions' in text:
                                details['Dimensions'] = text.split(':')[-1].strip()                              
                            elif 'Publication date' in text:
                                details['Publication date'] = text.split(':')[-1].strip()                            
                            elif 'Best Sellers Rank' in text:
                                details['Best Sellers Rank'] = text.split(':')[-1].strip().split('(')[0].replace('#', '').replace(',', '').strip()
                        except:
                            pass

                        if 'Publication date' not in details:
                            try:
                                text = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//span[@id='productSubtitle']"))).get_attribute('textContent')
                                for month in months:
                                    if month in text:
                                        details['Publication date'] = text.split('�')[-1].strip()
                                        break
                            except:
                                pass


                except:
                    # audio books
                    tag = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//table[@class='a-keyvalue a-vertical-stripes a-span6']")))
                    trs = wait(tag, 4).until(EC.presence_of_all_elements_located((By.TAG_NAME, "tr")))
                    for tr in trs:
                        th = wait(tr, 4).until(EC.presence_of_element_located((By.TAG_NAME, "th"))).get_attribute('textContent')
                        td = wait(tr, 4).until(EC.presence_of_element_located((By.TAG_NAME, "td"))).get_attribute('textContent').strip()
                        try:
                            if 'Listening Length' in th:
                                details['Listening Length'] = td
                            elif 'Release Date' in th:
                                details['Publication date'] = td 
                            elif 'Publisher' in th:
                                details['Publisher'] = td 
                            elif 'Type' in th:
                                details['Format'] = td   
                            elif 'Version' in th:
                                details['Version'] = td   
                            elif 'Language' in th:
                                details['Language'] = td 
                            elif 'ASIN' in th:
                                details['ASIN'] = td 
                            elif 'Best Sellers Rank' in th:
                                details['Best Sellers Rank'] = td.split('(')[0].replace('#', '').replace(',', '').strip()
                        except:
                            pass
                    try:
                        # reading age
                        text = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//div[@class='a-section cr-childrens-books']"))).get_attribute('textContent')
                        age = int(re.findall("\d+", text)[0]) 
                        details['Reading Age'] = age
                    except:
                        pass
            except:
                pass

            # average rating
            rating = ''
            try:
                rating = wait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrPopover']"))).get_attribute('title').split()[0]
            except:
                pass

            details['Average Rating'] = rating

            # number of ratings
            nratings = ''
            try:
                 nratings = wait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[id='acrCustomerReviewText']"))).get_attribute('textContent').split()[0].replace(',', '')
            except:
                pass

            details['# Ratings'] = nratings

            # rating per star
            stars = ["5 star", "4 star", "3 star", "2 star", "1 star"]
            try:
                tds = wait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td[class*='a-text-right a-nowrap']")))
                if len(tds) == 5:
                    for k, td in enumerate(tds):
                        per = td.get_attribute('textContent').strip()
                        details[stars[k]] = per
            except:
                pass

            # price
            price = ''            
            try:
                try:
                    text = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//span[@class='a-button a-button-selected a-spacing-mini a-button-toggle format']"))).get_attribute('textContent').replace('\n', '').strip() 
                except:
                    text = wait(driver, 4).until(EC.presence_of_element_located((By.XPATH, "//span[@class='a-button a-spacing-mini a-button-toggle format']"))).get_attribute('textContent').replace('\n', '').strip() 
                price = float(re.findall("[0-9]+[.][0-9]+", text)[0])
            except:
                pass                             
            details['Price'] = price   
            
            try:
                if 'Format' not in details:
                    details['Format'] = text.split('$')[0].replace('from', '').replace('�', '').replace('\n', '').strip()
            except:
                pass

            # reviews link
            rev_link = ''
            try:
                rev_link = wait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']"))).get_attribute('href')
            except:
                pass

            details['Reviews Link'] = rev_link

            # badge
            try:
                tag = wait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='badge-link']")))
                badge = tag.get_attribute('textContent').replace('\n', '').strip()
                value = wait(tag, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[class='cat-name']"))).get_attribute('textContent').replace('\n', '').strip()
                badge = badge.replace(value, '')
                if 'Best Seller' not in badge:
                    details[badge] = value
            except:
                pass

            # number of reviews
            nrevs = ''
            try:
                driver.get(rev_link)
                text = wait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id='filter-info-section']"))).get_attribute('textContent')
                nrevs = text.split()[3].replace(',', '')
            except:
                pass

            details['# Reviews'] = nrevs

            # appending the output to the datafame        
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                writer = pd.ExcelWriter(name, engine_kwargs={'options':{'strings_to_urls': False}})
                data.to_excel(writer, index=False)
                writer.close()
        except:
            pass

    # optional output to excel
    writer = pd.ExcelWriter(name, engine_kwargs={'options':{'strings_to_urls': False}})
    data.to_excel(writer, index=False)
    writer.close()
    elapsed = round((time.time() - start)/60, 4)
    print('-'*75)
    print(f'Amazon.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":

    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_Amazon(path)
