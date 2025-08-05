import os
import speech_recognition as sr
import pandas as pd
from speech_recognizer import SpeechRecognizer

class AudioProcessor:
    def __init__(self, key):
        self.key = key
        self.recognizer = SpeechRecognizer()
        self.transcriptions_df = pd.DataFrame(columns=['ID', 'Transcription', 'Tag', 'Link', 'Views'])

    def process_audio_file(self, file, link, count, views):
        """Process a single audio file: recognize speech and transcribe if recognized."""
        recognized_class = self.recognizer.recognize_speech(file)
        if recognized_class == "Speech":
            transcription = self.transcribe_audio(file)
            if transcription:
                self.transcriptions_df = pd.concat([self.transcriptions_df, pd.DataFrame({
                    'ID': [count],
                    'Transcription': [transcription],
                    'Tag': [self.key],
                    'Link': [link],
                    'Views': [views]
                })])

    @staticmethod
    def transcribe_audio(file) -> str:
        """Transcribe audio file to text using Google Web Speech API."""
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
        """Save transcriptions to a CSV file."""
        output_path = f'./CSV/{self.key}_audio_transcriptions.csv'
        self.transcriptions_df.to_csv(output_path, index=False)

    def process_all_files(self):
        """Process all audio files for the given key."""
        links = pd.read_csv(f'./CSV/{self.key}/{self.key}.csv')[['Link', 'Views']].values.tolist()
        for count, row in enumerate(links):
            link = row[0]
            views = row[1]
            video_id = link.split('/')[4]
            filename = f'{count}_{video_id}.wav'
            wav_file_name = os.path.join(f'./Videos/{self.key}', filename)
            if os.path.exists(wav_file_name):
                self.process_audio_file(wav_file_name, link, count, views)
        self.save_transcriptions()

def main():
    hashtags_list = {
        #"ansiedade": ["#ansiedade", "#transtornodeansiedade"],
        #"depressao": ["#depressao", "#transtornodepressivo"],
        #"TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        #"TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
        "TEPT": ["#TEPT", "#transtornodeestressepostraumatico"],
        #"suicidio": ["#suicidio"]
    }

    for key in hashtags_list.keys():
        processor = AudioProcessor(key)
        processor.process_all_files()

if __name__ == '__main__':
    main()
