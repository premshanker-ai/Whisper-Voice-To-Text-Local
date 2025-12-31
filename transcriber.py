from faster_whisper import WhisperModel
import torch

class Transcriber:
    def __init__(self, model_size="base", device="auto", compute_type="default"):
        """
        Initializes the Transcriber with a Whisper model.

        Args:
            model_size (str): The size of the Whisper model to use (e.g., "tiny", "base", "small").
            device (str): The device to run the model on ("auto", "cpu", "cuda").
            compute_type (str): The compute type for the model ("default", "int8", "float16").
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        if self.device == "cuda" and compute_type == "default":
            self.compute_type = "float16" # Use float16 for better performance on CUDA
        else:
            self.compute_type = compute_type

        self.model_size = model_size
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)

    def transcribe(self, audio_path, language=None):
        """
        Transcribes an audio file.

        Args:
            audio_path (str): The path to the audio file to transcribe.
            language (str, optional): The language of the audio. If None, it will be auto-detected.

        Returns:
            str: The transcribed text.
        """
        segments, info = self.model.transcribe(audio_path, beam_size=5, language=language)

        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        transcription = "".join(segment.text for segment in segments)
        return transcription.strip()

    def change_model(self, model_size):
        """
        Changes the loaded Whisper model.
        """
        self.model_size = model_size
        self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)


if __name__ == '__main__':
    # Example Usage
    # Create a dummy audio file for testing
    import soundfile as sf
    import numpy as np

    samplerate = 16000
    duration = 3
    frequency = 440
    t = np.linspace(0., duration, int(samplerate * duration), endpoint=False)
    amplitude = np.iinfo(np.int16).max * 0.5
    data = amplitude * np.sin(2. * np.pi * frequency * t)
    
    dummy_audio_path = "dummy_audio.wav"
    sf.write(dummy_audio_path, data.astype(np.int16), samplerate)

    print("Initializing transcriber...")
    transcriber = Transcriber(model_size="base")
    
    print(f"Transcribing {dummy_audio_path}...")
    text = transcriber.transcribe(dummy_audio_path)
    print(f"Transcription: {text}")

    # Example with a real recording (assuming you have one from recorder.py)
    # real_audio_path = "test_recording.wav" 
    # if os.path.exists(real_audio_path):
    #     print(f"Transcribing {real_audio_path}...")
    #     text = transcriber.transcribe(real_audio_path)
    #     print(f"Transcription: {text}")

