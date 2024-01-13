from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from boto3 import client as boto3_client
import logging    
from dateutil.relativedelta import relativedelta
import configparser
import os
from datetime import date


@task(task_id="get_scrape_historical_limit")
def get_scrape_historical_limit(**kwargs):
        
    
    def is_empty_s3_bucket():
        
        parser = configparser.ConfigParser()
        parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

        # AWS
        aws_access_key = parser.get('aws', 'aws_access_key')
        aws_secret_key = parser.get('aws', 'aws_secret_key')
        s3_bucket_name = parser.get('aws', 's3_bucket_name')

        s3_client = boto3_client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
        s3_bucket = s3_client.list_objects(Bucket=s3_bucket_name, Prefix="raw-data/")
        
        return "Contents" not in s3_bucket


    def get_scrape_date(is_empty_s3_bucket):

        if not is_empty_s3_bucket:
            
            return date.today().strftime("%Y-%m-%d")
        else:
            
            return (date.today() + relativedelta(months=-3)).strftime("%Y-%m-%d")
        
    
    is_empty_s3 = is_empty_s3_bucket()
    scrape_date = get_scrape_date(is_empty_s3)
    
    return scrape_date
    
    
@task(task_id="scrape_bbc_articles")
def scrape_bbc_articles(**kwargs):
    
    from concurrent.futures import ThreadPoolExecutor as thread_executor
    from itertools import repeat
    import requests
    from bs4 import BeautifulSoup
    from lxml import etree
    import dateparser
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import ChromiumOptions
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException, WebDriverException
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    ACTIVE_MENU = None
    ACTIVE_SUBMENU = None
   
    # sets to keep track of menus to skip if there is a stale element on menus 
    VISITED_MAIN_MENU = set()
    VISITED_SECONDARY_MENU = set()
   
    SCRAPED_DATA = [] # to be pushed to next task
    VISITED_ARTICLES = set()
    
    
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
            
            WebDriverWait(driver, 60).until(
                lambda drvr: int(drvr.find_element(By.CLASS_NAME, "qa-pagination-current-page-number").text) != current_page
            )
            
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
                
        except StaleElementReferenceException:
            logging.info("Refresh driver triggered from scrape articles")
            driver.refresh()
            scrape_articles(driver, root_tab, menu_tab, submenu_tab, scrape_date)
        

    '''
    # OBSOLETE
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
    '''
        
        
    def get_article_data(article, latest_news, menu_tab, submenu_tab, scrape_date):
        nonlocal VISITED_ARTICLES
        
        # new hybrid way
        is_latest_news = article[0] in latest_news
        uri = article[1]
        
        if uri in VISITED_ARTICLES: return None
        
        if not ('/news/' in uri) or '/live/' in uri or '/resources/' in uri: return None # we want only articles aka /news
        
        return scrape_article(menu_tab, submenu_tab, uri, is_latest_news, scrape_date)
        
       
    
    def gather_data_from_page(driver, root_tab, menu_tab, submenu_tab, scrape_date):
        
        # new hybrid approach
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
        
        pages_uris = []
        
        for page in page_news:
            uri = page.get_attribute('href')
            pages_uris.append((page, uri))
            
        with thread_executor(max_workers=10) as executor:
            logging.info("%s Worker in executor", executor._max_workers)
            results = executor.map(get_article_data, pages_uris, repeat(latest_news), repeat(menu_tab), repeat(submenu_tab), repeat(scrape_date))
                        
            should_continue_scraping = True
            
            for is_valid_article in results:
                if is_valid_article is not None and not is_valid_article:
                    should_continue_scraping = False
            
            if not should_continue_scraping: 
                logging.info("Stopping scraping of category due to historical limit")

            return should_continue_scraping
    
    
    '''
    # OBSOLETE
    def scrape_article(driver, menu, submenu, uri, is_latest_news, scrape_date): 
    
        nonlocal ACTIVE_MENU
        nonlocal ACTIVE_SUBMENU
        nonlocal SCRAPED_DATA
        
        logging.info("Currently at article: %s", uri)
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

            SCRAPED_DATA.append(scraped_object)
    
            return True

        except WebDriverException:
            driver.refresh()
    
            return scrape_article(driver, menu, submenu, uri, is_latest_news, scrape_date)
    '''
        
        
    def scrape_article(menu, submenu, uri, is_latest_news, scrape_date): 
        
        nonlocal ACTIVE_MENU
        nonlocal ACTIVE_SUBMENU
        nonlocal SCRAPED_DATA
        nonlocal VISITED_ARTICLES
        
        logging.info("Currently at article: %s", uri)
        article_response = requests.get(uri)
        article_bs = BeautifulSoup(article_response.content, 'html.parser')
        article_dom = etree.HTML(str(article_bs)) 

        
        date_posted = get_date_posted(article_dom)
        if date_posted < scrape_date:
            # article posted before our tolerance
            VISITED_ARTICLES.add(uri)
            
            return not is_latest_news
            
        title = get_title(article_dom)
        subtitle = get_subtitle(article_dom)
        full_text = get_full_text(article_dom)
        topics = get_topics(article_dom)
        images = get_images(article_dom)
        authors = get_authors(article_dom)
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
           
        logging.info(scraped_object)
        
        SCRAPED_DATA.append(scraped_object)
        
        return True


    def get_title(dom):
        
        title_XPATH = '//h1[@id="main-heading"]'
        title = dom.xpath(title_XPATH)
        
        return ''.join(title[0].itertext()).strip().replace(";", ":") if title else None


    def get_subtitle(dom):
        
        subtitle_XPATH = '//b[contains(@class, "ssrcss-hmf8ql-BoldText")]' # if exists
        subtitle = dom.xpath(subtitle_XPATH)
        
        return ''.join(subtitle[0].itertext()).strip().replace(";", ":") if subtitle else None


    def get_date_posted(dom):
        
        date_posted_XPATH = '//time' #convert to datetime
      
        date_posted = dom.xpath(date_posted_XPATH)
        # date is always existing unless video, if no date element should not be gathered -> return today + 10
        if not date_posted:

            return (date.today() + relativedelta(days=10)).strftime('%Y-%m-%d')
        
        else:
            date_posted = date_posted[0]
        
        date_string = ''.join(date_posted.itertext()).strip()
                
        # if date posted text exists
        if date_string != "":
            timestamp = dateparser.parse(date_string, settings={'RELATIVE_BASE': datetime.now()}).timestamp()
        else:
            timestamp = dateparser.parse(date_posted.get("datetime")).timestamp()

        datetime_object = datetime.fromtimestamp(timestamp)
        
        return datetime_object.strftime('%Y-%m-%d')
        

    def get_full_text(dom):
        
        text_XPATH = '//div[@data-component="text-block"]'
        
        full_text = dom.xpath(text_XPATH)
        
        if full_text:
            article_text = ' '.join(''.join(paragraph.itertext()).strip().replace(";", ":") for paragraph in full_text)
            
            return article_text
        else:
            
            return None
        

    def get_topics(dom):
        
        topics_XPATH = '//div[contains(@class, "ssrcss-1szabdv-StyledTagContainer")]/div/ul/li'
        topics = dom.xpath(topics_XPATH)

        return list(set([''.join(topic.itertext()).strip().replace(";", ":") for topic in topics])) if topics else None


    def get_images(dom):
        
        images_XPATH = '//div[@data-component="image-block"]//img'
        images = dom.xpath(images_XPATH)
        
        return [image.get("src") for image in images] if images else None


    def get_authors(dom):
        
        authors_XPATH = '//div[@data-component="byline-block"]/div/div[contains(@class, "ssrcss-h3c0s8-ContributorContainer")]/div[contains(@class, "ssrcss-1u2in0b-Container-ContributorDetails")]/div'
        authors = dom.xpath(authors_XPATH)
        
        return [''.join(author.itertext()).strip().replace(";", ":") for author in authors] if authors else None
    
    
    ''' OBSOLETE SECTION
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
    
        try:
            date_posted_XPATH = '//time' #convert to datetime
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, date_posted_XPATH))
            )
            
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
    '''
        
        
    def scrape_secondary_menu(driver, parent_tab, tab, submenu, scrape_date):
        
        nonlocal ACTIVE_SUBMENU
        nonlocal VISITED_SECONDARY_MENU
        
        for secondary_menu_element in submenu:
            logging.info("SubMenu: %s", secondary_menu_element.text)
            
            ACTIVE_SUBMENU = secondary_menu_element.text
            
            # if (ACTIVE_SUBMENU in VISITED_SECONDARY_MENU): continue # already finished this submenu 
            
            if (secondary_menu_element.text in ["Local News", "Market Data"]) or (ACTIVE_SUBMENU in VISITED_SECONDARY_MENU):continue
            
            ActionChains(driver).move_to_element(secondary_menu_element).key_down(Keys.CONTROL).click(secondary_menu_element).key_up(Keys.CONTROL).perform()

            child_of_child_tab = driver.window_handles
            for child_tab in child_of_child_tab:
                if (child_tab != tab and child_tab != parent_tab):break
                
            driver.switch_to.window(child_tab)
            logging.info("Switched to child of main for secondary menu")
            scrape_articles(driver, parent_tab, tab, child_tab, scrape_date)
            
            VISITED_SECONDARY_MENU.add(ACTIVE_SUBMENU)

            driver.close()
            logging.info("Closed  secondary menu")

            driver.switch_to.window(tab)
            logging.info("Switched to primary menu")

    
    def refresh_scrape_secondary_menu(driver, parent_tab, tab, scrape_date):
        
        nonlocal ACTIVE_SUBMENU
        
        # SECONDARY OPTIONS ---------------------------------------------------------
        secondary_menu_xpath = '//nav[@class="nw-c-nav__wide-secondary"]/ul/li/a[@class="nw-o-link"]'
        secondary_overflow_menu_xpath = '//div[@class="nw-c-nav__secondary-overflow-list-container"]/div/ul/li/a[@class="nw-o-link"]'
        secondary_more_button_xpath = '//nav[@class="nw-c-nav__wide-secondary"]/ul/li/span/button[contains(@class, "nw-c-nav__secondary-morebutton")]'
        
        # SECOND UI LAYOUT ----------------------------------------------------------
        alternative_secondary_menu_xpath = '//div[contains(@class, "ssrcss-vmsd89-MenuContainer-SecondaryNavBarContainer")]/div/div/ul/li/a[contains(@class,"ssrcss-1wnvs3g-StyledLink")]'
        # does not have overflow
        
        try:
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
                # scrape_secondary_menu(driver, parent_tab, tab, secondary_menu_elements, scrape_date)
            
        except StaleElementReferenceException:
            logging.info("Refreshed driver from refresh scrape secondary menu")
            driver.refresh()
            refresh_scrape_secondary_menu(driver, parent_tab, tab, scrape_date)
            
            
    def scrape_main_menu(driver, menu_name, menu_element, scrape_date):
        
        nonlocal ACTIVE_MENU
        nonlocal ACTIVE_SUBMENU
        
        ACTIVE_MENU = menu_name
    
       
        logging.info("Main Menu: %s", menu_name)
        
        ActionChains(driver).move_to_element(menu_element).key_down(Keys.CONTROL).click(menu_element).key_up(Keys.CONTROL).perform()
        
        parent_tab = driver.current_window_handle
        child_tab = driver.window_handles
        
        for tab in child_tab:
            if(tab != parent_tab):break
        
        driver.switch_to.window(tab)
        logging.info("Switched to primary menu from root")
        
        # refresh if stale
        refresh_scrape_secondary_menu(driver, parent_tab, tab, scrape_date)
                    
        driver.close()
        logging.info("Closed Primary Menu")
        driver.switch_to.window(parent_tab)
        logging.info("Switch to root menu")

    
    def save_scrapped_data(SCRAPED_DATA):
        
        bbc_df = pd.DataFrame().from_dict(SCRAPED_DATA)
        
        file_name = f"BBC_DATA_{date.today().strftime('%Y-%m-%d')}.csv"
        file_path = f"./data/{file_name}"
        
        bbc_df.to_csv(file_path, index=False)
        
        return {"name": file_name, "path": file_path}
        
        
    def discover_main_menu_elements(driver, scrape_date):
        
        nonlocal VISITED_MAIN_MENU

        try:
            menu_dict = {}
            overflow_menu_dict = {}
            
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
                
                # if menu_text in VISITED_MAIN_MENU: continue # dont add menus that succeeded
                if any(exclude in menu_text.lower() for exclude in exclude_items) or menu_text in VISITED_MAIN_MENU:continue
            
                menu_dict[menu_text] = main_menu_element
            
            for menu_name, menu_element in menu_dict.items():
                scrape_main_menu(driver, menu_name, menu_element, scrape_date)
                VISITED_MAIN_MENU.add(menu_name)
                
            # MAIN MENU More------------------------------------------------------------------
            more_button = driver.find_element(By.XPATH, more_button_xpath)
            more_button.click()
            overflow_menu_elements = driver.find_elements(By.XPATH, overflow_menu_xpath)
            
            for main_menu_element in overflow_menu_elements:
                menu_text = main_menu_element.text
                if any(exclude in menu_text.lower() for exclude in exclude_items) or menu_text in VISITED_MAIN_MENU:continue
                
                if menu_text in VISITED_MAIN_MENU: continue # dont add menus that succeeded

                overflow_menu_dict[menu_text] = main_menu_element
                
            for menu_name,menu_element in overflow_menu_dict.items():
                scrape_main_menu(driver, menu_name, menu_element, scrape_date)
                VISITED_MAIN_MENU.add(menu_name)
                
        except StaleElementReferenceException:
            logging.info("Refreshed driver from discover main menu")
            driver.refresh()
            discover_main_menu_elements(driver)
                
                
    def initialize_scraping(base_url, scrape_date):
        
        driver.get(base_url)
        logging.info(scrape_date)
        logging.info(base_url)
       
        discover_main_menu_elements(driver, scrape_date)
            
        return SCRAPED_DATA
    
    task_instance = kwargs['ti']
    scrape_date = task_instance.xcom_pull(task_ids="get_scrape_historical_limit")
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    
    driver = webdriver.Remote(
        'remote_chrome:4444',
        options=chrome_options
    )
    
    logging.info("Initialized driver...")
        
    data = initialize_scraping("https://www.bbc.co.uk/news", scrape_date) # trigger task
    
    return save_scrapped_data(data)
    

