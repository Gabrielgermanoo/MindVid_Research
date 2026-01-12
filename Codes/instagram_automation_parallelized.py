import os
import time
import pandas as pd
import threading
from dotenv import load_dotenv
from appium import webdriver
from pathlib import Path
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp as youtube_dl
from typing import Any, Dict, List, Tuple, Set

# Global lock for CSV file access
csv_lock = threading.Lock()


class InstagramAutomation:
    """
    Automation helper for interacting with Instagram on an Android device via Appium.

    Attributes:
        device_id (str): Device identifier or emulator name.
        appium_port (int): Port where Appium server is running.
        driver (Any): Appium webdriver instance.
    """

    def __init__(
        self, device_id: str = "emulator-5554", appium_port: int = 4723
    ) -> None:
        """
        Initialize InstagramAutomation.

        Parameters:
            device_id (str): Android device id or name.
            appium_port (int): Appium server port.
        """
        self.device_id: str = device_id
        self.appium_port: int = appium_port
        self.driver: Any = self._config_driver()

    def _config_driver(self) -> Any:
        """
        Configure and return an Appium webdriver.Remote instance.

        Returns:
            Any: Configured Appium driver (webdriver.Remote).
        """
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
        capabilities = {
            "platformName": "Android",
            "automationName": "uiautomator2",
            "deviceName": self.device_id,  # Use device_id parameter
            "udid": self.device_id,
            "appPackage": "com.android.settings",
            "appActivity": ".Settings",
            "language": "en",
            "locale": "US",
            "noReset": True,
            "adbExecTimeout": 60000,  # Increased timeout
        }
        appium_server_url = f"http://localhost:{self.appium_port}"  # Use port parameter
        capabilities_options = UiAutomator2Options().load_capabilities(capabilities)

        return webdriver.Remote(
            command_executor=appium_server_url, options=capabilities_options
        )

    def swipe_up(self, duration: int = 800) -> None:
        """
        Swipe up on the device screen.

        Parameters:
            duration (int): Duration of the swipe in milliseconds.
        """
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = size["height"] // 2
        end_y = size["height"] // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, duration)

    def find_instagram_app(self) -> Any:
        """
        Find the Instagram app icon element.

        Returns:
            Any: WebElement for the Instagram app icon.
        """
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Instagram")'
        )

    def open_instagram_app(self) -> None:
        """
        Open the Instagram application by clicking its icon.
        """
        self.find_instagram_app().click()
        print(f"[Device {self.device_id}] Instagram app opened")

    def login(self) -> None:
        """
        Perform login using INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD from environment.
        """
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")

        username_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (AppiumBy.XPATH, "(//android.widget.EditText)[1]")
            )
        )
        username_field.clear()
        username_field.send_keys(username)

        password_field = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (AppiumBy.XPATH, "(//android.widget.EditText)[2]")
            )
        )
        password_field.send_keys(password)

        self.driver.find_element(
            AppiumBy.XPATH,
            "//android.widget.Button[@content-desc='Log in']/android.view.ViewGroup",
        ).click()
        print(f"[Device {self.device_id}] Logged in as {username}")

    def is_link_in_csv(self, link: str, csv_file: str) -> bool:
        """
        Check if a link exists in a CSV file.

        Parameters:
            link (str): Link to check.
            csv_file (str): Path to CSV file.

        Returns:
            bool: True if link exists, False otherwise.
        """
        df = pd.read_csv(csv_file)
        return df["Link"].str.contains(link).any()

    def search_hashtag(self, text: str, first: bool) -> None:
        """
        Search a hashtag within Instagram app.

        Parameters:
            text (str): Hashtag or search text.
            first (bool): If True, use first-run selector for search icon.
        """
        time.sleep(5)
        if first:
            search_button = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().resourceId("com.instagram.android:id/tab_icon").instance(2)',
            )
        else:
            search_button = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().resourceId("com.instagram.android:id/search_tab")',
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
            self.driver.press_keycode(66)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().resourceId("com.instagram.android:id/layout_container").instance(0)',
                    )
                )
            ).click()

        print(f"[Device {self.device_id}] Searching hashtag: {text}")

    def _get_clipboard_with_retry(self, max_attempts: int = 3, delay: int = 2) -> str:
        """
        Get clipboard text with a retry mechanism.

        Parameters:
            max_attempts (int): Number of retry attempts.
            delay (int): Delay in seconds between attempts.

        Returns:
            str: Clipboard text or empty string on failure.
        """
        for attempt in range(max_attempts):
            try:
                return self.driver.get_clipboard_text()
            except Exception as e:
                print(
                    f"[Device {self.device_id}] Attempt {attempt + 1}: Failed to get clipboard text: {str(e)}"
                )
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                else:
                    print(
                        f"[Device {self.device_id}] All attempts to get clipboard failed"
                    )
                    return ""

    def download_videos(self, save_directory: str, key: str) -> None:
        """
        Browse through videos, collect links and download videos meeting criteria.

        Parameters:
            save_directory (str): Directory where videos will be saved.
            key (str): Subfolder/key name used to store CSV and videos.
        """
        csv_path = os.getenv("CSV_PATH")
        key_folder = os.path.join(csv_path, key)
        os.makedirs(key_folder, exist_ok=True)

        full_path = os.path.join(key_folder, key + ".csv")

        with csv_lock:
            existing_links: Set[str] = set()
            last_id = -1

            if os.path.exists(full_path):
                df = pd.read_csv(full_path)
                existing_links.update(df["Link"])
                if "ID" in df.columns:
                    last_id = df["ID"].max()

        urls = pd.DataFrame(columns=["ID", "Link", "Views"])
        videos = 0
        cont = 0

        while cont < 100:
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

            if num_views > 40000:
                success, new_id = self._handle_video_download(
                    existing_links, urls, last_id, save_directory, key, num_views
                )

                if success:
                    last_id = new_id  # Update last_id with the new ID
                    cont += 1
                    print(
                        f"[Device {self.device_id}] Vídeo {cont} com mais de 100k views: {num_views} views - last_id: {last_id}"
                    )
                self._save_csv(full_path, urls, existing_links)
                self.driver.back()

            videos += 1
            self._swipe_to_next_video()

        self._save_csv(full_path, urls, existing_links)
        print(
            f"[Device {self.device_id}] Total de vídeos analisados: {videos}\nTotal de vídeos com mais de 100k views: {cont}"
        )

    def _handle_video_download(
        self,
        existing_links: Set[str],
        urls: pd.DataFrame,
        last_id: int,
        save_directory: str,
        key: str,
        num_views: int,
    ) -> Tuple[bool, int]:
        """
        Handle the process of copying a video's link, checking duplicates and downloading.

        Parameters:
            existing_links (Set[str]): Set of links already processed.
            urls (pd.DataFrame): DataFrame that accumulates new records.
            last_id (int): Last numeric ID used.
            save_directory (str): Directory to save downloads.
            key (str): Current key/subfolder name.
            num_views (int): Number of views for the current video.

        Returns:
            Tuple[bool, int]: (success, new_id). success True if download succeeded, new_id is updated ID.
        """
        try:
            share_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        AppiumBy.XPATH,
                        '//android.widget.ImageView[@content-desc="Share"]',
                    )
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

            link = self._get_clipboard_with_retry()

            if not link:
                return False, last_id

            if link in existing_links:
                print(f"[Device {self.device_id}] Link já existe: {link}")
                self.swipe_up()
                return False, last_id
            else:
                new_id = last_id + 1
                urls.loc[len(urls)] = [new_id, link, num_views]

                existing_links.add(link)

                download_success = self._download_video(link, save_directory, new_id)
                if download_success:
                    return True, new_id
                else:
                    urls.drop(urls[urls["Link"] == link].index, inplace=True)
                    return False, last_id

        except Exception as e:
            print(
                f"[Device {self.device_id}] Error in _handle_video_download: {str(e)}"
            )
            return False, last_id

    def _download_video(self, link: str, save_directory: str, last_id: int) -> bool:
        """
        Download a video/audio using yt_dlp.

        Parameters:
            link (str): URL to download.
            save_directory (str): Directory to store the downloaded file.
            last_id (int): Numeric id used in the output filename.

        Returns:
            bool: True if download was successful, False otherwise.
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
            print(f"[Device {self.device_id}] Successfully downloaded video: {link}")
            return True
        except youtube_dl.utils.DownloadError as e:
            print(f"[Device {self.device_id}] Error downloading video {link}: {str(e)}")
            return False

    def _swipe_to_next_video(self) -> None:
        """
        Swipe up to advance to the next video and wait a small delay.
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

    def _save_csv(
        self, csv_file_path: str, urls: pd.DataFrame, existing_links: Set[str]
    ) -> None:
        """
        Save the accumulated DataFrame to CSV, merging with existing file and ensuring schema.

        Parameters:
            csv_file_path (str): Destination CSV file path.
            urls (pd.DataFrame): New rows to add.
            existing_links (Set[str]): Set of existing links (not directly used here, but kept for consistency).
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
            print(f"[Device {self.device_id}] CSV saved: {csv_file_path}")


def process_device(
    device_id: str, appium_port: int, hashtags_to_process: Dict[str, List[str]]
) -> None:
    """
    Process a single device with specific hashtags.

    Parameters:
        device_id (str): Device identifier.
        appium_port (int): Appium server port for that device.
        hashtags_to_process (Dict[str, List[str]]): Mapping of key -> list of hashtags to process.
    """
    try:
        instagram_bot = InstagramAutomation(
            device_id=device_id, appium_port=appium_port
        )
        instagram_bot.open_instagram_app()
        time.sleep(5)

        save_directory = os.getenv("SAVE_DIRECTORY")

        for key, hashtags in hashtags_to_process.items():
            subfolder_path = os.path.join(save_directory, key)
            os.makedirs(subfolder_path, exist_ok=True)

            for hashtag in hashtags:
                instagram_bot.search_hashtag(hashtag, first=True)
                instagram_bot.download_videos(subfolder_path, key)

        print(f"[Device {device_id}] Process completed")
    except Exception as e:
        print(f"[Device {device_id}] Error in process_device: {str(e)}")


def distribute_hashtags(
    devices: List[Tuple[str, int]], hashtags_list: Dict[str, List[str]]
) -> Dict[str, Dict[str, List[str]]]:
    """
    Distribute hashtags evenly across devices.

    Parameters:
        devices (List[Tuple[str, int]]): List of (device_id, port) tuples.
        hashtags_list (Dict[str, List[str]]): Mapping of key -> list of hashtags.

    Returns:
        Dict[str, Dict[str, List[str]]]: Mapping of device_id -> (key -> list of hashtags).
    """
    device_hashtags: Dict[str, Dict[str, List[str]]] = {}
    device_count = len(devices)

    for device_id, _ in devices:
        device_hashtags[device_id] = {}

    device_index = 0
    for key, hashtags in hashtags_list.items():
        current_device = devices[device_index][0]

        device_hashtags[current_device][key] = hashtags

        device_index = (device_index + 1) % device_count

    return device_hashtags


def run_in_parallel(
    devices: List[Tuple[str, int]], hashtags_list: Dict[str, List[str]]
) -> None:
    """
    Run automation on multiple devices simultaneously.

    Parameters:
        devices (List[Tuple[str, int]]): List of (device_id, port) tuples.
        hashtags_list (Dict[str, List[str]]): Mapping of key -> list of hashtags.
    """
    device_hashtags = distribute_hashtags(devices, hashtags_list)

    threads: List[threading.Thread] = []
    for device_id, port in devices:
        thread = threading.Thread(
            target=process_device, args=(device_id, port, device_hashtags[device_id])
        )
        threads.append(thread)
        thread.start()
        print(f"Thread started for device {device_id}")

    for thread in threads:
        thread.join()


def main() -> None:
    """
    Entry point: define devices and hashtags and start parallel processing.
    """
    devices: List[Tuple[str, int]] = [
        ("RXCY201DBTA", 4724),
        ("RXCY20183JY", 4725),
    ]

    hashtags_list: Dict[str, List[str]] = {
        # "ansiedade": ["#ansiedade"],
        # "depressao": ["#depressao", "#transtornodepressivo"],
        # "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        # "TEA": ["#TEA", "#autismo", "#transtornodoespectroautista"],
        # "suicidio": ["#prevencaosuicidio"],
        "TBP": ["#TBP", "#bipolar"],
    }

    run_in_parallel(devices, hashtags_list)

    print("All processes completed")


if __name__ == "__main__":
    main()
