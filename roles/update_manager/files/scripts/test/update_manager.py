import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTextEdit, QLabel)
from PySide6.QtCore import Qt, QThread, Slot, Signal
from PySide6.QtGui import QFont
import subprocess
from time import sleep

class UpdateWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal(bool)  # True if reboot is needed

    def __init__(self):
        super().__init__()

    def run_update(self):
        if self.updates_available():
            self.output_signal.emit("Updating system packages:")
            self.generic_run(command=["sudo", "apt-get", "upgrade", "-y"])
            self.output_signal.emit("Updating flatpak packages:")
            self.generic_run(command=["flatpak", "update", "-y"])
            self.output_signal.emit("Reboot in 30 seconds!")
            sleep(30)
            #self.generic_run(command=["reboot"])

    def updates_available(self) -> bool:
        commands = [
            ["flatpak", "remote-ls", "--updates"],
            ["apt", "--quiet", "list", "--upgradeable"],
        ]
        update_needed = False
        self.output_signal.emit("##################################")
        self.output_signal.emit("Checking for updates:")
        self.generic_run(command=["sudo", "apt-get", "update", "-y"], allowed_exit_codes=[0, 130])

        for command in commands:
            self.output_signal.emit(f"Checking for with {command}")
            output = self.generic_run(command=command, return_output=True)
            if output:
                self.output_signal.emit(f"Checking for with {output}")
                update_needed = True
        return update_needed

    def generic_run(self, command, return_output=False, allowed_exit_codes=[0]) -> list[str]|None:

        combined_output = []
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # Read output line by line
            while True:
                output = process.stdout.readline()
                if output:
                    clean_output = output.strip()
                    self.output_signal.emit(clean_output)
                    if clean_output:
                        combined_output.append(clean_output)

                if not output and process.poll() is not None:
                    break

            return_code = process.wait()

            # If command failed, log it
            if return_code not in allowed_exit_codes:
                self.output_signal.emit(f"Command {' '.join(command)} failed with exit code {return_code}")

        except Exception as e:
            self.output_signal.emit(f"Error running command {' '.join(command)}: {str(e)}")

        if return_output:
            return combined_output
        return None

class UpdateManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PiSight Update Manager")
        self.setWindowState(Qt.WindowFullScreen)

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create update button
        self.update_button = QPushButton("Update")
        self.update_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Create log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Monospace", 12))
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: white;
                border-radius: 5px;
            }
        """)

        # Create status label
        self.status_label = QLabel("idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))

        # Add widgets to layout
        main_layout.addWidget(self.update_button, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.log_output)
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Connect button click signal
        self.update_button.clicked.connect(self.start_update_process)

        # Initialize worker thread
        self.worker_thread = QThread()
        self.worker = UpdateWorker()
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run_update)
        self.worker.output_signal.connect(self.log_output.append)
        self.worker.finished_signal.connect(self.on_update_finished)

    def start_update_process(self):
        self.update_button.setEnabled(False)
        self.status_label.setText("running")
        self.log_output.clear()

        # Start thread
        self.worker_thread.start()

    @Slot(bool)
    def on_update_finished(self, reboot_needed):
        self.worker_thread.quit()
        self.update_button.setEnabled(True)
        self.status_label.setText("complete")

        if not reboot_needed:
            self.log_output.append("Update complete. No reboot needed.")
        else:
            self.log_output.append("Reboot initiated.")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = UpdateManager()
    window.show()

    sys.exit(app.exec())
