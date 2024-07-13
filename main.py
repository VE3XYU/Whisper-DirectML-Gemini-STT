import pyaudio
import math
import struct
import wave
import time
import datetime
import os
from dotenv import load_dotenv
from whisper_transcriber import WhisperTranscriber
from cognxcore import CogniCore

load_dotenv()
class Recorder:
    def __init__(self, trigger_rms=10, rate=16000, timeout_secs=1, frame_secs=0.25, cushion_secs=1, directory='./'):
        self.TRIGGER_RMS = trigger_rms
        self.RATE = rate
        self.TIMEOUT_SECS = timeout_secs
        self.FRAME_SECS = frame_secs
        self.CUSHION_SECS = cushion_secs
        self.f_name_directory = directory

        self.SHORT_NORMALIZE = (1.0/32768.0)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.SHORT_WIDTH = 2
        self.CHUNK = int(self.RATE * self.FRAME_SECS)
        self.CUSHION_FRAMES = int(self.CUSHION_SECS / self.FRAME_SECS)
        self.TIMEOUT_FRAMES = int(self.TIMEOUT_SECS / self.FRAME_SECS)
        #This pyaudio automatically gets the default recording device
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=self.CHUNK)
                        #input_device_index=1  # You can also specify input device index here instead of default
        self.time = time.time()
        self.quiet = []
        self.quiet_idx = -1
        self.timeout = 0
#calculates the RMS value of an audio frame, returns in decibels
    def rms(self, frame):
        count = len(frame) / self.SHORT_WIDTH
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * self.SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000
#main recording loop
    def record(self):
        print('')
        sound = []
        start = time.time()
        begin_time = None
        while True:
            data = self.stream.read(self.CHUNK)
            rms_val = self.rms(data) #reads audio data from the stream in chunks and calculates the RMS value of each chunk.
                                        #If the RMS value exceeds the trigger threshold, it starts recording and sets a timeout period.
            if self.inSound(data):
                sound.append(data)
                if begin_time == None:
                    begin_time = datetime.datetime.now()
            else:
                if len(sound) > 0:
                    self.write(sound, begin_time)
                    sound.clear()
                    begin_time = None
                else:
                    self.queueQuiet(data)

            curr = time.time()
            secs = int(curr - start)
            tout = 0 if self.timeout == 0 else int(self.timeout - curr)
            label = 'Listening' if self.timeout == 0 else 'Recording'
            print('[+] %s: Level=[%4.2f] Secs=[%d] Timeout=[%d]' % (label, rms_val, secs, tout), end='\r')
        
    def queueQuiet(self, data): # The queueQuiet method adds quiet audio frames to a queue.
        self.quiet_idx += 1
        # start over again on overflow
        if self.quiet_idx == self.CUSHION_FRAMES:
            self.quiet_idx = 0
        
        # fill up the queue
        if len(self.quiet) < self.CUSHION_FRAMES:
            self.quiet.append(data)
        else:            
            self.quiet[self.quiet_idx] = data

    def dequeueQuiet(self, sound):
        if len(self.quiet) == 0:
            return sound
        
        ret = []
        
        if len(self.quiet) < self.CUSHION_FRAMES:
            ret.append(self.quiet)
            ret.extend(sound)
        else:
            ret.extend(self.quiet[self.quiet_idx + 1:])
            ret.extend(self.quiet[:self.quiet_idx + 1])
            ret.extend(sound)

        return ret
    
    def inSound(self, data):
        rms = self.rms(data)
        curr = time.time()

        if rms > self.TRIGGER_RMS:
            self.timeout = curr + self.TIMEOUT_SECS
            return True
        
        if curr < self.timeout:
            return True

        self.timeout = 0
        return False

    def write(self, sound, begin_time): #The write method writes the recorded audio to a file and transcribes it using the WhisperTranscriber
        sound = self.dequeueQuiet(sound)
        keep_frames = len(sound) - self.TIMEOUT_FRAMES + self.CUSHION_FRAMES
        recording = b''.join(sound[0:keep_frames])

        filename= "voice"
        pathname = os.path.join(self.f_name_directory, '{}.wav'.format(filename))

        wf = wave.open(pathname, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(recording)
        wf.close()
        print('[+] Saved: {}'.format(pathname))

        transcriber = WhisperTranscriber() #Transcribe using DML
        transcription = transcriber.transcribe_audio(pathname)
        print('[+] Transcription: {}'.format(transcription))

        ai = CogniCore(os.getenv("API_KEY"),config_file='config.json') #uses Gemini
        prompt = transcription
        response = ai.generate_content(prompt)
        print('[+] Response: {}'.format(response))
        

def main():
    recorder = Recorder()
    recorder.record()
    print(recorder)
    
if __name__ == "__main__":
    main()