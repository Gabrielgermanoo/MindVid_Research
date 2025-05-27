import os
import time
import pandas as pd
import threading
from dotenv import load_dotenv
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp as youtube_dl

# Global lock for CSV file access
csv_lock = threading.Lock()


class InstagramAutomation:
    def __init__(self, device_id="emulator-5554", appium_port=4723):
        self.device_id = device_id
        self.appium_port = appium_port
        self.driver = self._config_driver()

    def _config_driver(self):
        load_dotenv()
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

    def swipe_up(self, duration=800):
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = size["height"] // 2
        end_y = size["height"] // 4
        self.driver.swipe(start_x, start_y, start_x, end_y, duration)

    def find_instagram_app(self):
        return self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Instagram")'
        )

    def open_instagram_app(self):
        self.find_instagram_app().click()
        print(f"[Device {self.device_id}] Instagram app opened")

    def login(self):
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

    def is_link_in_csv(self, link, csv_file):
        df = pd.read_csv(csv_file)
        return df["Link"].str.contains(link).any()

    def search_hashtag(self, text, first):
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

    def _get_clipboard_with_retry(self, max_attempts=3, delay=2):
        """Get clipboard text with retry mechanism"""
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

    def download_videos(self, save_directory, key):
        csv_path = os.getenv("CSV_PATH")
        key_folder = os.path.join(csv_path, key)
        os.makedirs(key_folder, exist_ok=True)

        full_path = os.path.join(key_folder, key + ".csv")

        # Use lock when accessing shared file
        with csv_lock:
            existing_links = set()
            last_id = -1

            if os.path.exists(full_path):
                df = pd.read_csv(full_path)
                existing_links.update(df["Link"])
                if "ID" in df.columns:
                    last_id = df["ID"].max()

        urls = pd.DataFrame(columns=["ID", "Link"])
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

            if num_views > 100000:
                # Modified to use current_id instead of modifying last_id directly
                success, new_id = self._handle_video_download(
                    existing_links, urls, last_id, save_directory, key
                )

                if success:
                    last_id = new_id  # Update last_id with the new ID
                    cont += 1
                    print(
                        f"[Device {self.device_id}] Vídeo {cont} com mais de 100k views: {num_views} views - last_id: {last_id}"
                    )

                self.driver.back()

            videos += 1
            self._swipe_to_next_video()

        self._save_csv(full_path, urls, existing_links)
        print(
            f"[Device {self.device_id}] Total de vídeos analisados: {videos}\nTotal de vídeos com mais de 100k views: {cont}"
        )

    def _handle_video_download(
        self, existing_links, urls, last_id, save_directory, key
    ):
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

            # Use retry mechanism for clipboard
            link = self._get_clipboard_with_retry()

            if not link:  # If link is empty or None
                return False, last_id

            if link in existing_links:
                print(f"[Device {self.device_id}] Link já existe: {link}")
                self.swipe_up()
                return False, last_id
            else:
                new_id = last_id + 1
                urls.loc[len(urls)] = [new_id, link]

                # Add to existing_links to prevent duplicates within the same session
                existing_links.add(link)

                download_success = self._download_video(link, save_directory, new_id)
                if download_success:
                    return True, new_id
                else:
                    # If download fails, remove the entry from dataframe
                    urls.drop(urls[urls["Link"] == link].index, inplace=True)
                    return False, last_id

        except Exception as e:
            print(
                f"[Device {self.device_id}] Error in _handle_video_download: {str(e)}"
            )
            return False, last_id

    def _download_video(self, link, save_directory, last_id):
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

    def _swipe_to_next_video(self):
        size = self.driver.get_window_size()
        self.driver.swipe(
            size["width"] // 2,
            size["height"] * 3 // 4,
            size["width"] // 2,
            size["height"] // 4,
            1000,
        )
        time.sleep(3)

    def _save_csv(self, csv_file_path, urls, existing_links):
        with csv_lock:
            combined_df = pd.DataFrame()

            if os.path.exists(csv_file_path):
                existing_df = pd.read_csv(csv_file_path)
                combined_df = pd.concat([existing_df, urls], ignore_index=True)
            else:
                combined_df = urls

            combined_df.drop_duplicates(subset=["Link"], inplace=True)
            if not combined_df.empty and "ID" in combined_df.columns:
                combined_df["ID"] = combined_df["ID"].astype(int)

            combined_df = combined_df[["ID", "Link"]]

            combined_df.to_csv(csv_file_path, index=False, header=True)
            print(f"[Device {self.device_id}] CSV saved: {csv_file_path}")


def process_device(device_id, appium_port, hashtags_to_process):
    """Process a single device with specific hashtags"""
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


def distribute_hashtags(devices, hashtags_list):
    """Distribute hashtags evenly across devices"""
    device_hashtags = {}
    device_count = len(devices)

    # Initialize empty dictionaries for each device
    for device_id, _ in devices:
        device_hashtags[device_id] = {}

    # Distribute hashtags by round-robin
    device_index = 0
    for key, hashtags in hashtags_list.items():
        # Get current device ID
        current_device = devices[device_index][0]

        # Assign this hashtag to the current device
        device_hashtags[current_device][key] = hashtags

        # Move to next device
        device_index = (device_index + 1) % device_count

    return device_hashtags


def run_in_parallel(devices, hashtags_list):
    """Run automation on multiple devices simultaneously"""
    # Distribute hashtags among devices
    device_hashtags = distribute_hashtags(devices, hashtags_list)

    # Create and start threads
    threads = []
    for device_id, port in devices:
        thread = threading.Thread(
            target=process_device, args=(device_id, port, device_hashtags[device_id])
        )
        threads.append(thread)
        thread.start()
        print(f"Thread started for device {device_id}")

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


def main():
    # Define devices - can be emulators or physical devices
    devices = [
        ("RXCY20183EH", 4723),  # First physical device
        ("RXCY201DBTA", 4724),  # Second physical device
        # Second device
        # Add more devices as needed
    ]

    # Define hashtags to search
    hashtags_list = {
        "ansiedade": ["#ansiedade"],
        "depressao": ["#depressao", "#transtornodepressivo"],
        "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        "TEA": ["#TEA", "#autismo", "#transtornodoespectroautista"],
    }

    # Run in parallel
    run_in_parallel(devices, hashtags_list)

    print("All processes completed")


if __name__ == "__main__":
    main()
