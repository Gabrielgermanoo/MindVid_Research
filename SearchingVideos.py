from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import yt_dlp as youtube_dl
from dotenv import load_dotenv
import pandas as pd
import time
import os

capabilities = dict(
    platformName='Android',
    automationName='uiautomator2',
    deviceName='emulator-5554',
    appPackage='com.android.settings',
    appActivity='.Settings',
    language='en',
    locale='US',
    noReset = True,
)

def __init__(self):
    self.driver = config()

def config():
    appium_server_url = 'http://localhost:4723'
    capabilities_options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(command_executor=appium_server_url,options=capabilities_options)

    return driver

def findInstagramApp(driver):
    # Find the Instagram app
    instagram_app = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Instagram")')
    return instagram_app

def openInstagramApp(driver):
    # Open the Instagram app
    instagram_app = findInstagramApp(driver)
    instagram_app.click()
    del instagram_app

def login(driver):
    load_dotenv()
    username_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((AppiumBy.XPATH, '(//android.widget.EditText)[1]')))
    username_field.clear()
    username_field.send_keys("")
    username_field.send_keys("INSTAGRAM_USERNAME")
    password_field = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((AppiumBy.XPATH, '(//android.widget.EditText)[2]')))
    password_field.send_keys("INSTAGRAM_PASSWORD")
    
    login_button = driver.find_element(AppiumBy.XPATH, "//android.widget.Button[@content-desc='Log in']/android.view.ViewGroup").click()

def searching(driver, text):
    # Procurar botão de pesquisa
    click_on_search = driver.find_element(AppiumBy.XPATH, '(//android.widget.ImageView[@resource-id="com.instagram.android:id/tab_icon"])[3]')
    click_on_search.click()
    del click_on_search
    search = driver.find_element(AppiumBy.XPATH, '//android.widget.EditText[@resource-id="com.instagram.android:id/action_bar_search_edit_text"]').click()
    search = driver.find_element(AppiumBy.XPATH, '//android.widget.EditText[@resource-id="com.instagram.android:id/action_bar_search_edit_text"]').clear()
    # Enviar texto para o campo de pesquisa
    search.send_keys(text)
    del search

    # Realizar a pesquisa clicando em "Search" -> Verificação de proteção de pesquisa por tópicos sensíveis
    try:
        search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((AppiumBy.XPATH, '//android.widget.Button[@resource-id="com.instagram.android:id/echo_text"]')))
        search_button.click()
        del search_button
        keep_searching_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/see_results_footer")))
        location = keep_searching_button.location
        size = keep_searching_button.size
        x = location['x'] + size['width'] - 1
        y = location['y'] + size['height'] - 1
        driver.tap([(x, y)])
        del keep_searching_button
    except TimeoutException:
        pass
    
    find_reels = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, '(//android.widget.ImageView[@resource-id="com.instagram.android:id/redesign_icon_image"])[1]')))
    find_reels.click()
    del find_reels

def downloading_videos(driver, save_directory, key):
    videos = 0
    cont = 0
    urls = pd.DataFrame(columns=[ 'ID','Link'])
    
    while cont < 100:
        try:
            likes = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, "//android.view.ViewGroup[contains(@content-desc, 'Like number is')]")))
            likes.click()
        except TimeoutException:
            try:
                likes = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, "//android.view.ViewGroup[contains(@content-desc, 'View likes')]")))
                likes.click()
            except TimeoutException:
                driver.swipe(500, 1500, 500, 500, 1000)
                continue
        del likes
        try:
            views_string = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.ID, "com.instagram.android:id/play_count_text")))
            num_views_string = views_string.text.split(" ")[0]
            remove_commas = num_views_string.replace(",", "")
            num_views = int(remove_commas)
            del views_string
        except TimeoutException:
            num_views = 0
        driver.back()
        if num_views > 100000:
            share_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.ImageView[@content-desc="Share"]')))
            share_button.click()
            del share_button
            copied_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, '//android.widget.TextView[@resource-id="com.instagram.android:id/label" and @text="Copy link"]'))).click()
            link = driver.get_clipboard_text()
            urls.loc[cont] = [cont, link]
            urls.to_csv(save_directory + '/' + key + '.csv', index=False)
            del copied_link
            ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': save_directory + '/' + str(cont) + '_%(id)s.%(ext)s',
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

            cont += 1
        videos += 1
        driver.swipe(500, 1500, 500, 500, 1000)

    print(f"Total de vídeos: {videos}"
        f"Total de vídeos com mais de 100k views: {cont}")

hashtags_list = {
    "ansiedade": ["#ansiedade", "#transtornodeansiedade"],
    "depressao": ["#depressao", "#transtornodepressivo"],
    "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
    "TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
}


def main():
    driver = config()
    time.sleep(5)
    openInstagramApp(driver)
    #login(driver)
    if os.path.exists('Videos') == False:
        os.mkdir('Videos')
        save_directory = "D:/Gabriel/UFAL/Pesquisa/fake_videos/Appium/Videos"
    else:
        save_directory = "D:/Gabriel/UFAL/Pesquisa/fake_videos/Appium/Videos"
    for key, value in hashtags_list.items():
        for hashtag in value:
            searching(driver, hashtag)
            if os.path.exists(save_directory + '/' + key) == False:
                os.mkdir(save_directory + '/' + key)
                save_directory = save_directory + '/' + key
            else:
                save_directory = save_directory + '/' + key
            downloading_videos(driver, save_directory, key)

if __name__ == '__main__':
    main()