import os
import tkinter as tk
from tkinter import ttk, messagebox


class RecordingIndicator:
    def __init__(self, root, size=200):
        self.size = size
        self._transparent = "#010203"
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.configure(
            bg=self._transparent,
            highlightbackground="#FF4D4D",
            highlightthickness=3
        )
        try:
            self.window.attributes("-transparentcolor", self._transparent)
        except tk.TclError:
            pass

    def show_indicator(self):
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = (screen_w - self.size) // 2
        y = (screen_h - self.size) // 2
        self.window.geometry(f"{self.size}x{self.size}+{x}+{y}")
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()


class SettingsWindow(tk.Tk):
    def __init__(self, current_settings):
        super().__init__()
        self._callbacks = {
            "settings_changed": [],
            "restart_requested": [],
            "close": []
        }
        self._colors = {
            "bg": "#101216",
            "card": "#161A22",
            "text": "#E7EAF0",
            "muted": "#9AA3B2",
            "border": "#2A3242",
            "accent": "#4B7BEC",
            "accent_hover": "#5C8BFF",
            "button": "#222A3A",
            "button_hover": "#2C3648",
            "entry": "#11141B"
        }
        self.title("Super Whisper Settings")
        self.configure(bg=self._colors["bg"])
        self.geometry("520x520")
        self.minsize(480, 480)
        self._set_icon()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._init_styles()
        self._build_ui(current_settings)

    def _set_icon(self):
        icon_path = os.path.join(os.getcwd(), "icon.png")
        if os.path.exists(icon_path):
            try:
                icon = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, icon)
            except tk.TclError:
                pass

    def _init_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Dark.TCombobox",
            fieldbackground=self._colors["entry"],
            background=self._colors["entry"],
            foreground=self._colors["text"],
            bordercolor=self._colors["border"],
            arrowcolor=self._colors["text"]
        )
        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", self._colors["entry"])],
            foreground=[("readonly", self._colors["text"])],
            background=[("readonly", self._colors["entry"])]
        )

    def _build_ui(self, current_settings):
        pad_x = 18
        pad_y = 12

        container = tk.Frame(self, bg=self._colors["bg"])
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=self._colors["bg"], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=self._colors["bg"])
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_frame_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        content.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_scroll(_event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_scroll(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_scroll)
        canvas.bind("<Leave>", _unbind_scroll)

        header = tk.Frame(content, bg=self._colors["bg"])
        header.pack(fill="x", padx=pad_x, pady=(pad_y, 6))

        title = tk.Label(
            header,
            text="Super Whisper",
            fg=self._colors["text"],
            bg=self._colors["bg"],
            font=("Segoe UI", 16, "bold")
        )
        title.pack(anchor="w")
        subtitle = tk.Label(
            header,
            text="Tune transcription quality, hotkeys, and output behavior.",
            fg=self._colors["muted"],
            bg=self._colors["bg"],
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        self._section_label("MODEL", parent=content).pack(fill="x", padx=pad_x, pady=(10, 6))
        model_card = self._card(parent=content)
        model_card.pack(fill="x", padx=pad_x)
        model_body = tk.Frame(model_card, bg=self._colors["card"])
        model_body.pack(fill="x", padx=12, pady=12)

        tk.Label(
            model_body,
            text="Whisper Model Size",
            fg=self._colors["text"],
            bg=self._colors["card"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.model_var = tk.StringVar(
            value=current_settings.get("model_size", "base")
        )
        model_combo = ttk.Combobox(
            model_body,
            values=["tiny", "base", "small", "medium"],
            textvariable=self.model_var,
            style="Dark.TCombobox",
            state="readonly"
        )
        model_combo.pack(fill="x", pady=(6, 0))

        self._section_label("HOTKEY", parent=content).pack(fill="x", padx=pad_x, pady=(12, 6))
        hotkey_card = self._card(parent=content)
        hotkey_card.pack(fill="x", padx=pad_x)
        hotkey_body = tk.Frame(hotkey_card, bg=self._colors["card"])
        hotkey_body.pack(fill="x", padx=12, pady=12)

        tk.Label(
            hotkey_body,
            text="Global Hotkey",
            fg=self._colors["text"],
            bg=self._colors["card"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        self.hotkey_var = tk.StringVar(
            value=current_settings.get("hotkey", "<ctrl>+<shift>+v")
        )
        hotkey_entry = tk.Entry(
            hotkey_body,
            textvariable=self.hotkey_var,
            fg=self._colors["text"],
            bg=self._colors["entry"],
            insertbackground=self._colors["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self._colors["border"],
            highlightcolor=self._colors["accent"]
        )
        hotkey_entry.pack(fill="x", pady=(6, 0), ipady=6)

        tk.Label(
            hotkey_body,
            text="Examples: <ctrl>+<shift>+v, <space>+`, <cmd>+k",
            fg=self._colors["muted"],
            bg=self._colors["card"],
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(6, 0))

        self._section_label("BEHAVIOR", parent=content).pack(fill="x", padx=pad_x, pady=(12, 6))
        behavior_card = self._card(parent=content)
        behavior_card.pack(fill="x", padx=pad_x)
        behavior_body = tk.Frame(behavior_card, bg=self._colors["card"])
        behavior_body.pack(fill="x", padx=12, pady=12)

        self.sound_var = tk.BooleanVar(
            value=current_settings.get("play_sounds", True)
        )
        sound_toggle = tk.Checkbutton(
            behavior_body,
            text="Play a sound when recording starts and stops",
            variable=self.sound_var,
            fg=self._colors["text"],
            bg=self._colors["card"],
            activebackground=self._colors["card"],
            selectcolor=self._colors["card"]
        )
        sound_toggle.pack(anchor="w", pady=(0, 6))

        self.auto_paste_var = tk.BooleanVar(
            value=current_settings.get("auto_paste", True)
        )
        auto_paste = tk.Checkbutton(
            behavior_body,
            text="Auto-paste transcription into the active window",
            variable=self.auto_paste_var,
            fg=self._colors["text"],
            bg=self._colors["card"],
            activebackground=self._colors["card"],
            selectcolor=self._colors["card"]
        )
        auto_paste.pack(anchor="w")

        tk.Label(
            behavior_body,
            text="Transcription Language",
            fg=self._colors["text"],
            bg=self._colors["card"],
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(10, 0))

        language = current_settings.get("language")
        self.lang_var = tk.StringVar(value=language or "")
        lang_entry = tk.Entry(
            behavior_body,
            textvariable=self.lang_var,
            fg=self._colors["text"],
            bg=self._colors["entry"],
            insertbackground=self._colors["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self._colors["border"],
            highlightcolor=self._colors["accent"]
        )
        lang_entry.pack(fill="x", pady=(6, 0), ipady=6)

        footer = tk.Label(
            content,
            text="Hotkey and model changes take effect after restart.",
            fg=self._colors["muted"],
            bg=self._colors["bg"],
            font=("Segoe UI", 9)
        )
        footer.pack(anchor="w", padx=pad_x, pady=(10, 0))

        button_row = tk.Frame(content, bg=self._colors["bg"])
        button_row.pack(fill="x", padx=pad_x, pady=(12, 16))
        button_row.columnconfigure(0, weight=1)

        save_button = tk.Button(
            button_row,
            text="Save",
            command=self.save_settings,
            fg=self._colors["text"],
            bg=self._colors["button"],
            activebackground=self._colors["button_hover"],
            relief="flat",
            padx=16,
            pady=6
        )
        save_button.grid(row=0, column=1, padx=(0, 8))

        restart_button = tk.Button(
            button_row,
            text="Save and Restart",
            command=self.save_and_restart,
            fg=self._colors["text"],
            bg=self._colors["accent"],
            activebackground=self._colors["accent_hover"],
            relief="flat",
            padx=16,
            pady=6
        )
        restart_button.grid(row=0, column=2)

    def _section_label(self, text, parent=None):
        if parent is None:
            parent = self
        return tk.Label(
            parent,
            text=text,
            fg=self._colors["muted"],
            bg=self._colors["bg"],
            font=("Segoe UI", 9, "bold")
        )

    def _card(self, parent=None):
        if parent is None:
            parent = self
        return tk.Frame(
            parent,
            bg=self._colors["card"],
            highlightbackground=self._colors["border"],
            highlightthickness=1
        )

    def bind_settings_changed(self, callback):
        self._callbacks["settings_changed"].append(callback)

    def bind_restart_requested(self, callback):
        self._callbacks["restart_requested"].append(callback)

    def bind_close(self, callback):
        self._callbacks["close"].append(callback)

    def get_current_settings(self):
        language = self.lang_var.get().strip()
        if not language:
            language = None
        return {
            "model_size": self.model_var.get(),
            "hotkey": self.hotkey_var.get(),
            "auto_paste": self.auto_paste_var.get(),
            "play_sounds": self.sound_var.get(),
            "language": language
        }

    def save_settings(self):
        new_settings = self.get_current_settings()
        for callback in self._callbacks["settings_changed"]:
            callback(new_settings)

    def save_and_restart(self):
        new_settings = self.get_current_settings()
        for callback in self._callbacks["settings_changed"]:
            callback(new_settings)
        for callback in self._callbacks["restart_requested"]:
            callback()

    def show(self):
        self.deiconify()
        self.lift()

    def show_error(self, title, message):
        messagebox.showerror(title, message, parent=self)

    def _on_close(self):
        if self._callbacks["close"]:
            for callback in self._callbacks["close"]:
                callback()
        else:
            self.destroy()
