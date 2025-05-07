# This sample code supports Appium Python client >=2.3.0
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python

from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import yt_dlp as youtube_dl
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
        
   
    def _initialize(self):
        print('initialize')
        pd.options.display.max_rows = 9999
        options = AppiumOptions()
        options.load_capabilities({
        "appium:automationName": "UiAutomator2",
        "appium:platformName": "Android",
        "appium:platformVersion": "14",
        "appium:deviceName": "emulator-5554",
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
        el1 = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/or6")
        el1.click()
        el2 = self.driver.find_element(by=AppiumBy.ACCESSIBILITY_ID, value="Copy link")
        el2.click()
        link=self.driver.get_clipboard_text()
        return link
    
    def checkViews(self):
        print('check views')
        el1 = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/dt6")
        print(el1.text)
        if 'K' in el1.text:
            return True
        if 'M' in el1.text:
            return True
        return False

    def DownLoadVideos(self,key,videoCount,path):
        time.sleep(2)
        full_path =path+'/'+key+'.csv'
        existing_links = set()
        

        if os.path.exists(full_path):
            df = pd.read_csv(full_path)
            existing_links.update(df['Link'])

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
            go_to_search_button= self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/gll")
            go_to_search_button.click()

        else:
            print('second')
            go_to_search_button = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/jd6")
            go_to_search_button.click()

        print('type')

        time.sleep(2)
        search_field= self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/eu9")
        search_field.send_keys(text)


        print('search')
        search_button = self.driver.find_element(by=AppiumBy.ID, value="com.zhiliaoapp.musically:id/skb")
        search_button.click()
        time.sleep(2)
        
        first_video = self.driver.find_element(by=AppiumBy.ANDROID_UIAUTOMATOR, value="new UiSelector().resourceId(\"com.zhiliaoapp.musically:id/qrh\").instance(0)")
        first_video.click()



def _download_video(link,key,path):
    print(link)
    ydl_opts = {
        'format': 'bestaudio/best',
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
        # "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        # "TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
    }
    save_directory = '/Users/victorferro/Documents/mind_research/'
    for key, value in hashtags_list.items():
        subfolder_path = os.path.join(save_directory, key)
        os.makedirs(subfolder_path, exist_ok=True)
        for hashtag in value:
            tikTokBot.searchHastag(hashtag,isFirst=isFirst)
            isFirst=False
            tikTokBot.DownLoadVideos(key=key,videoCount=10,path=save_directory)

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