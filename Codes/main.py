import instagram_automation as ia
import audio_processor as ap
import os, time

def main():
    instagram_bot = ia.InstagramAutomation()
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
    
    for key in hashtags_list.keys():
        processor = ap.AudioProcessor(key)
        processor.process_all_files()
        
if __name__ == '__main__':
    main()