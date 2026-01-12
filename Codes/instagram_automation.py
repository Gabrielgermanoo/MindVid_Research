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
from selenium.webdriver.remote.webelement import WebElement
from appium.webdriver.webdriver import WebDriver
import yt_dlp as youtube_dl
import threading
from typing import Set, Optional

csv_lock = threading.Lock()


class InstagramAutomation:
    def __init__(self) -> None:
        """
        Initialize the InstagramAutomation instance and configure the Appium driver.
        """
        self.driver: WebDriver = self._config_driver()

    def _config_driver(self) -> WebDriver:
        """
        Configure and return an Appium WebDriver for the Android device.

        Returns:
            WebDriver: Configured Appium WebDriver instance.
        """
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
        capabilities = {
            "platformName": "Android",
            "automationName": "uiautomator2",
            "deviceName": "RXCY20183EH",  # Use the adb device command to find your device name
            "udid": "RXCY20183EH",  # Use the adb device command to find your device name
            "appPackage": "com.android.settings",
            "appActivity": ".Settings",
            "language": "en",
            "locale": "US",
            "noReset": True,
            "adbExecTimeout": 60000,
        }
        appium_server_url = "http://localhost:4723"  # Here the port should match the one used by your Appium server
        capabilities_options = UiAutomator2Options().load_capabilities(capabilities)

        return webdriver.Remote(command_executor=appium_server_url, options=capabilities_options)

    def swipe_up(self, duration: int = 800) -> None:
        """
        Swipe up on the device screen.

        Args:
            duration (int): Duration of the swipe in milliseconds.
        """
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = size["height"] // 2
        end_y = size["height"] // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, duration)

    def find_instagram_app(self) -> WebElement:
        """
        Find the Instagram app icon element on the device.

        Returns:
            WebElement: The WebElement corresponding to the Instagram app icon.
        """
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Instagram")'
        )

    def open_instagram_app(self) -> None:
        """
        Open the Instagram app by tapping its icon.
        """
        self.find_instagram_app().click()

    def login(self) -> None:
        """
        Log in to Instagram using credentials from environment variables:
        INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD.
        """
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")

        username_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "(//android.widget.EditText)[1]"))
        )
        username_field.clear()
        username_field.send_keys(username)

        password_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((AppiumBy.XPATH, "(//android.widget.EditText)[2]"))
        )
        password_field.send_keys(password)

        self.driver.find_element(
            AppiumBy.XPATH,
            "//android.widget.Button[@content-desc='Log in']/android.view.ViewGroup",
        ).click()

    def is_link_in_csv(self, link: str, csv_file: str) -> bool:
        """
        Check if a link is already present in a CSV file.

        Args:
            link (str): The link to check.
            csv_file (str): Path to the CSV file.

        Returns:
            bool: True if the link exists in the CSV, False otherwise.
        """
        df = pd.read_csv(csv_file)
        return df["Link"].str.contains(link).any()

    def search_hashtag(self, text: str, first: bool) -> None:
        """
        Search a hashtag in Instagram.

        Args:
            text (str): Hashtag or text to search.
            first (bool): Whether this is the first search (affects which tab is used).
        """
        time.sleep(5)
        if first:
            search_button = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().resourceId("com.instagram.android:id/search_tab")',
            )
        else:
            search_button = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().resourceId("com.instagram.android:id/tab_icon").instance(1)',
            )
        search_button.click()

        search_field = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().resourceId("com.instagram.android:id/action_bar_search_edit_text")',
        )
        search_field.click()
        search_field.clear()
        search_field.send_keys(text)
        self.driver.press_keycode(66)

        try:
            keep_searching_button = WebDriverWait(self.driver, 6).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().resourceId("com.instagram.android:id/see_results_footer")',
                    )
                )
            )
            self.driver.tap(
                [
                    (
                        keep_searching_button.location["x"]
                        + keep_searching_button.size["width"]
                        - 1,
                        keep_searching_button.location["y"]
                        + keep_searching_button.size["height"]
                        - 1,
                    )
                ]
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().resourceId("com.instagram.android:id/layout_container").instance(0)',
                    )
                )
            ).click()
        except TimeoutException:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().resourceId("com.instagram.android:id/layout_container").instance(0)',
                    )
                )
            ).click()

    def download_videos(self, save_directory: str, key: str) -> None:
        """
        Scroll through posts in a hashtag and download videos that meet view thresholds.
        Results and metadata are stored in a per-key CSV under CSV_PATH.

        Args:
            save_directory (str): Directory to save downloaded audio files.
            key (str): Key used for CSV filename and subfolder.
        """
        csv_path = os.getenv("CSV_PATH")
        key_folder = os.path.join(csv_path, key)
        os.makedirs(key_folder, exist_ok=True)

        full_path = os.path.join(key_folder, key + ".csv")
        existing_links: Set[str] = set()
        last_id = -1

        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            existing_links.update(df["Link"])
            if "ID" in df.columns:
                last_id = df["ID"].max()

        urls = pd.DataFrame(columns=["ID", "Link", "Views"])
        videos = 0
        cont = len(existing_links)

        while cont < 200:
            try:
                likes_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().resourceId("com.instagram.android:id/like_count")',
                        )
                    )
                )
                likes_button.click()
            except TimeoutException:
                self.swipe_up()
                continue

            try:
                views_string = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (AppiumBy.ID, "com.instagram.android:id/video_view_count_text")
                    )
                )
                num_views = int(views_string.text.split(" ")[0].replace(",", ""))
            except TimeoutException:
                num_views = 0
            finally:
                self.driver.back()

            if num_views > 10000:
                success = self._handle_video_download(
                    existing_links, urls, last_id, save_directory, key, num_views
                )
                if success:
                    last_id += 1
                    cont += 1
                    print(
                        f"Vídeo {cont} com mais de 100k views: {num_views} views - last_id: {last_id}"
                    )

                self.driver.back()
            videos += 1
            self._save_csv(full_path, urls, existing_links)
            self._swipe_to_next_video()

        self._save_csv(full_path, urls, existing_links)
        print(
            f"Total de vídeos analisados: {videos}\nTotal de vídeos com mais de 100k views: {cont}"
        )

    def _handle_video_download(
        self,
        existing_links: Set[str],
        urls: pd.DataFrame,
        last_id: int,
        save_directory: str,
        key: str,
        num_views: int,
    ) -> bool:
        """
        Copy the current post link, check for duplicates, add metadata and download audio.

        Args:
            existing_links (Set[str]): Set of already seen links.
            urls (pd.DataFrame): DataFrame to which the new entry will be appended.
            last_id (int): Last used numeric ID (will be incremented locally).
            save_directory (str): Directory to save files.
            key (str): Key used for naming.
            num_views (int): Number of views for the current video.

        Returns:
            bool: True if a new video was processed and downloaded, False if the link existed.
        """
        share_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Share"]')
            )
        )
        share_button.click()

        copy_link_option = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Copy link")')
            )
        )
        copy_link_option.click()

        time.sleep(2)

        link = self.driver.get_clipboard_text()

        if link in existing_links:
            print(f"Link já existe: {link}")
            return False
        else:
            last_id += 1
            urls.loc[len(urls)] = [last_id, link, num_views]
            self._download_video(link, save_directory, last_id)
            return True

    def _download_video(self, link: str, save_directory: str, last_id: int) -> None:
        """
        Download audio from a given Instagram/video link using yt_dlp and ffmpeg.

        Args:
            link (str): URL to download.
            save_directory (str): Directory where the file will be saved.
            last_id (int): Numeric ID used in the output filename.
        """
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(save_directory, f"{last_id}_%(id)s.%(ext)s"),
            "cookiesfrombrowser": None,
            "headers": {
                "User-Agent": "Instagram 219.0.0.12.117 Android",
            },
        }
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
        except youtube_dl.utils.DownloadError:
            print(f"Erro ao baixar o vídeo {link}")

    def _swipe_to_next_video(self) -> None:
        """
        Swipe from bottom to top to move to the next video/post.
        """
        size = self.driver.get_window_size()
        self.driver.swipe(
            size["width"] // 2,
            size["height"] * 3 // 4,
            size["width"] // 2,
            size["height"] // 4,
            1000,
        )
        time.sleep(3)

    def _save_csv(self, csv_file_path: str, urls: pd.DataFrame, existing_links: Set[str]) -> None:
        """
        Save or merge the collected URLs DataFrame with an existing CSV file in a thread-safe way.

        Args:
            csv_file_path (str): Path to the CSV file to write.
            urls (pd.DataFrame): Newly collected rows to append.
            existing_links (Set[str]): Set of existing links (not directly modified here).
        """
        with csv_lock:
            combined_df = pd.DataFrame()

            if os.path.exists(csv_file_path):
                existing_df = pd.read_csv(csv_file_path)

                if "Views" not in existing_df.columns:
                    existing_df["Views"] = 0

                combined_df = pd.concat([existing_df, urls], ignore_index=True)
            else:
                combined_df = urls

            combined_df.drop_duplicates(subset=["Link"], inplace=True)
            if not combined_df.empty and "ID" in combined_df.columns:
                combined_df["ID"] = combined_df["ID"].astype(int)
                combined_df["Views"] = combined_df["Views"].astype(int)

            combined_df = combined_df[["ID", "Link", "Views"]]

            combined_df.to_csv(csv_file_path, index=False, header=True)


