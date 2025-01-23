# Whisper DirectML Wave Transcription
 
 This is a fork and conversion of https://github.com/Conradium/Whisper-DirectML-Gemini-STT
 
 This will convert pre-recorded audio (.WAV) to a .TXT file containing the transcription, using locally run Whisper DirectML (on Windows)

 Allows you to use Whisper without CUDA, or ROCm, or money (no API required)
 Utilizes torch_directML (chooses devices with DirectX12 compatibility).

Tested on python 3.10 with a Radeon RX570 8GB on Windows 10 Enterprise.  I'll test later on a 6800XT, but I expect it will work without issue.

## Installation

Ensure Python is installed, and on your PATH.

Install and initialize your virtual environment (venv)
Run Command Prompt as Administrator (PowerShell was giving me problems...) and ewnsure you're in the main project directory.

```bash
python -m pip install venv
python -m venv venv
```

Activate your venv

```bash
\venv\scripts\activate.bat
```
If you are using PowerShell, the above command would instead be activate.ps1

Install the requirements from requirements.txt

```bash
pip install -r requirements.txt
```

Install [ffmpeg](https://www.ffmpeg.org/download.html) on your computer and ensure it is on your PATH.

For the best result, and faster processing, convert all of your files to 16-bit WAV, 16000Hz, Mono.
It will still work with stereo 44.1KHz, but time will be lost as ffmpeg has to convert each chunk before passing to Whisper. This can be done with ffmpeg on the command line, or something like Audacity.

## Running

With your venv active, place your .WAV files in the wav_files/ directory.

```bash
python main.py
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
