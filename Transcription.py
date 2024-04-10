import speech_recognition as sr

def audioTranscription(file):
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