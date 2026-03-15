#!/usr/bin/env python3
import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import queue
import json
import sys
import os

# ====================== CONFIG ======================
if len(sys.argv) > 1:
    config_path = sys.argv[1]
else:
    sys.exit(1)

try:
    with open(config_path, "r") as f:
        config = json.load(f)
except Exception as e:
    print(f"Could not load config: {e}")
    sys.exit(1)

TITLE = config.get("title", "System Tool")
BUTTON_TEXT = config.get("button_text", "Run Command")
COMMAND = config.get("command", ["echo", "No command defined in JSON"])
WORKING_DIR = config.get("working_dir")
SUCCESS_MSG = config.get("success_msg", "Finished successfully.")
SUCCESS_EXIT_CODES = config.get("success_exit_codes", [0])  # ← NEW: list of exit codes considered success
# ===================================================

class LiveUpdateWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE)
        self.attributes('-fullscreen', True)
        self.configure(bg="#1e1e1e")

        # Top button frame
        self.btn_frame = tk.Frame(self, bg="#1e1e1e")
        self.btn_frame.pack(fill="x", padx=20, pady=30)

        self.button = tk.Button(
            self.btn_frame,
            text=BUTTON_TEXT,
            font=("Arial", 42, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            relief="flat",
            padx=80,
            pady=40,
            command=self.start_command
        )
        self.button.pack(expand=True)

        # Live log area
        self.log = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("JetBrains Mono", 14),
            bg="#0d0d0d",
            fg="#00ff00",
            insertbackground="white"
        )
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Status textbox (small, always visible)
        self.status_text = tk.Text(
            self,
            height=2,
            font=("Arial", 16, "bold"),
            bg="#222222",
            fg="#cccccc",
            state="disabled",
            relief="flat",
            padx=10,
            pady=5
        )
        self.status_text.pack(fill="x", padx=20, pady=(0, 20))

        self.set_status("Ready", "#888888")

        self.output_queue = queue.Queue()
        self.running = False

        self.bind("<Escape>", lambda e: self.quit())

    def set_status(self, message, fg_color="#cccccc"):
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, message)
        self.status_text.configure(fg=fg_color)
        self.status_text.configure(state="disabled")

    def start_command(self):
        if self.running:
            return
        self.running = True
        self.button.config(text="Running...", state="disabled", bg="#f0ad4e")
        self.set_status("Running...", "#ffcc00")
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, f"→ Starting: {' '.join(COMMAND)}\n\n")
        self.log.see(tk.END)

        thread = threading.Thread(target=self.run_subprocess, daemon=True)
        thread.start()

        self.after(100, self.poll_queue)

    def run_subprocess(self):
        try:
            proc = subprocess.Popen(
                COMMAND,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=WORKING_DIR
            )

            for line in proc.stdout:
                self.output_queue.put(line)
            proc.wait()

            exit_code = proc.returncode
            self.output_queue.put(f"\nProcess finished with exit code {exit_code}\n")

            if exit_code in SUCCESS_EXIT_CODES:
                self.output_queue.put(f"=== SUCCESS ===\n{SUCCESS_MSG}\n")
            else:
                self.output_queue.put(f"=== FAILED (exit code {exit_code}) ===\n")

        except Exception as e:
            self.output_queue.put(f"\n=== ERROR ===\n{str(e)}\n")

    def poll_queue(self):
        while not self.output_queue.empty():
            line = self.output_queue.get()
            self.log.insert(tk.END, line)
            self.log.see(tk.END)

        if self.running:
            self.after(50, self.poll_queue)
        else:
            self.finish_command()

    def finish_command(self):
        self.running = False
        # The finish logic now lives in run_subprocess → status updated via queue
        self.button.config(
            text="Close Window",
            state="normal",
            bg="#d9534f",
            command=self.destroy
        )


if __name__ == "__main__":
    app = LiveUpdateWindow()
    app.mainloop()
