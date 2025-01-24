import whisper
import torch_directml

class WhisperTranscriber:
    def __init__(self, model_size="small", fp16=False, use_dml_attn=False):
        self.device = torch_directml.device(torch_directml.default_device())
        self.model = whisper.load_model(model_size, device=self.device, use_dml_attn=use_dml_attn)
        self.model_size = model_size
        self.fp16 = fp16

    def transcribe_audio(self, input_file):
        # Load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(input_file)
        audio = whisper.pad_or_trim(audio)
        
        n_mels = 80
        if self.model_size == "large-v3":
            n_mels = 128

        mel = whisper.log_mel_spectrogram(audio, n_mels=n_mels).to(self.model.device)
        language = "zh"
     #   if "en" not in self.model_size:
     #       _, probs = self.model.detect_language(mel)
     #       language = max(probs, key=probs.get)
        print(f"Forced language: {language}")

        options = whisper.DecodingOptions(language=language, fp16=self.fp16)
        result = whisper.decode(self.model, mel, options)
        
        return result.text