def main() -> None:
    """
    Entry point: instantiate the bot, open Instagram, and run searches/downloads for configured hashtags.
    """
    instagram_bot = InstagramAutomation()
    instagram_bot.open_instagram_app()
    # instagram_bot.login()
    time.sleep(5)

    hashtags_list = {
        # "ansiedade": ["#ansiedade"],
        # "depressao": ["#depressao", "#transtornodepressivo"],
        # "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        # "TEA": ["#transtornodoespectroautista"],
        # "TEPT": ["#PTSD"], #estressepostraumatico,TEPT
        # "TBP": ["#transtornoafetivobipolar"],
        # "TOC": ["#TOC"], #transtornoobsessivocompulsivo,
        # "suicidio": ["#diganaoaosuicidio"], #prevencaosuicidio,suicidionão,combateaosuicidio
        "borderline": ["#borderline"],  # transtornoborderline
    }

    save_directory = os.getenv("SAVE_DIRECTORY")

    for key, value in hashtags_list.items():
        subfolder_path = os.path.join(save_directory, key)
        os.makedirs(subfolder_path, exist_ok=True)
        for hashtag in value:
            instagram_bot.search_hashtag(hashtag, first=True)
            instagram_bot.download_videos(subfolder_path, key)


if __name__ == "__main__":
    main()
