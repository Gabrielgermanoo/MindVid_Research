import os
import speech_recognition as sr
import pandas as pd
from speech_recognizer import SpeechRecognizer
import requests
import re


class AudioProcessor:
    def __init__(self, key):
        self.key = key
        self.recognizer = SpeechRecognizer()
        self.transcriptions_df = pd.DataFrame(
            columns=["ID", "Transcription", "Tag", "Link", "Views"]
        )

    def process_audio_file(self, file, link, count, views):
        """Process a single audio file: recognize speech and transcribe if recognized."""
        recognized_class = self.recognizer.recognize_speech(file)
        if recognized_class == "Speech":
            transcription = self.transcribe_audio(file)
            if transcription:
                self.transcriptions_df = pd.concat(
                    [
                        self.transcriptions_df,
                        pd.DataFrame(
                            {
                                "ID": [count],
                                "Transcription": [transcription],
                                "Tag": [self.key],
                                "Link": [link],
                                "Views": [views],
                            }
                        ),
                    ],
                    ignore_index=True,
                )

    @staticmethod
    def transcribe_audio(file) -> str:
        """Transcribe audio file to text using Google Web Speech API."""
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="pt-BR")
            print(f"Transcription: {text}")
            return text
        except Exception as e:
            print(f"Error transcribing {file}: {str(e)}")
            return None

    def save_transcriptions(self):
        """Save transcriptions to a CSV file."""
        csv_dir = "./CSV"
        os.makedirs(csv_dir, exist_ok=True)
        output_path = os.path.join(csv_dir, f"{self.key}_audio_transcriptions.csv")
        self.transcriptions_df.to_csv(output_path, index=False)
        print(f"✓ Transcriptions saved to: {output_path}")

    def process_all_files(self):
        csv_path = f"./CSV/{self.key}/{self.key}.csv"

        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return

        df = pd.read_csv(csv_path)

        if "Link" not in df.columns or "Views" not in df.columns:
            print("CSV missing required columns: Link, Views")
            return

        links = df[["Link", "Views"]].values.tolist()
        print(f"Found {len(links)} links for key: {self.key}")

        processed = 0
        skipped = 0

        for count, row in enumerate(links):
            link = row[0]
            views = row[1]
            video_id = None

            if "tiktok.com" in link:
                if "vt.tiktok.com" in link or "vm.tiktok.com" in link:
                    print(
                        f"[{count + 1}/{len(links)}] Resolving TikTok short link: {link}"
                    )
                    video_id = self.resolve_tiktok_shortlink(link)
                else:
                    # Link completo do TikTok
                    match = re.search(r"/video/(\d+)", link)
                    if match:
                        video_id = match.group(1)
                        print(
                            f"[{count + 1}/{len(links)}] Extracted video ID: {video_id}"
                        )
            else:
                # Link do Instagram
                parts = link.split("/")
                if len(parts) > 4:
                    video_id = parts[4]
                    print(
                        f"[{count + 1}/{len(links)}] Extracted Instagram ID: {video_id}"
                    )

            if not video_id:
                print(f"Could not extract video ID from: {link}")
                skipped += 1
                continue

            filename = f"{count}_{video_id}.wav"
            wav_file_name = os.path.join(f"../Videos/{self.key}", filename)

            if os.path.exists(wav_file_name):
                print(f"Processing audio: {filename}")
                self.process_audio_file(wav_file_name, link, count, views)
                processed += 1
            else:
                print(f"File not found: {wav_file_name}")
                skipped += 1

        print(f"\n{'=' * 60}")
        print(f"Processed: {processed} | Skipped: {skipped} | Total: {len(links)}")
        print(f"{'=' * 60}")
        self.save_transcriptions()

    def resolve_tiktok_shortlink(self, short_url):
        """Resolve TikTok short links to get video ID."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        try:
            # Primeira tentativa: seguir redirecionamentos normalmente
            resp = requests.get(
                short_url, headers=headers, allow_redirects=True, timeout=10
            )
            expanded_url = resp.url

            # Extrai video ID da URL final
            match = re.search(r"/video/(\d+)", expanded_url)
            if match:
                video_id = match.group(1)
                print(f"  ✓ Video ID: {video_id}")
                return video_id

            # Segunda tentativa: extrair do redirect_url se estiver na página de login
            match = re.search(r"redirect_url=([^&]+)", expanded_url)
            if match:
                import urllib.parse

                redirect_url = urllib.parse.unquote(match.group(1))
                print(f"Found redirect URL: {redirect_url}")

                match = re.search(r"/video/(\d+)", redirect_url)
                if match:
                    video_id = match.group(1)
                    print(f"Video ID from redirect: {video_id}")
                    return video_id

            print(f"No video ID found in: {expanded_url[:100]}...")

        except Exception as e:
            print(f"Error expanding {short_url}: {e}")

        return None


def main():
    hashtags_list = {
        # "ansiedade": ["#ansiedade", "#transtornodeansiedade"],
        # "depressao": ["#depressao", "#transtornodepressivo"],
        # "TDAH": ["#TDAH", "#transtornodedeficitdeatencaohiperatividade"],
        # "TEA": ["#TEA", "autismo", "#transtornodoespectroautista"],
        # "TEPT": ["#TEPT", "#transtornodeestressepostraumatico"],
        # "suicidio": ["#suicidio"]
        # "borderline": ["#borderline"]
        # "anorexia_homem": ["#anorexiahomem", "#anorexia"]
        "anorexia_mulher": ["#anorexiamulher", "#anorexia"]
    }

    print("=" * 60)
    print("Audio Processor Started")
    print("=" * 60)

    for key in hashtags_list.keys():
        print(f"\n{'=' * 60}")
        print(f"Processing category: {key}")
        print(f"{'=' * 60}")
        processor = AudioProcessor(key)
        processor.process_all_files()

    print("\n" + "=" * 60)
    print("Audio Processing Completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
