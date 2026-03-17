#!/usr/bin/env python3
import json
import os
import subprocess

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio
import sys
import threading
import time

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

def load_config():
    if len(sys.argv) < 2:
        print("Usage: python3 tv_control.py <config.json>")
        sys.exit(1)

    config_path = sys.argv[1]
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Could not load config file '{config_path}': {e}")
        sys.exit(1)

    # Extract values with sensible defaults
    return {
        "title": config.get("title", "System Tool"),
        "button_text": config.get("button_text", "RUN"),
        "stop_text": config.get("stop_text", "STOP"),
        "command": config.get("command", ["echo", "No command defined in JSON"]),
        "working_dir": config.get("working_dir", None),
        "success_msg": config.get("success_msg", "Process finished successfully ✓"),
        "success_exit_codes": config.get("success_exit_codes", [0]),
        "description": config.get("description",
            "Press RUN to start the process. Press STOP to interrupt."),
    }

class TVAppWindow(Gtk.ApplicationWindow):
    def __init__(self, app, config):
        super().__init__(application=app)
        self.config = config
        self.set_title(self.config["title"])

        # Main vertical container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_hexpand(True)
        main_box.set_vexpand(True)

        # ── Big RUN button area (top) ──
        button_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        button_area.set_hexpand(True)
        button_area.set_vexpand(False)
        button_area.set_valign(Gtk.Align.CENTER)
        button_area.set_margin_top(60)
        button_area.set_margin_bottom(20)

        self.run_button = Gtk.Button(label=self.config["button_text"])
        self.run_button.add_css_class("run-button")
        self.run_button.set_halign(Gtk.Align.CENTER)
        self.run_button.set_hexpand(False)
        self.run_button.connect("clicked", self.on_run_clicked)
        button_area.append(self.run_button)

        # ── Description / instruction line ──
        description_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        description_area.set_hexpand(True)
        description_area.set_vexpand(False)
        description_area.set_valign(Gtk.Align.CENTER)
        description_area.set_margin_bottom(30)

        self.description_label = Gtk.Label(
            label=self.config["description"]
        )
        self.description_label.add_css_class("description-label")
        self.description_label.set_halign(Gtk.Align.CENTER)
        self.description_label.set_justify(Gtk.Justification.CENTER)
        self.description_label.set_wrap(True)
        self.description_label.set_max_width_chars(60)
        description_area.append(self.description_label)

        # ── Log section ── (takes most of the height)
        log_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        log_container.set_hexpand(True)
        log_container.set_vexpand(True)
        log_container.set_valign(Gtk.Align.FILL)
        log_container.set_margin_start(40)
        log_container.set_margin_end(40)
        log_container.set_margin_bottom(20)

        log_title = Gtk.Label(label="Log Output:")
        log_title.add_css_class("log-title")
        log_title.set_halign(Gtk.Align.START)
        log_container.append(log_title)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_valign(Gtk.Align.FILL)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(380)

        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.add_css_class("log-text")
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scrolled.set_child(self.log_view)

        log_container.append(scrolled)

        # ── Status label (below log) ──
        status_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        status_area.set_hexpand(True)
        status_area.set_vexpand(False)
        status_area.set_valign(Gtk.Align.END)
        status_area.set_margin_bottom(40)
        status_area.set_margin_start(40)

        self.status_label = Gtk.Label(label="💤 Idle")
        self.status_label.add_css_class("status-label")
        self.status_label.set_halign(Gtk.Align.START)
        status_area.append(self.status_label)

        # Assemble everything
        main_box.append(button_area)
        main_box.append(description_area)
        main_box.append(log_container)
        main_box.append(status_area)

        self.set_child(main_box)

        self.setup_css()
        self.is_running = False


    def setup_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(b"""
            window {
                background-color: #0f0f0f;
                color: #e0e0e0;
                font-family: sans-serif;
            }
            .run-button {
                background-color: #e74c3c;      /* red when RUN */
                color: black;
                font-size: 52px;
                font-weight: bold;
                padding: 28px 80px;
                border-radius: 12px;
                min-width: 360px;
                box-shadow: 0 6px 16px rgba(0,0,0,0.5);
                transition: all 0.12s;
            }
            .run-button:hover {
                background-color: #c0392b;
            }
            .run-button:active {
                background-color: #a93226;
                transform: translateY(2px);
            }
            .run-button.running {               /* when STOP is shown */
                background-color: #e67e22 !important;
            }
            .status-label {
                font-size: 24px;
                font-weight: 500;
                color: #d0d8e0;
                text-align: left;
            }
            .log-title {
                font-size: 18px;
                font-weight: bold;
                color: #a0b0c0;
                margin-bottom: 8px;
            }
            .log-text {
                background-color: #141414;
                color: #d8dee9;
                font-family: monospace;
                font-size: 20px;
                padding: 16px;
                caret-color: #60a0ff;
            }
            .description-label {
                font-size: 22px;
                font-weight: 400;
                color: #b0c0d0;
                opacity: 0.9;
                padding: 0 20px;
                margin: 12px 0;
            }
            textview {
                background-color: #141414;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_buffer.insert_at_cursor(f"[{timestamp}] {message}\n")
        end = self.log_buffer.get_end_iter()
        self.log_view.scroll_to_iter(end, 0.0, True, 0.0, 1.0)


    def on_run_clicked(self, btn):
        if not self.is_running:
            self.start_process()
        else:
            self.stop_process()


    def start_process(self):
        self.is_running = True
        self.run_button.set_label(self.config["stop_text"])
        self.run_button.add_css_class("running")
        self.status_label.set_text("⏳ Running")
        self.log_message("Process started")
        threading.Thread(target=self.run_subprocess, daemon=True).start()


    def stop_process(self):
        self.is_running = False
        self.run_button.set_label("RUN")
        self.run_button.remove_css_class("running")
        self.status_label.set_text("🛑 Stopped")
        self.log_message("Process stopped by user")

    def run_subprocess(self):
        cmd = self.expand_tilde_in_list(self.config["command"])
        cwd = self.config["working_dir"]

        if cwd and '~' in cwd:
            cwd = os.path.expanduser(cwd)

        if cwd and not os.path.isdir(cwd):
            GLib.idle_add(lambda: self.log_message(f"Invalid working directory: {cwd}"))
            GLib.idle_add(lambda: self._finish("Failed — invalid working directory"))
            return
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=cwd
            )

            for line in proc.stdout:
                GLib.idle_add(lambda: self.log_message(line))
            proc.wait()

            exit_code = proc.returncode
            GLib.idle_add(lambda: self.log_message(f"Process finished with exit code {exit_code}"))

            if exit_code in self.config["success_exit_codes"]:
                GLib.idle_add(lambda: self.status_label.set_text("✅ Completed"))
            else:
                GLib.idle_add(lambda: self.status_label.set_text("📛 Failed"))


        except Exception as e:
            GLib.idle_add(lambda: self.status_label.set_text("📛 Failed"))
        GLib.idle_add(lambda: self.run_button.set_label(self.config["button_text"]))
        GLib.idle_add(lambda: self.run_button.remove_css_class("running"))
        self.is_running = False


    def simulate_work(self):
        for i in range(1, 26):
            if not self.is_running:
                GLib.idle_add(lambda: self.log_message("Process interrupted"))
                return
            GLib.idle_add(lambda s=f"Step {i}/25 - Processing...": self.log_message(s))
            time.sleep(0.6)

        if self.is_running:
            GLib.idle_add(lambda: self.log_message("Process finished successfully ✓"))
            GLib.idle_add(lambda: self.status_label.set_text("✅ Completed"))
            GLib.idle_add(lambda: self.run_button.set_label("RUN"))
            GLib.idle_add(lambda: self.run_button.remove_css_class("running"))
            self.is_running = False

    def expand_tilde_in_list(self, cmd_list):
        """
        Expand ~ → os.path.expanduser() in every list item.
        Leaves ~ inside quoted strings / arguments that shouldn't be expanded alone.
        """
        expanded = []
        for arg in cmd_list:
            # Only expand if ~ appears at the beginning of the argument or after /
            # (common cases: ~/data, ~/.config, /home/user/~something is rare)
            if '~' in arg:
                expanded.append(os.path.expanduser(arg))
            else:
                expanded.append(arg)
        return expanded
class TVApp(Gtk.Application):
    def __init__(self, config):
        super().__init__(application_id="BigButtonExecutor")
        self.config = config

    def do_activate(self):
        win = TVAppWindow(self, self.config)
        win.fullscreen()
        win.present()


def main():
    config = load_config()
    app = TVApp(config)
    try:
        return app.run(sys.argv[1:])   # skip the config file arg
    except KeyboardInterrupt:
        print("Exiting…")
        return 0


if __name__ == "__main__":
    sys.exit(main())
