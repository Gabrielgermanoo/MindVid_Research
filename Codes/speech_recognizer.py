import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import csv
import scipy
from scipy.io import wavfile
import os


class SpeechRecognizer:
    def __init__(self, model_url="https://tfhub.dev/google/yamnet/1"):
        self.model = hub.load(model_url)
        self.class_names = self._load_class_names()

    def _load_class_names(self):
        """Load class names from the model's class map."""
        class_map_path = self.model.class_map_path().numpy()
        return self._class_names_from_csv(class_map_path)

    @staticmethod
    def _class_names_from_csv(class_map_csv_path) -> list:
        """Load class names from a CSV file."""
        class_names = []
        with tf.io.gfile.GFile(class_map_csv_path) as csvfile:
            reader = csv.DictReader(csvfile)
            class_names = [row["display_name"] for row in reader]
        return class_names

    @staticmethod
    def _ensure_sample_rate(original_sample_rate, waveform, desired_sample_rate=16000) -> tuple:
        """Ensure the waveform is at the desired sample rate."""
        if original_sample_rate != desired_sample_rate:
            desired_length = int(
                round(float(len(waveform)) / original_sample_rate * desired_sample_rate)
            )
            waveform = scipy.signal.resample(waveform, desired_length)
        return desired_sample_rate, waveform

    def recognize_speech(self, file) -> str:
        """Recognize speech in an audio file and return the inferred class."""
        sample_rate, wav_data = wavfile.read(file, "rb")

        if wav_data.ndim > 1:  # Convert stereo to mono if necessary
            wav_data = np.mean(wav_data, axis=1)

        sample_rate, wav_data = self._ensure_sample_rate(sample_rate, wav_data)
        waveform = wav_data / tf.int16.max

        scores, _, _ = self.model(waveform)
        scores_np = scores.numpy()

        inferred_class = self.class_names[scores_np.mean(axis=0).argmax()]
        print(f"The main sound is: {inferred_class}")
        return inferred_class
