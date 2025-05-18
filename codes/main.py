import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSpinBox, QLineEdit, QTextEdit
from pynput import keyboard
from gacha_reroll import GachaAutoThread
from discord_bot import DiscordBotThread
from pause_rules import URCountRule, ContainsAnyRule, ContainsAllRule

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.gacha_thread = GachaAutoThread("BrownDust II")
        self.gacha_thread.label_signal.connect(self.update_label)
        self.gacha_thread.update_execution_count_signal.connect(self.update_execution_count)

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def initUI(self):
        self.setWindowTitle("BD2 Reroller")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Waiting")
        layout.addWidget(self.label)

        self.ur_count_label = QLabel("Set the number of UR:")
        layout.addWidget(self.ur_count_label)

        self.ur_count_spinbox = QSpinBox()
        self.ur_count_spinbox.setRange(1, 10)
        self.ur_count_spinbox.setValue(3)
        layout.addWidget(self.ur_count_spinbox)

        self.character_any_label = QLabel("Pause if any of these characters appear (comma-separated):")
        layout.addWidget(self.character_any_label)

        self.character_any_input = QLineEdit()
        layout.addWidget(self.character_any_input)

        self.character_all_label = QLabel("Pause if all of these characters appear (comma-separated):")
        layout.addWidget(self.character_all_label)

        self.character_all_input = QLineEdit()
        layout.addWidget(self.character_all_input)

        self.discord_user_id_label = QLabel("Discord UserID:")
        layout.addWidget(self.discord_user_id_label)

        self.discord_user_id_input = QLineEdit()
        layout.addWidget(self.discord_user_id_input)

        self.check_button = QPushButton("Check Discord Bot Connection")
        self.check_button.clicked.connect(self.check_connect_bot)
        layout.addWidget(self.check_button)

        self.connect_check = QLabel("Discord bot not connected")
        layout.addWidget(self.connect_check)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_gacha)
        self.start_button.setEnabled(False)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Exit")
        self.stop_button.clicked.connect(self.stop_gacha)
        layout.addWidget(self.stop_button)

        self.execution_count_label = QLabel("Pull Count: 0")
        layout.addWidget(self.execution_count_label)

        self.setLayout(layout)

    def start_gacha(self):
        target_ur_count = self.ur_count_spinbox.value()
        self.gacha_thread.set_target_ur_count(target_ur_count)
        channel_id = self.discord_channel_id_input.text()
        self.gacha_thread.set_channel_id(channel_id)

        rules = [URCountRule(target_ur_count)]

        any_names = [name.strip() for name in self.character_any_input.text().split(',') if name.strip()]
        if any_names:
            rules.append(ContainsAnyRule(any_names))

        all_names = [name.strip() for name in self.character_all_input.text().split(',') if name.strip()]
        if all_names:
            rules.append(ContainsAllRule(all_names))

        self.gacha_thread.set_pause_rules(rules)
        self.gacha_thread.start()

    def stop_gacha(self):
        self.bot_thread.stop()
        self.gacha_thread.stop()
        sys.exit(app.exec_())

    def check_connect_bot(self):
        print("Start checking Discord connections")
        try:
            if hasattr(self, 'bot_thread') and self.bot_thread.isRunning():
                self.bot_thread.stop()
                self.bot_thread.wait()

            user_id = int(self.discord_user_id_input.text())
            self.bot_thread = DiscordBotThread(user_id)

            self.bot_thread.log_signal.connect(self.update_connect)
            self.bot_thread.reroll_signal.connect(self.gacha_thread.handle_user_response)
            self.gacha_thread.notify_signal.connect(self.bot_thread.send_message_with_names)

            self.bot_thread.start()
        except ValueError:
            self.update_connect("Invalid input. The User ID is only numeric.")
        except Exception as e:
            self.update_connect(f"Error: {str(e)}")

    def update_connect(self, message):
        if "connected" in message:
            self.connect_check.setText(f"{message}")
            self.start_button.setEnabled(True)
        else:
            self.connect_check.setText(f"{message}")
            self.start_button.setEnabled(False)

    def on_press(self, key):
        try:
            if key.char == 'q':
                self.label.setText("q Stopped by keystroke")
                self.stop_gacha()
        except AttributeError:
            pass

    def update_label(self, s):
        self.label.setText(s)

    def update_execution_count(self, execution_count):
        self.execution_count_label.setText(f"Number of Pulls: {execution_count}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
