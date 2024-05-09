import os
import speech_recognition as sr
from recognizer import SpeechRecognition
import pandas as pd

def audioTranscription(file):
    rec = SpeechRecognition(file)
    if rec == "Speech":
        print("Passou!")
        # Initialize recognizer
        r = sr.Recognizer()

        # Load audio file
        with sr.AudioFile(file) as source:
            audio = r.record(source)

        # Transcribe audio file
        try:
            text = r.recognize_google(audio, language='pt-BR')
            print("Transcription: " + text)
        except Exception as e:
            print("Error: " + str(e))
            text = None

        return text
    else:
        return False

def initRecognizer(key):
    cont = 0
    df = pd.DataFrame(columns=['ID', 'Transcription', 'tag'])
    for dirpath, dirname, filenames in os.walk(f'./Videos/{key}'):
        for filename in filenames:
            if filename.endswith('.wav'):
                wav_file_name = os.path.join(dirpath, filename)
                transcription = audioTranscription(wav_file_name)
                if transcription is not False:
                    df = pd.concat([df, pd.DataFrame({'ID': [cont], 'Transcription': [transcription], 'tag': [key]})])
                    cont += 1
    df = df.to_csv(f'./Videos/{key}_audio_transcriptions.csv', index=False)

def main():
    hashtags_list = {
        "ansiedade": ["#ansiedade", "#transtornodeansiedade"],
        "depressao": ["#depressao", "#transtornodepressivo"],
        "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        "TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
    }
    for key, value in hashtags_list.items():
        initRecognizer(key)

if __name__ == '__main__':
    main()