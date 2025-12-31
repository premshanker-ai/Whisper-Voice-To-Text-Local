import wave
import webrtcvad
import collections
import pyaudio
import threading

class AudioRecorder:
    def __init__(self, channels=1, rate=16000, chunk=1024, frame_duration_ms=30):
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.format = pyaudio.paInt16
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(self.rate * (self.frame_duration_ms / 1000.0))
        self.frames = []
        self.recording = False
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode from 0 to 3
        self.lock = threading.Lock()

    def start_recording(self):
        with self.lock:
            if self.recording:
                return
            self.frames = []
            try:
                self.stream = self.p.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk,
                    stream_callback=self._callback
                )
            except Exception as exc:
                print(f"Failed to start recording: {exc}")
                self.recording = False
                return
            self.recording = True
            self.stream.start_stream()

    def _callback(self, in_data, frame_count, time_info, status):
        with self.lock:
            if self.recording:
                self.frames.append(in_data)
            return (in_data, pyaudio.paContinue)

    def stop_recording(self, output_filename="output.wav"):
        with self.lock:
            if not self.recording:
                return None
                
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()

            # Voice Activity Detection (VAD)
            pcm_data = b''.join(self.frames)
            
        if not pcm_data:
            return None

        # VAD processing on raw 16-bit mono PCM
        frames = self.frame_generator(self.frame_duration_ms, pcm_data, self.rate)
        voiced_frames = []
        for frame in frames:
            is_speech = self.vad.is_speech(frame.bytes, self.rate)
            if is_speech:
                voiced_frames.append(frame)

        if not voiced_frames:
            return None

        # Save the processed audio
        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(f.bytes for f in voiced_frames))
            
        return output_filename

    def frame_generator(self, frame_duration_ms, audio, sample_rate):
        n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
        offset = 0
        timestamp = 0.0
        duration = (float(n) / sample_rate) / 2.0
        Frame = collections.namedtuple('Frame', 'bytes timestamp duration')
        while offset + n < len(audio):
            yield Frame(audio[offset:offset + n], timestamp, duration)
            timestamp += duration
            offset += n

    def __del__(self):
        self.p.terminate()

if __name__ == '__main__':
    # Example Usage
    import time

    recorder = AudioRecorder()
    print("Recording for 5 seconds...")
    recorder.start_recording()
    time.sleep(5)
    output_file = recorder.stop_recording("test_recording.wav")
    if output_file:
        print(f"Recording saved to {output_file}")
    else:
        print("No speech detected.")
