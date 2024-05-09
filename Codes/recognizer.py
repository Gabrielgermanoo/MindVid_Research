import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import csv
import scipy

from scipy.io import wavfile
import os

model = hub.load('https://tfhub.dev/google/yamnet/1')

def class_names_from_csv(class_map_csv_text):
    class_names = []
    with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            class_names.append(row['display_name'])
    return class_names

def ensure_sample_rate(original_sample_rate, waveform, desired_sample_rate=16000):
    if original_sample_rate != desired_sample_rate:
        desired_length = int(round(float(len(waveform)) / original_sample_rate * desired_sample_rate))
        waveform = scipy.signal.resample(waveform, desired_length)
    return desired_sample_rate, waveform


def SpeechRecognition(file):
    class_map_path = model.class_map_path().numpy()
    class_names = class_names_from_csv(class_map_path)
    wav_file_name = file
    sample_rate, wav_data = wavfile.read(wav_file_name, 'rb')
    # Convert stereo to mono by averaging the two channels
    if len(wav_data.shape) > 1 and wav_data.shape[1] > 1:
        wav_data = np.mean(wav_data, axis=1)
    sample_rate, wav_data = ensure_sample_rate(sample_rate, wav_data)
    duration = len(wav_data) * 1/sample_rate
    waveform = wav_data / tf.int16.max
    # print(f'Sample rate: {sample_rate} Hz')
    # print(f'Total duration: {duration:.2f} seconds')
    # print(f'size of wav_data: {len(wav_data)}')
    
    scores, embeddings, spectrogram = model(waveform)
    
    scores_np = scores.numpy()
    spectrogram_np = spectrogram.numpy()
    infered_class = class_names[scores_np.mean(axis=0).argmax()]
    print(f'The main sound is: {infered_class}')
    
    return infered_class