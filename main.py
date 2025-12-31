import sys
import os
import json
import platform
import threading
import math
import tempfile
import wave
import pyperclip
from pynput import keyboard

try:
    import winsound
except ImportError:
    winsound = None

from recorder import AudioRecorder
from transcriber import Transcriber
from ui import SettingsWindow, RecordingIndicator


class Worker(threading.Thread):
    """
    Worker thread for transcription to avoid blocking the UI.
    """
    def __init__(self, transcriber, audio_path, language, on_done):
        super().__init__(daemon=True)
        self.transcriber = transcriber
        self.audio_path = audio_path
        self.language = language
        self.on_done = on_done

    def run(self):
        try:
            text = self.transcriber.transcribe(self.audio_path, self.language)
        except Exception as exc:
            print(f"Error during transcription: {exc}")
            text = ""
        self.on_done(text)


class SuperWhisperApp:
    def __init__(self):
        self.settings_file = "settings.json"
        self.load_settings()
        self._ensure_icon()
        self._sound_paths = {}

        self.settings_window = SettingsWindow(self.settings)
        self.settings_window.bind_settings_changed(self.handle_settings_change)
        self.settings_window.bind_restart_requested(self.restart_app)
        self.settings_window.bind_close(self.quit_app)

        self.recorder = AudioRecorder()
        self.transcriber = None
        self.indicator = RecordingIndicator(self.settings_window)

        self.is_recording = False
        self.hotkey_listener = None
        self.worker = None

        self.apply_settings(self.settings)
        self.start_hotkey_listener()

    def _ensure_icon(self):
        if os.path.exists("icon.png"):
            return
        try:
            from PIL import Image
        except ImportError:
            print("Pillow is not installed. Skipping icon creation.")
            return
        img = Image.new("RGB", (64, 64), color="blue")
        img.save("icon.png")

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "model_size": "base",
                "hotkey": "<ctrl>+<shift>+v",
                "auto_paste": True,
                "play_sounds": True,
                "language": "en"
            }

    def save_settings(self, new_settings):
        self.settings = new_settings
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def apply_settings(self, settings):
        current_model = settings.get("model_size", "base")
        if not self.transcriber or self.transcriber.model_size != current_model:
            print(f"Loading model: {current_model}")
            self.transcriber = Transcriber(model_size=current_model)
        self.settings = settings

    def start_hotkey_listener(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        hotkey_str = self.settings.get("hotkey", "<ctrl>+<shift>+v")
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({
                self.format_hotkey_for_pynput(hotkey_str): self.on_hotkey_activated
            })
            self.hotkey_listener.start()
            print(f"Hotkey '{hotkey_str}' is set.")
        except Exception as exc:
            message = f"Failed to set hotkey '{hotkey_str}': {exc}"
            print(message)
            self.settings_window.show_error("Hotkey Error", message)

    def format_hotkey_for_pynput(self, hotkey):
        hotkey = hotkey.lower()
        parts = hotkey.split("+")
        formatted_parts = []
        for part in parts:
            part = part.strip()
            if part in ["ctrl", "control"]:
                formatted_parts.append("<ctrl>")
            elif part in ["shift"]:
                formatted_parts.append("<shift>")
            elif part in ["alt", "option"]:
                formatted_parts.append("<alt>")
            elif part in ["cmd", "command"]:
                formatted_parts.append("<cmd>")
            else:
                formatted_parts.append(part)
        return "+".join(formatted_parts)

    def on_hotkey_activated(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_and_transcribe()

    def start_recording(self):
        print("Starting recording...")
        self.is_recording = True
        self.recorder.start_recording()
        self.indicator.show_indicator()
        if self.settings.get("play_sounds", True):
            self._play_sound("start")

    def stop_and_transcribe(self):
        print("Stopping recording...")
        self.is_recording = False
        self.indicator.hide()
        if self.settings.get("play_sounds", True):
            self._play_sound("stop")

        audio_file = self.recorder.stop_recording("temp_recording.wav")
        if not audio_file:
            print("No speech detected.")
            return

        print(f"Audio saved to {audio_file}. Transcribing...")
        self.worker = Worker(
            self.transcriber,
            audio_file,
            self.settings.get("language"),
            self._on_worker_done
        )
        self.worker.start()

    def _on_worker_done(self, text):
        self._schedule_ui(lambda: self.on_transcription_finished(text))

    def on_transcription_finished(self, text):
        if not text:
            print("Transcription was empty.")
            return

        print(f"Transcription: {text}")

        if self.settings.get("auto_paste", True):
            self.paste_text(text)
        else:
            pyperclip.copy(text)
            print("Copied to clipboard.")

    def paste_text(self, text):
        try:
            original_clipboard = pyperclip.paste()
        except pyperclip.PyperclipException:
            original_clipboard = ""

        pyperclip.copy(text)

        controller = keyboard.Controller()
        paste_key = keyboard.Key.ctrl
        if platform.system() == "Darwin":
            paste_key = keyboard.Key.cmd

        with controller.pressed(paste_key):
            controller.press("v")
            controller.release("v")

        self._schedule_ui(lambda: pyperclip.copy(original_clipboard), delay_ms=100)
        print("Pasted text and restored clipboard.")

    def handle_settings_change(self, new_settings):
        self.save_settings(new_settings)
        self.apply_settings(new_settings)

    def restart_app(self):
        print("Restarting application...")
        latest_settings = self.settings_window.get_current_settings()
        self.save_settings(latest_settings)

        if self.hotkey_listener:
            self.hotkey_listener.stop()

        self._schedule_ui(self._do_restart, delay_ms=100)

    def _do_restart(self):
        os.execl(sys.executable, sys.executable, *sys.argv)

    def quit_app(self):
        print("Quitting application.")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.settings_window.destroy()

    def _schedule_ui(self, func, delay_ms=0):
        if self.settings_window:
            self.settings_window.after(delay_ms, func)
        else:
            if delay_ms:
                timer = threading.Timer(delay_ms / 1000.0, func)
                timer.daemon = True
                timer.start()
            else:
                func()

    def _play_sound(self, kind):
        if winsound and os.name == "nt":
            path = self._ensure_sound_file(kind)
            if path:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            return
        try:
            self.settings_window.bell()
        except Exception:
            sys.stdout.write("\a")
            sys.stdout.flush()

    def _ensure_sound_file(self, kind):
        if kind in self._sound_paths and os.path.exists(self._sound_paths[kind]):
            return self._sound_paths[kind]

        filename = f"superwhisper_{kind}.wav"
        path = os.path.join(tempfile.gettempdir(), filename)
        if not os.path.exists(path):
            freqs = (523.25, 659.25) if kind == "start" else (392.0, 293.66)
            try:
                self._write_chime(path, freqs)
            except Exception as exc:
                print(f"Failed to write sound file: {exc}")
                return None
        self._sound_paths[kind] = path
        return path

    def _write_chime(self, path, freqs, duration=0.14, volume=0.4):
        sample_rate = 44100
        frames = int(sample_rate * duration)
        attack = 0.015
        release = 0.04
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for i in range(frames):
                t = i / sample_rate
                if t < attack:
                    env = t / attack
                elif t > duration - release:
                    env = max(0.0, (duration - t) / release)
                else:
                    env = 1.0
                sample = 0.0
                for freq in freqs:
                    sample += math.sin(2 * math.pi * freq * t)
                sample /= max(1, len(freqs))
                sample *= volume * env
                value = int(max(-1.0, min(1.0, sample)) * 32767)
                wf.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))

    def run(self):
        self.settings_window.show()
        self.settings_window.mainloop()


if __name__ == "__main__":
    app = SuperWhisperApp()
    app.run()
