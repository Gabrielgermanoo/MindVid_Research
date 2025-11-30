import os
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp as youtube_dl
import threading
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

csv_lock = threading.Lock()


class TikTokAutomation:
    def __init__(self):
        self.driver = self._config_driver()

    def _config_driver(self):
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
        capabilities = {
            "platformName": "Android",
            "automationName": "uiautomator2",
            "deviceName": "RXCY20183EH",
            "udid": "RXCY20183EH",
            "appPackage": "com.android.settings",
            "appActivity": ".Settings",
            "language": "en",
            "locale": "US",
            "noReset": True,
            "adbExecTimeout": 60000,
        }
        appium_server_url = "http://localhost:4723"
        capabilities_options = UiAutomator2Options().load_capabilities(capabilities)

        return webdriver.Remote(
            command_executor=appium_server_url, options=capabilities_options
        )

    def open_tiktok(self):
        print("open_tik_tok")
        el1 = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="TikTok")
        el1.click()

    def scroll_down(self):
        size = self.driver.get_window_size()
        self.driver.swipe(
            size["width"] // 2,
            size["height"] * 3 // 4,
            size["width"] // 2,
            size["height"] // 4,
            1000,
        )

    def get_link(self):
        print("getLink")
        el1 = self.driver.find_element(
            by=AppiumBy.ANDROID_UIAUTOMATOR,
            value='new UiSelector().descriptionStartsWith("Share video")',
        )
        el1.click()
        time.sleep(2)
        print("copy link")
        el2 = self.driver.find_element(
            by=AppiumBy.ANDROID_UIAUTOMATOR,
            value='new UiSelector().text("Copy link")',
        )
        el2.click()
        print("get clipboard")
        link = self.driver.get_clipboard_text()
        return link

    def check_views(self):
        print("check views")
        import re
        try:
            el1 = self.driver.find_element(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value='new UiSelector().descriptionStartsWith("Like video")',
            )
            like_desc = el1.get_attribute("contentDescription")
            print("Descrição do like:", like_desc)
            match = re.search(r"Like video\. ([\d\.,KM]+) likes", like_desc)
            if match:
                num_likes = match.group(1)
                print("Likes extraídos:", num_likes)
                if any(x in num_likes for x in ["K", "M", "mi"]):
                    return True
            return False
        except Exception as e:
            print("Erro ao checar views:", e)
            return False

    def search_hashtag(self, text, is_first):
        time.sleep(2)
        print(text)

        if is_first:
            print("first")
            go_to_search_button = self.driver.find_element(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value='new UiSelector().text("Discover")',
            )
            go_to_search_button.click()
        else:
            print("second")
            go_to_search_button = self.driver.find_element(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value='new UiSelector().resourceId("com.zhiliaoapp.musically:id/wau")',
            )
            go_to_search_button.click()

        print("type")
        time.sleep(2)
        search_field = self.driver.find_element(
            by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Search")'
        )
        search_field.click()

        search_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (AppiumBy.CLASS_NAME, "android.widget.EditText")
            )
        )
        search_field.click()
        search_field.clear()
        search_field.send_keys(text)

        print("search")
        search_button = self.driver.find_element(
            by=AppiumBy.ANDROID_UIAUTOMATOR,
            value='new UiSelector().text("Search")',
        )
        search_button.click()
        time.sleep(2)

        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(
            self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch")
        )
        actions.w3c_actions.pointer_action.move_to_location(199, 584)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def download_videos(self, save_directory, key):
        csv_path = os.getenv("CSV_PATH")
        print(f"CSV Path: {csv_path}")
        key_folder = os.path.join(csv_path, key)
        os.makedirs(key_folder, exist_ok=True)

        full_path = os.path.join(key_folder, key + ".csv")
        existing_links = set()
        last_id = -1

        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            existing_links.update(df["Link"])
            if "ID" in df.columns:
                last_id = df["ID"].max()

        urls = pd.DataFrame(columns=["ID", "Link", "Views"])
        videos = 0
        cont = len(existing_links)

        while cont < 400:
            try:
                should_save = self.check_views()
            except:
                self.scroll_down()
                time.sleep(2)
                should_save = self.check_views()

            if should_save:
                success = self._handle_video_download(
                    existing_links, urls, last_id, save_directory, key
                )
                if success:
                    last_id += 1
                    cont += 1
                    print(f"Vídeo {cont} com views altas - last_id: {last_id}")

            self.scroll_down()
            time.sleep(2)
            videos += 1
            self._save_csv(full_path, urls, existing_links)

        self._save_csv(full_path, urls, existing_links)
        print(f"Total de vídeos analisados: {videos}\nTotal de vídeos baixados: {cont}")

    def _handle_video_download(
        self, existing_links, urls, last_id, save_directory, key
    ):
        try:
            link = self.get_link()
            print(f"Link obtido: {link}")

            if link in existing_links:
                print(f"Link já existe: {link}")
                return False
            else:
                last_id += 1
                urls.loc[len(urls)] = [
                    last_id,
                    link,
                    0,
                ]  # Views será 0 por padrão no TikTok
                self._download_video(link, save_directory, last_id)
                return True
        except Exception as e:
            print(f"Erro ao obter link: {e}")
            return False

    def _download_video(self, link, save_directory, last_id):
        ydl_opts = {
            "format": "bestaudio/best",
            "cookiesfrombrowser": ("chrome",),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(save_directory, f"{last_id}_%(id)s.%(ext)s"),
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
        except youtube_dl.utils.DownloadError:
            print(f"Erro ao baixar o vídeo {link}")

    def _save_csv(self, csv_file_path, urls, existing_links):
        with csv_lock:
            combined_df = pd.DataFrame()

            if os.path.exists(csv_file_path):
                existing_df = pd.read_csv(csv_file_path)

                if "Views" not in existing_df.columns:
                    existing_df["Views"] = 0

                combined_df = pd.concat([existing_df, urls], ignore_index=True)
            else:
                combined_df = urls.copy()

            combined_df.drop_duplicates(subset=["Link"], inplace=True)

            if not combined_df.empty and "ID" in combined_df.columns:
                combined_df["ID"] = (
                    pd.to_numeric(combined_df["ID"], errors="coerce")
                    .fillna(0)
                    .astype(int)
                )
                combined_df["Views"] = (
                    pd.to_numeric(combined_df["Views"], errors="coerce")
                    .fillna(0)
                    .astype(int)
                )

            combined_df = combined_df[["ID", "Link", "Views"]]
            combined_df.to_csv(csv_file_path, index=False, header=True)


def main():
    tiktok_bot = TikTokAutomation()
    tiktok_bot.open_tiktok()

    hashtags_list = {
        # "depressao": ["#depressao"],
        # "ansiedade": ["#ansiedade"],
        # "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        # "TEA": ["#TEA", "#autismo", "#transtornodoespectroautista"],
        # "TBP": ["#bipolaridade"],
        "borderline": ["#transtornoborderline"],  # transtornoborderline
    }

    save_directory = os.getenv("SAVE_DIRECTORY")
    if not save_directory:
        raise ValueError("SAVE_DIRECTORY não definido no .env")

    is_first = True
    for key, value in hashtags_list.items():
        subfolder_path = os.path.join(save_directory, key)
        os.makedirs(subfolder_path, exist_ok=True)
        for hashtag in value:
            tiktok_bot.search_hashtag(hashtag, is_first=is_first)
            is_first = False
            tiktok_bot.download_videos(subfolder_path, key)

    tiktok_bot.driver.quit()


if __name__ == "__main__":
    main()
