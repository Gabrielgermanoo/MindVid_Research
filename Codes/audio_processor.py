import os
import speech_recognition as sr
import pandas as pd
from speech_recognizer import SpeechRecognizer  # Supondo que o código anterior foi salvo como speech_recognizer.py

class AudioProcessor:
    def __init__(self, key):
        self.key = key
        self.recognizer = SpeechRecognizer()
        self.transcriptions_df = pd.DataFrame(columns=['ID', 'Transcription', 'Tag', 'Link'])

    def process_audio_file(self, file, link, count):
        recognized_class = self.recognizer.recognize_speech(file)
        if recognized_class == "Speech":
            transcription = self.transcribe_audio(file)
            if transcription:
                self.transcriptions_df = pd.concat([self.transcriptions_df, pd.DataFrame({
                    'ID': [count],
                    'Transcription': [transcription],
                    'Tag': [self.key],
                    'Link': [link]
                })])

    @staticmethod
    def transcribe_audio(file):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='pt-BR')
            print(f"Transcription: {text}")
            return text
        except Exception as e:
            print(f"Error transcribing {file}: {str(e)}")
            return None

    def save_transcriptions(self):
        output_path = f'./CSV/{self.key}_audio_transcriptions.csv'
        self.transcriptions_df.to_csv(output_path, index=False)

    def process_all_files(self):
        links = pd.read_csv(f'./CSV/{self.key}/{self.key}.csv')['Link']
        for count, link in enumerate(links):
            video_id = link.split('/')[4]
            filename = f'{count}_{video_id}.wav'
            wav_file_name = os.path.join(f'./Videos/{self.key}', filename)
            if os.path.exists(wav_file_name):
                self.process_audio_file(wav_file_name, link, count)
        self.save_transcriptions()

def main():
    hashtags_list = {
        #"ansiedade": ["#ansiedade", "#transtornodeansiedade"],
        "depressao": ["#depressao", "#transtornodepressivo"],
        #"TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        #"TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
    }

    for key in hashtags_list.keys():
        processor = AudioProcessor(key)
        processor.process_all_files()

if __name__ == '__main__':
    main()
