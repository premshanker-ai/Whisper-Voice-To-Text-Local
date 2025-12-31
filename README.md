# Super Whisper Clone

This application is a cross-platform desktop tool that allows you to record your voice using a global hotkey and have the transcribed text pasted into your active window.

## Features

-   **Global Hotkey:** Start and stop recording from anywhere in your OS.
-   **Local Transcription:** Uses `faster-whisper` for fast and private transcription.
-   **Automatic Pasting:** Transcribed text is automatically pasted into your current application.
-   **System Tray Integration:** Runs discreetly in your system tray.
-   **Configurable Settings:** Change the model size, hotkey, and more.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.10+
    *   FFmpeg: `faster-whisper` requires FFmpeg to be installed on your system. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html). Make sure it's in your system's PATH.
    *   PortAudio (for PyAudio): On Windows you can use the pre-built wheels linked below. On macOS, install it with Homebrew: `brew install portaudio`. Linux package managers usually provide it as `portaudio`.

2.  **Install Dependencies:**
    Open a terminal or command prompt, navigate to the project directory, and install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    **Note on PyAudio:** If you encounter issues installing `PyAudio` on Windows, you might need to install it from a pre-compiled wheel. You can find wheels at the [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) page.

    **GUI Note:** The settings window uses Tk (included with Python), so there is no extra GUI dependency to install.

    **Note on CUDA:** If you have an NVIDIA GPU, you can get a significant performance boost. Make sure you have the CUDA Toolkit installed, and then install the CUDA-enabled version of PyTorch by following the instructions on the [PyTorch website](https://pytorch.org/). `faster-whisper` will automatically detect and use it.

## How to Run

1.  Navigate to the project directory in your terminal.
2.  Run the main application:
    ```bash
    python main.py
    ```
3.  The application icon will appear in your system tray.

## How to Use

1.  Press the global hotkey (default: `Ctrl+Shift+V`) to start recording. You will see a red border overlay on your screen.
2.  Press the hotkey again to stop recording.
3.  The recorded audio will be transcribed, and the text will be pasted into the currently active window.

## Settings

Right-click the system tray icon and select "Settings" to open the settings window. You can configure:

-   **Whisper Model:** The size of the model to use. Smaller models are faster but less accurate.
-   **Global Hotkey:** The key combination to trigger recording. The format for `pynput` should be used (e.g., `<ctrl>+<shift>+v`).
-   **Auto-paste:** Toggle whether to paste the text automatically or just copy it to the clipboard.
-   **Language:** The language of the transcription (e.g., 'en', 'es'). Leave blank for auto-detection.

**Important:** You will need to restart the application for changes to the hotkey and model to take effect. The "Save and Restart" button will do this for you.

**Note on macOS:** The application will use `Cmd+V` for pasting, while on Windows and Linux it will use `Ctrl+V`. The hotkey itself can be configured in the settings.
