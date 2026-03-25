#!/usr/bin/python3
"""App to do system and flatpak updates"""

import sys
import os
import subprocess
from time import sleep
from tempfile import NamedTemporaryFile
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QTextEdit,
    QLabel,
)
from PySide6.QtCore import Qt, QThread, Slot, Signal
from PySide6.QtGui import QFont


class UpdateWorker(QThread):
    """Class to run the update process"""

    output_signal = Signal(str)
    finished_signal = Signal(bool)  # True if reboot is needed

    def run_update(self):
        """Run the update process"""
        if self.updates_available():
            self.output_signal.emit("Updating system packages:")
            self.generic_run(command=["sudo", "apt-get", "upgrade", "-y"], i_hate_ubuntu=True)
            self.output_signal.emit("Updating flatpak packages:")
            self.generic_run(command=["flatpak", "update", "-y"])
            self.output_signal.emit("Reboot in 30 seconds!")
            self.finished_signal.emit(True)
            sleep(30)
            # self.generic_run(command=["reboot"])
        self.output_signal.emit("No Updates available.")
        self.finished_signal.emit(True)

    def updates_available(self) -> bool:
        """Check if there are any available updates."""
        commands = [
            ["flatpak", "remote-ls", "--updates"],
            [
                "apt-get",
                "-o",
                "APT::Get::Show-User-Simulation-Note=false",
                "--quiet",
                "--quiet",
                "--simulate",
                "upgrade",
            ],
        ]
        update_needed = False
        self.output_signal.emit("##################################")
        self.output_signal.emit("Checking for updates:")
        self.generic_run(
            command=["sudo", "apt-get", "update"], allowed_exit_codes=[0, 130], i_hate_ubuntu=True
        )

        for command in commands:
            self.output_signal.emit(f"Checking for with {command}")
            output = self.generic_run(command=command, return_output=True)
            if output:
                self.output_signal.emit(f"Checking for with {output}")
                update_needed = True
        return update_needed

    def generic_run(
        self, command, return_output=False, allowed_exit_codes=None, i_hate_ubuntu=False
    ) -> list[str] | None:
        """Runs a shell command with optional output capture."""

        if not allowed_exit_codes:
            allowed_exit_codes = [0]

        combined_output = []
        self.output_signal.emit("Updating system packages:")
        if i_hate_ubuntu:

            temp_file = NamedTemporaryFile(mode='w+', delete=False)
            command_string = " ".join(command)
            temp_file.write(f"#!/bin/bash\n{command_string}\nexit $?")
            temp_file.flush()
            temp_file.close()
            os.chmod(temp_file.name, 0o755)
            command = [temp_file.name]

        try:
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            ) as process:

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
                    self.output_signal.emit(
                        f"Command {' '.join(command)} failed with exit code {return_code}"
                    )

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.output_signal.emit(
                f"Error running command {' '.join(command)}: {str(e)}"
            )
        if i_hate_ubuntu and temp_file:
            os.unlink(temp_file.name)

        if return_output:
            return combined_output
        return None


class UpdateManager(QMainWindow):
    """Class that provides Update Manager UI"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PiSight Update Manager")
        self.setWindowState(Qt.WindowFullScreen)

        # Create central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Button Layout (horizontal)
        button_layout = QHBoxLayout()

        # Create update button
        self.update_button = QPushButton("Update")
        self.update_button.setFocusPolicy(Qt.StrongFocus)
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

        # Exit Button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setFocusPolicy(Qt.StrongFocus)

        # Style
        self.exit_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                background-color: red;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # Buttons zum Layout hinzufügen
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.exit_button)

        # Create log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFocusPolicy(Qt.NoFocus)
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
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.log_output)
        main_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Set central widget
        self.setCentralWidget(central_widget)

        # Connect button click signal
        self.update_button.clicked.connect(self.start_update_process)  # pylint: disable=no-member
        self.exit_button.clicked.connect(self.close)  # pylint: disable=no-member

        # Initialize worker thread
        self.worker_thread = QThread()
        self.worker = UpdateWorker()
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run_update)  # pylint: disable=no-member
        self.worker.output_signal.connect(self.log_output.append)
        self.worker.finished_signal.connect(self.on_update_finished)

        self.setTabOrder(self.update_button, self.exit_button)
        self.setTabOrder(self.exit_button, self.update_button)

        self.update_button.setFocus()

    def keyPressEvent(self, event):  # pylint: disable=invalid-name
        """Handle key press events"""
        if event.key() in (Qt.Key_Right, Qt.Key_Down):
            if self.update_button.hasFocus():
                self.exit_button.setFocus()
            else:
                self.update_button.setFocus()

        elif event.key() in (Qt.Key_Left, Qt.Key_Up):
            if self.exit_button.hasFocus():
                self.update_button.setFocus()
            else:
                self.exit_button.setFocus()

        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            focused_widget = self.focusWidget()
            if isinstance(focused_widget, QPushButton):
                focused_widget.click()

    def start_update_process(self):
        """Function to start the update process"""
        # Stop
        self.update_button.setEnabled(False)
        self.status_label.setText("running")
        self.log_output.clear()

        # Start thread
        self.worker_thread.start()

    @Slot(bool)
    def on_update_finished(self):
        """Function so do tasks after the update finished"""
        self.worker_thread.quit()
        self.update_button.setEnabled(True)
        self.status_label.setText("complete")
        self.exit_button.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = UpdateManager()
    window.show()

    sys.exit(app.exec())