@task(task_id="upload_scraped_data")
def upload_scraped_data(**kwargs):
    
    from boto3.s3.transfer import S3Transfer
    
    task_instance = kwargs['ti']
    scraped_data_info = task_instance.xcom_pull(task_ids="scrape_bbc_articles")
    file_name = scraped_data_info["name"]
    file_path = scraped_data_info["path"]
    
    parser = configparser.ConfigParser()
    parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

    # AWS
    aws_access_key = parser.get('aws', 'aws_access_key')
    aws_secret_key = parser.get('aws', 'aws_secret_key')
    s3_bucket_name = parser.get('aws', 's3_bucket_name')
    
    s3_client = boto3_client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

    transfer = S3Transfer(s3_client)
    
    transfer.upload_file(file_path, s3_bucket_name, f"raw-data/{file_name}", extra_args={'ServerSideEncryption': "AES256"})


default_args = {
    'owner': 'Adnane',
    'depends_on_past': False, # Previous Fails doesn't stop it from triggering
    'start_date': datetime(2024, 1, 8), # January 8th, 2024 
    'end_date': datetime(2024, 1, 12), # January 12th, 2024, daily collections as full 3 months run was triggered manually through airflow ui
    'email': ['adnanebenzo194@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
        dag_id='scrape_bbc_daily',
        default_args=default_args,
        schedule_interval='59 22 * * *', # every day before midnight, (clean/upsert worst case for data cleaning)
        tags=["Scraping", "Data Engineering"] 
    ) as dag:
    
    get_scrape_historical_limit() >> scrape_bbc_articles() >> upload_scraped_data()
    