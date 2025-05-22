# This sample code supports Appium Python client >=2.3.0
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python

from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import yt_dlp as youtube_dl
from dotenv import load_dotenv
import  os
import time
import pandas as pd

# For W3C actions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

class TikTokAutomation:
    def __init__(self):
        self.driver = self._initialize()
        load_dotenv()
        
   
    def _initialize(self):
        print('initialize')
        pd.options.display.max_rows = 9999
        options = AppiumOptions()
        options.load_capabilities({
        "appium:automationName": "UiAutomator2",
        "appium:platformName": "Android",
        "appium:platformVersion": "10",
        "appium:deviceName": "moto e(7) power",
        "appium:newCommandTimeout": 3600,
        "appium:connectHardwareKeyboard": True
    })

        return webdriver.Remote("http://127.0.0.1:4723", options=options)
    
    def openTikTok(self):
        print('open_tik_tok')
        el1 =self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="TikTok")
        el1.click()
    
    def scrollDown(self):
        size = self.driver.get_window_size()
        self.driver.swipe(size['width'] // 2, size['height'] * 3 // 4, size['width'] // 2, size['height'] // 4, 1000)
    
    def getLink(self):
        print('getLink')
        el1 = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/pk_")
        el1.click()
        time.sleep(2)
        print("copy link")
        el2 = self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value="new UiSelector().resourceId(\"com.zhiliaoapp.musically:id/pk2\").instance(0)")
        el2.click()
        print("get clipboard")
        link=self.driver.get_clipboard_text()
        return link
    
    def checkViews(self):
        print('check likes')
        el1 = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/e2q")
        print(el1.text)
        if 'K' in el1.text:
            return True
        if 'M' in el1.text:
            return True
        if 'mi' in el1.text:
            return True
        return False

    def DownLoadVideos(self,key,videoCount,path):
        time.sleep(2)
        full_path =path+'/'+key+'.csv'
        existing_links = set()
        

        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            existing_links.update(df['link'])

        cont = 0
        print(existing_links)
        
    
        while cont<videoCount:
            try:
                shouldSave= self.checkViews()
            except:
                self.scrollDown()
                time.sleep(2)
                shouldSave=self.checkViews() 

            if shouldSave:
                    link=self.getLink()
                    if link not in existing_links:
                        shouldCount=_download_video(link=link,key=key,path=path)
                        if shouldCount:
                            cont+=1
            self.scrollDown()
            time.sleep(2)
    
    def searchHastag(self,text,isFirst):
        time.sleep(2)
        print('search_hashtag')

        if isFirst:
         
            print('first')
            go_to_search_button= self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value="new UiSelector().resourceId(\"com.zhiliaoapp.musically:id/h0i\").instance(1)")
            go_to_search_button.click()

        else:
            print('second')
            go_to_search_button = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/tjy")
            go_to_search_button.click()

        print('type')

        time.sleep(2)
        search_field= self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/f5t")
        search_field.send_keys(text)


        print('search')
        search_button = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/tk1")
        search_button.click()
        time.sleep(2)
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.w3c_actions.pointer_action.move_to_location(199, 584)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()
        
        



def _download_video(link,key,path):
    print(link)
    ydl_opts = {
        'format': 'bestaudio/best',
        'cookiesfrombrowser': ('chrome',),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(path+key, f'{1}_%(id)s.%(ext)s'),
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        saveCsv(key=key,path=path,link=link)
        return True
        
    except youtube_dl.utils.DownloadError:
        print(f"Erro ao baixar o vídeo {link}")
        return False
    
    


def main():
    tikTokBot=TikTokAutomation()
    # tikTokBot.openTikTok()


    isFirst=True
    hashtags_list = {
        "ansiedade": ["#ansiedade",],
        "depressao": ["#depressao"],
        "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        "TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
    }
    save_directory = os.getenv("save_directory")
    for key, value in hashtags_list.items():
        subfolder_path = os.path.join(save_directory, key)
        os.makedirs(subfolder_path, exist_ok=True)
        for hashtag in value:
            tikTokBot.searchHastag(hashtag,isFirst=isFirst)
            isFirst=False
            tikTokBot.DownLoadVideos(key=key,videoCount=1,path=save_directory)

    tikTokBot.driver.quit()


def saveCsv(key,path,link):
    fullPath=path+'/'+key+'.csv'
    pathExists=os.path.exists(fullPath)
    if pathExists:
        d = pd.read_csv(fullPath)
    else:   
        d=pd.DataFrame({'id': [1], 'link': [link],})

    df = pd.DataFrame(data=d)
    if pathExists:
        newIndex=int(df['id'].iloc[-1])+1
        df.loc[len(df)] = [newIndex, link]
        
    df.drop_duplicates(subset=['link'] , keep='first',inplace=True)
    

    df.to_csv(fullPath,index=False)
    print(df)



if __name__ == '__main__':
    main()