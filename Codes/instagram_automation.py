import os
import time
import pandas as pd
from dotenv import load_dotenv
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp as youtube_dl

class InstagramAutomation:
    def __init__(self):
        self.driver = self._config_driver()
        
    def _config_driver(self):
        load_dotenv()
        capabilities = {
            "platformName": "Android",
            "automationName": "uiautomator2",
            "deviceName": "emulator-5554",
            "appPackage": "com.android.settings",
            "appActivity": ".Settings",
            "language": "en",
            "locale": "US",
            "noReset": True,
        }
        appium_server_url = 'http://localhost:4723'
        capabilities_options = UiAutomator2Options().load_capabilities(capabilities)
        
        return webdriver.Remote(command_executor=appium_server_url, options=capabilities_options)
    
    def swipe_up(self, duration = 800):
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] // 2
        end_y = size['height'] // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, duration)
        
    def find_instagram_app(self):
        return self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Instagram")')
    
    def open_instagram_app(self):
        self.find_instagram_app().click()
        
    def login(self):
        username = os.getenv('INSTAGRAM_USERNAME')
        password = os.getenv('INSTAGRAM_PASSWORD')
        
        username_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((AppiumBy.XPATH, '(//android.widget.EditText)[1]')))
        username_field.clear()
        username_field.send_keys(username)

        password_field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((AppiumBy.XPATH, '(//android.widget.EditText)[2]')))
        password_field.send_keys(password)

        self.driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@content-desc='Log in']/android.view.ViewGroup").click()
        
    def is_link_in_csv(self, link, csv_file):
        df = pd.read_csv(csv_file)
        
        return df['Link'].str.contains(link).any()
    
    def search_hashtag(self, text, first):
        time.sleep(5)
        if first:
            search_button = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                     'new UiSelector().resourceId("com.instagram.android:id/tab_icon").instance(2)')
        else:
            search_button = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                     'new UiSelector().resourceId("com.instagram.android:id/search_tab")')
        search_button.click()

        search_field = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
                                                'new UiSelector().resourceId("com.instagram.android:id/action_bar_search_edit_text")')
        search_field.click()
        search_field.clear()
        search_field.send_keys(text)
        self.driver.press_keycode(66)  # Press Enter

        try:
            keep_searching_button = WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("com.instagram.android:id/see_results_footer")')))
            self.driver.tap([(keep_searching_button.location['x'] + keep_searching_button.size['width'] - 1,
                              keep_searching_button.location['y'] + keep_searching_button.size['height'] - 1)])
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("com.instagram.android:id/layout_container").instance(0)'))).click()
        except TimeoutException:
            self.driver.press_keycode(66)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("com.instagram.android:id/layout_container").instance(0)'))).click()
            
    def download_videos(self, save_directory, key):
        csv_path = os.getenv('CSV_PATH')
        full_path = os.path.join(csv_path, key + '.csv')
        existing_links = set()
        last_id = -1

        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            existing_links.update(df['Link'])
            if 'ID' in df.columns:
                last_id = df['ID'].max()

        urls = pd.DataFrame(columns=['ID', 'Link'])
        videos = 0
        cont = 0

        while cont < 140:
            try:
                likes_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, "//android.view.ViewGroup[contains(@content-desc, 'Like number is')]")))
                likes_button.click()
            except TimeoutException:
                self.swipe_up()
                continue

            try:
                views_string = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/play_count_text")))
                num_views = int(views_string.text.split(" ")[0].replace(",", ""))
            except TimeoutException:
                num_views = 0
            finally:
                self.driver.back()

            if num_views > 100000:
                self._handle_video_download(existing_links, urls, last_id, save_directory, key)
                cont += 1
                self.driver.back()
            videos += 1
            self._swipe_to_next_video()

        self._save_csv(full_path, urls, existing_links)
        print(f"Total de vídeos analisados: {videos}\nTotal de vídeos com mais de 100k views: {cont}")
        
    
    def _handle_video_download(self, existing_links, urls, last_id, save_directory, key):
        share_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Share"]')))
        share_button.click()

        copied_link = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.TextView[@resource-id="com.instagram.android:id/label" and @text="Copy link"]')))
        link = self.driver.get_clipboard_text()

        if link in existing_links:
            self.swipe_up()
        else:
            last_id += 1
            urls.loc[len(urls)] = [last_id, link]
            self._download_video(link, save_directory, last_id)
            
    
    def _download_video(self, link, save_directory, last_id):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(save_directory, f'{last_id}_%(id)s.%(ext)s'),
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
        except youtube_dl.utils.DownloadError:
            print(f"Erro ao baixar o vídeo {link}")

    def _swipe_to_next_video(self):
        size = self.driver.get_window_size()
        self.driver.swipe(size['width'] // 2, size['height'] * 3 // 4, size['width'] // 2, size['height'] // 4, 1000)
        time.sleep(3)
    
    def _save_csv(self, csv_file_path, urls, existing_links):
        combined_df = pd.concat([pd.DataFrame(list(existing_links), columns=['Link']), urls], ignore_index=True)
        combined_df.drop_duplicates(subset=['Link'], inplace=True)
        combined_df['ID'] = combined_df['ID'].astype(int)
        combined_df.to_csv(csv_file_path, index=False, header=True)
        

def main():
    instagram_bot = InstagramAutomation()
    instagram_bot.open_instagram_app()
    # instagram_bot.login()
    time.sleep(5)
    
    hashtags_list = {
        #"ansiedade": ["#ansiedade", "#transtornodeansiedade"],
        "depressao": ["#depressao", "#transtornodepressivo"],
        #"TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        #"TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
    }
    
    save_directory = os.getenv('SAVE_DIRECTORY')
    
    for key, value in hashtags_list.items():
        subfolder_path = os.path.join(save_directory, key)
        os.makedirs(subfolder_path, exist_ok=True)
        for hashtag in value:
            instagram_bot.search_hashtag(hashtag, first=True)
            instagram_bot.download_videos(subfolder_path, key)

if __name__ == '__main__':
    main()