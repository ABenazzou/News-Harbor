from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging    

@task(task_id="scrape_bbc_articles")
def scrape_bbc_articles(**kwargs):
    ACTIVE_MENU = None
    ACTIVE_SUBMENU = None
    
    def is_empty_s3_bucket():
        # to be stored in config.conf
        import boto3
        import configparser
        import os
        
        parser = configparser.ConfigParser()
        parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

        # AWS
        aws_access_key = parser.get('aws', 'aws_access_key')
        aws_secret_key = parser.get('aws', 'aws_secret_key')
        s3_bucket_name = parser.get('aws', 's3_bucket_name')

        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
        s3_bucket = s3_client.list_objects(Bucket=s3_bucket_name)
        return "Contents" not in s3_bucket


    def get_scrape_date(is_empty_s3_bucket):
        from datetime import date
        from dateutil.relativedelta import relativedelta

        if not is_empty_s3_bucket:
            return date.today().strftime("%Y-%m-%d")
        else:
            return (date.today() + relativedelta(months=-3)).strftime("%Y-%m-%d")


    def scrape_articles_from_main_ui(driver, root_tab, menu_tab, submenu_tab, scrape_date):
        total_pages = driver.find_element(By.CLASS_NAME, "qa-pagination-total-page-number")
        total_pages = int(total_pages.text)
        current_page = 1
        
        while True:
            logging.info("Scraping page: %s out of: %s", current_page, total_pages)
    
            # CLICK ALL PAGES AND CARDS BEFORE LEAVING TO NEXT PAGE
            page_result = gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date)
            
            #moving to next page if possible or historical limit met
            if current_page >= total_pages or not page_result:break
            
            next_button = driver.find_element(By.CLASS_NAME, "qa-pagination-next-page")
            next_button.click()
            
            next_page = driver.find_element(By.CLASS_NAME, "qa-pagination-current-page-number")
            current_page = int(next_page.text)
            

    def scrape_articles_from_secondary_ui(driver, root_tab, menu_tab, submenu_tab, scrape_date):
        total_pages = driver.find_elements(By.XPATH, '//nav[contains(@class, "ssrcss-1we4v4l-Pagination")]/div/div/div[contains(@class, "ssrcss-17k7p6q-SummaryContainer")]/div/b')
        first_match = int(total_pages[0].get_attribute("innerText"))
        second_match = int(total_pages[1].get_attribute("innerText"))
        if second_match > first_match:
            total_pages = second_match
        else:
            total_pages = first_match
        
        current_page = 1
        
        while True:
            logging.info("Scraping page: %s out of: %s", current_page, total_pages)
            
            page_result = gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date)
            
            if current_page >= total_pages or not page_result:break
            
            next_button = driver.find_elements(By.XPATH, '//nav[contains(@class, "ssrcss-1we4v4l-Pagination")]/div/div/div[contains(@class, "ssrcss-a11ok4-ArrowPageButtonContainer")]/div/a') # check if contents is next page
            for button in next_button:
                button_text = button.text
                if button_text == "next page":
                    next_button = button
                    break
            
            next_button.click()
            
            current_page = driver.find_elements(By.XPATH, '//nav[contains(@class, "ssrcss-1we4v4l-Pagination")]/div/div/div[contains(@class, "ssrcss-17k7p6q-SummaryContainer")]/div/b')
            
            first_match = int(current_page[0].get_attribute("innerText"))
            second_match = int(current_page[1].get_attribute("innerText"))
            if second_match <= first_match:
                current_page = second_match
            else:
                current_page = first_match
            


    def scrape_articles(driver, root_tab, menu_tab, submenu_tab, scrape_date):
        try:
            scrape_articles_from_main_ui(driver, root_tab, menu_tab, submenu_tab, scrape_date)
            
        except (NoSuchElementException):
            try:
                scrape_articles_from_secondary_ui(driver, root_tab, menu_tab, submenu_tab, scrape_date)
                
            except (NoSuchElementException, IndexError):
                #Scraping to be defined as no paging found so scraping without pressing next button
                page_result = gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date)
                # no need to break anything here as it is only a page and is already stopped
                logging.info("No Paging Scraping")
        

    def gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date):

        cards_XPATH = '//a[contains(@class, "gs-c-promo-heading")]' 
        latest_news_XPATH = '//div[@class="gs-o-media__body"]/h3/a' 
        
        cards_alternative_XPATH = '//div[contains(@class, "ssrcss-tq7xfh-PromoContent")]/div/a'
        latest_news_alternative_XPATH = '//ol[contains(@class, "ssrcss-jv9lse-Stack")]/li/div/div/div/div/a'

        cards = driver.find_elements(By.XPATH, cards_XPATH)
        latest_news = driver.find_elements(By.XPATH, latest_news_XPATH)
        page_news = cards + latest_news
        
        if not page_news:
            cards = driver.find_elements(By.XPATH, cards_alternative_XPATH)
            latest_news = driver.find_elements(By.XPATH, latest_news_alternative_XPATH)
            page_news = cards + latest_news
            
        latest_news = set(latest_news)
        cards = set(cards)

        try:
            for article in page_news:

                is_latest_news = article in latest_news
                uri = article.get_attribute('href')

                if uri in VISITED_ARTICLES: continue
                
                if not ('/news/' in uri) or '/live/' in uri or '/resources/' in uri: continue # we want only articles aka /news
                
                ActionChains(driver).move_to_element(article).key_down(Keys.CONTROL).click(article).key_up(Keys.CONTROL).perform()

                tabs = driver.window_handles
                
                for article_tab in tabs:
                    if (article_tab != root_tab and article_tab != menu_tab and article_tab != submenu_tab):break
                    
                driver.switch_to.window(article_tab)
                logging.info("Switched to article tab")
                import time
                time.sleep(1)
                # give 1 second to have the tab open with all necessary scrape info
                
                is_valid_article = scrape_article(driver, menu_tab, submenu_tab, uri, is_latest_news, scrape_date)

                if (is_valid_article or is_valid_article == None):
                    VISITED_ARTICLES.add(uri)

                else:
                    driver.close()
                    logging.info("Closed article tab")
                    # return False no need to scrape further
                    driver.switch_to.window(submenu_tab if submenu_tab else menu_tab)
                    logging.info("Switched to secondary if secondary else primary")

                    logging.info("Stopping scraping of category due to historical limit")
                    return False

                driver.close()
                logging.info("Closed article tab")
                driver.switch_to.window(submenu_tab if submenu_tab else menu_tab)
                logging.info("Switched to secondary if secondary else primary")

            return True # finished scraping page and no old elemnent in latest news
        except (StaleElementReferenceException, NoSuchElementException):
            # refresh and retry
            driver.refresh()
            return gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date)
        except (ElementNotInteractableException):

            driver.execute_script("arguments[0].click();", article)
            is_valid_article = scrape_article(driver, menu_tab, submenu_tab, uri, is_latest_news, scrape_date)

            if (is_valid_article or is_valid_article == None):
                VISITED_ARTICLES.add(uri)
            else:
                # return False no need to scrape further
                # driver.close() # DO NOT CLOSE AS WE ARE ON THE SAME TAB
                logging.info("Stopping scraping of category due to historical limit")

                driver.back()
                return False

            driver.back()
            driver.refresh()
            return gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date)


    def scrape_article(driver, menu, submenu, uri, is_latest_news, scrape_date): 
        nonlocal ACTIVE_MENU
        nonlocal ACTIVE_SUBMENU
        nonlocal SCRAPPED_DATA
        
        try:
            date_posted = get_date_posted(driver)
            if date_posted < scrape_date:
                # article posted before our tolerance
                if is_latest_news:
                    return False
                else:
                    return None
                
            title = get_title(driver)
            subtitle = get_subtitle(driver)
            full_text = get_full_text(driver)
            topics = get_topics(driver)
            images = get_images(driver)
            authors = get_authors(driver)
            # video = get_video(driver)
            scraped_object = {
                "id": uri,
                "title": title,
                "subtitle": subtitle,
                "date_posted": date_posted,
                "full_text": full_text,
                "topics": topics,
                "images": images,
                "authors": authors,
                # "video": video,
                "menu": ACTIVE_MENU,
                "submenu": ACTIVE_SUBMENU
            }   

            SCRAPPED_DATA.append(scraped_object)
            return True

        except WebDriverException:
            driver.refresh()
            return scrape_article(driver, menu, submenu, uri, is_latest_news, scrape_date)
        

    def get_title(driver):
        title_XPATH = '//h1[@id="main-heading"]'
        title = driver.find_element(By.XPATH, title_XPATH)
        return title.text if title else None


    def get_subtitle(driver):
        try:
            subtitle_XPATH = '//b[contains(@class, "ssrcss-hmf8ql-BoldText")]' # if exists
            subtitle = driver.find_element(By.XPATH, subtitle_XPATH)
            return subtitle.text
        except NoSuchElementException:
            return None


    def get_date_posted(driver):
        import dateparser
        
        try:
            date_posted_XPATH = '//time' #convert to datetime
            date_posted = driver.find_element(By.XPATH, date_posted_XPATH)
            if date_posted:
                try:
                    timestamp = dateparser.parse(date_posted.text, settings={'RELATIVE_BASE': datetime.now()}).timestamp()
                except AttributeError:
                    timestamp = dateparser.parse(date_posted.get_attribute("datetime")).timestamp()

                datetime_object = datetime.fromtimestamp(timestamp)
                return datetime_object.strftime('%Y-%m-%d')
        except NoSuchElementException:
            driver.refresh()
            import time
            time.sleep(1)
            get_date_posted(driver) # Date is always there
            # return None


    def get_full_text(driver):
        text_XPATH = '//div[@data-component="text-block"]'
        
        full_text = driver.find_elements(By.XPATH, text_XPATH)
        
        if full_text:
            article_text = ' '.join(paragraph.text for paragraph in full_text)
            return article_text
        else:
            return None
        

    def get_topics(driver):
        topics_XPATH = '//div[contains(@class, "ssrcss-1szabdv-StyledTagContainer")]/div/ul/li'
        topics = driver.find_elements(By.XPATH, topics_XPATH)

        return list(set([topic.text for topic in topics])) if topics else None


    def get_images(driver):
        images_XPATH = '//div[@data-component="image-block"]/@src'
        images = driver.find_elements(By.XPATH, images_XPATH)
        return [image.text for image in images] if images else None


    def get_authors(driver):
        authors_XPATH = '//div[@data-component="byline-block"]/div/div[contains(@class, "ssrcss-h3c0s8-ContributorContainer")]/div[contains(@class, "ssrcss-1u2in0b-Container-ContributorDetails")]/div'
        authors = driver.find_elements(By.XPATH, authors_XPATH)
        
        return [author.text for author in authors] if authors else None
        
        
    # def get_video(driver):
    #     try:
    #         play_button_XPATH = '//button[contains(@class, "p_button") and contains(@class,"p_cta")]'
    #         import time 
    #         time.sleep(1)

    #         play_button = WebDriverWait(driver, 20).until(
    #             EC.presence_of_element_located((By.XPATH, play_button_XPATH))
    #         )

    #         # play_button = driver.find_element(By.XPATH, play_button_XPATH)
    #         play_button.click()
    #         video_XPATH = '//video[@id="p_v_player_0"]/@src'
    #         video = driver.find_element(By.XPATH, video_XPATH)
    #     except NoSuchElementException:
    #         return None
    #     return video.text
        
        
    def scrape_secondary_menu(driver, parent_tab, tab, submenu, scrape_date):
        nonlocal ACTIVE_SUBMENU
        
        for secondary_menu_element in submenu:
            logging.info("SubMenu: %s", secondary_menu_element.text)
            
            ACTIVE_SUBMENU = secondary_menu_element.text

            if secondary_menu_element.text in ["Local News", "Market Data"]:continue
            
            ActionChains(driver).move_to_element(secondary_menu_element).key_down(Keys.CONTROL).click(secondary_menu_element).key_up(Keys.CONTROL).perform()

            child_of_child_tab = driver.window_handles
            for child_tab in child_of_child_tab:
                if (child_tab != tab and child_tab != parent_tab):break
                
            driver.switch_to.window(child_tab)
            logging.info("Switched to child of main for secondary menu")
            scrape_articles(driver, parent_tab, tab, child_tab, scrape_date)

            driver.close()
            logging.info("Closed  secondary menu")

            driver.switch_to.window(tab)
            logging.info("Switched to primary menu")
                                
        
    def scrape_main_menu(driver, menu_name, menu_element, scrape_date):
        nonlocal ACTIVE_MENU
        nonlocal ACTIVE_SUBMENU
        
        ACTIVE_MENU = menu_name

        # SECONDARY OPTIONS ---------------------------------------------------------
        secondary_menu_xpath = '//nav[@class="nw-c-nav__wide-secondary"]/ul/li/a[@class="nw-o-link"]'
        secondary_overflow_menu_xpath = '//div[@class="nw-c-nav__secondary-overflow-list-container"]/div/ul/li/a[@class="nw-o-link"]'
        secondary_more_button_xpath = '//nav[@class="nw-c-nav__wide-secondary"]/ul/li/span/button[contains(@class, "nw-c-nav__secondary-morebutton")]'
        
        # SECOND UI LAYOUT ----------------------------------------------------------
        alternative_secondary_menu_xpath = '//div[contains(@class, "ssrcss-vmsd89-MenuContainer-SecondaryNavBarContainer")]/div/div/ul/li/a[contains(@class,"ssrcss-1wnvs3g-StyledLink")]'
        # does not have overflow
        
        logging.info("Main Menu: %s", menu_name)
        
        ActionChains(driver).move_to_element(menu_element).key_down(Keys.CONTROL).click(menu_element).key_up(Keys.CONTROL).perform()
        
        parent_tab = driver.current_window_handle
        child_tab = driver.window_handles
        
        for tab in child_tab:
            if(tab != parent_tab):break
            
        driver.switch_to.window(tab)
        logging.info("Switched to primary menu from root")
        secondary_menu_elements = driver.find_elements(By.XPATH, secondary_menu_xpath)
        
        
        if not secondary_menu_elements:
            secondary_menu_elements = driver.find_elements(By.XPATH, alternative_secondary_menu_xpath)
                        
        if len(secondary_menu_elements) == 1 or not secondary_menu_elements: # no secondary menu or single element
            ACTIVE_SUBMENU = None
            if secondary_menu_elements:
                ACTIVE_SUBMENU = secondary_menu_elements[0].text
            scrape_articles(driver, parent_tab, tab, None, scrape_date)
            
        else:
            scrape_secondary_menu(driver, parent_tab, tab, secondary_menu_elements, scrape_date)
            
                    
        driver.close()
        logging.info("Closed Primary Menu")
        driver.switch_to.window(parent_tab)
        logging.info("Switch to root menu")

    
    def save_scrapped_data(SCRAPPED_DATA):
        import pandas as pd
        from datetime import date
        
        bbc_df = pd.DataFrame().from_dict(SCRAPPED_DATA)
        
        file_name = f"BBC_DATA_{date.today().strftime('%Y-%m-%d')}.csv"
        file_path = f"./data/{file_name}"
        
        bbc_df.to_csv(file_path, index=False)
        return {"name": file_name, "path": file_path}
        
    def initialize_scraping(base_url):
        menu_dict = {}
        overflow_menu_dict = {}

        is_empty_s3 = is_empty_s3_bucket()

        scrape_date = get_scrape_date(is_empty_s3)
        
        driver.get(base_url)
        logging.info(scrape_date)
        logging.info(base_url)
       
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//nav[@class="nw-c-nav__wide"]/ul/li/a[@class="nw-o-link"]'))
        )

        # MAIN MENU ------------------------------------------------------------------
        main_menu_xpath = '//nav[@class="nw-c-nav__wide"]/ul/li/a[@class="nw-o-link"]'
        overflow_menu_xpath = '//div[@class="nw-c-nav__wide-overflow-list-container"]/div/ul/li/a[@class="nw-o-link"]'
        more_button_xpath = '//nav[@class="nw-c-nav__wide"]/ul/li/span/button[contains(@class, "nw-c-nav__wide-morebutton")]'
        
        main_menu_elements = driver.find_elements(By.XPATH, main_menu_xpath)
        
        exclude_items = ["home", "video", "world news tv", "in pictures"]
        
        for main_menu_element in main_menu_elements:
            menu_text = main_menu_element.text

            if any(exclude in menu_text.lower() for exclude in exclude_items):continue
        
            menu_dict[menu_text] = main_menu_element
        
        for menu_name, menu_element in menu_dict.items():
            scrape_main_menu(driver, menu_name, menu_element, scrape_date)
            
        # MAIN MENU More------------------------------------------------------------------
        more_button = driver.find_element(By.XPATH, more_button_xpath)
        more_button.click()
        overflow_menu_elements = driver.find_elements(By.XPATH, overflow_menu_xpath)
        
        for main_menu_element in overflow_menu_elements:
            menu_text = main_menu_element.text
            if any(exclude in menu_text.lower() for exclude in exclude_items):continue

            overflow_menu_dict[menu_text] = main_menu_element
            
        for menu_name,menu_element in overflow_menu_dict.items():
            scrape_main_menu(driver, menu_name, menu_element, scrape_date)
            
        return SCRAPPED_DATA
    
    # task_instance = kwargs['ti']
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    
    driver = webdriver.Remote(
        'remote_chrome:4444',
        options=chrome_options
    )
    
    logging.info("Initialized driver...")
    
    SCRAPPED_DATA = [] # to be pushed to next task
    VISITED_ARTICLES = set()
    
    logging.info('Intialized Script')
    
    data = initialize_scraping("https://www.bbc.co.uk/news") # trigger task
    
    return save_scrapped_data(data)
    

