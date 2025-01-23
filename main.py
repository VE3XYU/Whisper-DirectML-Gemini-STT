import os
import wave
from dotenv import load_dotenv
from whisper_transcriber import WhisperTranscriber

load_dotenv()

class WAVProcessor:
    def __init__(self, directory='./'):
        self.f_name_directory = directory
        self.transcriber = WhisperTranscriber()

    def process_wav_file(self, filename):
        pathname = os.path.join(self.f_name_directory, filename)

        if not os.path.exists(pathname):
            print(f"[!] File not found: {pathname}")
            return

        # Open WAV file to get its duration
        with wave.open(pathname, 'rb') as wav_file:
            frame_rate = wav_file.getframerate()
            num_frames = wav_file.getnframes()
            duration = num_frames / frame_rate  # Total duration in seconds
            print(f"[+] Processing file: {pathname} ({duration:.2f} seconds)")

        chunk_duration = 30  # 30 second chunkss
        chunk_count = 0
        full_transcription = ""

        while True:
            start_time = chunk_count * chunk_duration
            end_time = min(start_time + chunk_duration, duration)

            if start_time >= duration:
                print("[+] Reached end of file. Stopping processing.")
                break

            chunk_file = f"{pathname.replace('.wav', '')}_chunk_{chunk_count}.wav"

            ffmpeg_cmd = (
                f'ffmpeg -i "{pathname}" -ss {start_time} -to {end_time} '
                f'-ac 1 -ar 16000 "{chunk_file}" -y -loglevel error'
            )

            os.system(ffmpeg_cmd)

            # ensure chunk exists and has content
            if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) == 0:
                print(f"[+] No more audio left after {chunk_count} chunks. Ending.")
                break

            transcription = self.transcriber.transcribe_audio(chunk_file)
            full_transcription += transcription + " "

            # clean up chunked file after processing
            os.remove(chunk_file)

            chunk_count += 1

        # save to txt
        output_txt = pathname.replace('.wav', '_transcription.txt')
        with open(output_txt, 'w') as f:
            f.write(full_transcription.strip())

        print(f'[+] Transcription saved to: {output_txt}')

    def process_directory(self):
        """Process all WAV files in the specified directory."""
        for filename in os.listdir(self.f_name_directory):
            if filename.lower().endswith('.wav'):
                self.process_wav_file(filename)

def main():
    processor = WAVProcessor(directory='./wav_files')
    processor.process_directory()

if __name__ == "__main__":
    main()