@task(task_id="upload_scraped_data")
def upload_scraped_data(**kwargs):
    
    task_instance = kwargs['ti']
    scraped_data_info = task_instance.xcom_pull(task_ids="scrape_bbc_articles")
    file_name = scraped_data_info["name"]
    file_path = scraped_data_info["path"]
    
    import boto3
    from boto3.s3.transfer import S3Transfer
    import configparser
    import os
        
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

    transfer = S3Transfer(s3_client)
    
    transfer.upload_file(file_path, s3_bucket_name, file_name, extra_args={'ServerSideEncryption': "AES256"})


default_args = {
    'owner': 'Adnane',
    'depends_on_past': False, # Previous Fails doesn't stop it from triggering
    'start_date': datetime(2024, 1, 7), # January 7th, 2024 (7th for historicall and 8th for daily)
    'end_date': datetime(2024, 1, 13), # January 13th, 2024, daily collections as full 3 months run was triggered manually through airflow ui
    'email': ['adnanebenzo194@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        dag_id='scrape_bbc',
        default_args=default_args,
        schedule_interval='0 22 * * *', # everyday some time before midnight, scrape date is gathered before starting process so no issue shall happen (clean/upsert worst case)
        tags=["Scraping", "Data Engineering"] 
    ) as dag:
    
    scrape_bbc_articles() >> upload_scraped_data()