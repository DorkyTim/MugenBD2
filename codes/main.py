import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QDialog, QVBoxLayout, QTextEdit, QPushButton
)
from pynput import keyboard
from gacha_reroll import GachaAutoThread
from discord_bot import DiscordBotThread
from pause_rules import (
    MinURCountRule, ContainsAnyRule, ContainsAllRule, CompositeRule
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.gacha_thread = GachaAutoThread("BrownDust II")
        self.gacha_thread.label_signal.connect(self.update_label)
        self.gacha_thread.update_execution_count_signal.connect(self.update_execution_count)

        self.bot_thread = None
        self.current_composite_rules = []
        self.saved_rule_sets = []

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def initUI(self):
        self.setWindowTitle("BD2 Reroller")
        self.setGeometry(100, 100, 500, 600)

        layout = QVBoxLayout()

        self.label = QLabel("Waiting")
        layout.addWidget(self.label)

        self.discord_user_id_label = QLabel("Discord UserID:")
        layout.addWidget(self.discord_user_id_label)

        self.discord_user_id_input = QLineEdit()
        layout.addWidget(self.discord_user_id_input)

        self.check_button = QPushButton("Check Discord Bot Connection")
        self.check_button.clicked.connect(self.check_connect_bot)
        layout.addWidget(self.check_button)

        self.connect_check = QLabel("Discord bot not connected")
        layout.addWidget(self.connect_check)

        # RULE BUILDER UI
        self.rule_type_selector = QComboBox()
        self.rule_type_selector.addItems(["Min UR Count", "Contains Any", "Contains All"])
        layout.addWidget(self.rule_type_selector)

        self.rule_input = QLineEdit()
        self.rule_input.setPlaceholderText("e.g. Nebris-NewHire,Nebris-NewHire,Helena-Idol")
        layout.addWidget(self.rule_input)
        
        self.info_button = QPushButton("Show Costume Names")
        self.info_button.clicked.connect(self.show_class_names)
        layout.addWidget(self.info_button)

        self.add_rule_button = QPushButton("Add Rule to Current Set")
        self.add_rule_button.clicked.connect(self.add_rule_to_set)
        layout.addWidget(self.add_rule_button)

        self.finish_set_button = QPushButton("Save Current Rule Set")
        self.finish_set_button.clicked.connect(self.save_current_set)
        layout.addWidget(self.finish_set_button)

        self.rule_sets_display = QListWidget()
        layout.addWidget(QLabel("Saved Rule Sets (OR logic between sets):"))
        layout.addWidget(self.rule_sets_display)
        
        self.remove_rule_set_button = QPushButton("Remove Selected Rule Set")
        self.remove_rule_set_button.clicked.connect(self.remove_selected_rule_set)
        layout.addWidget(self.remove_rule_set_button)

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

    def add_rule_to_set(self):
        rule_type = self.rule_type_selector.currentText()
        input_text = self.rule_input.text().strip()

        if not input_text:
            self.label.setText("Please enter a value for the rule.")
            return

        try:
            if rule_type == "Min UR Count":
                count = int(input_text)
                self.current_composite_rules.append(MinURCountRule(count))
            else:
                names = [name.strip() for name in input_text.split(',') if name.strip()]
                if rule_type == "Contains Any":
                    self.current_composite_rules.append(ContainsAnyRule(names))
                elif rule_type == "Contains All":
                    self.current_composite_rules.append(ContainsAllRule(names))

            self.label.setText(f"Added {rule_type} rule.")
            self.rule_input.clear()
        except Exception as e:
            self.label.setText(f"Failed to add rule: {str(e)}")

    def save_current_set(self):
        if not self.current_composite_rules:
            self.label.setText("No rules to save.")
            return

        composite = CompositeRule(*self.current_composite_rules)
        self.saved_rule_sets.append(composite)

        item_text = f"Set {len(self.saved_rule_sets)}: " + ", ".join([repr(r) for r in self.current_composite_rules])
        self.rule_sets_display.addItem(QListWidgetItem(item_text))

        self.current_composite_rules = []
        self.label.setText("Saved current rule set.")

    def remove_selected_rule_set(self):
        selected_items = self.rule_sets_display.selectedItems()
        if not selected_items:
            self.label.setText("No rule set selected.")
            return

        for item in selected_items:
            index = self.rule_sets_display.row(item)
            self.rule_sets_display.takeItem(index)
            del self.saved_rule_sets[index]
            self.label.setText(f"Removed Rule Set {index + 1}")

    def start_gacha(self):
        if self.gacha_thread.isRunning():
            if self.gacha_thread.pending_response:
                self.gacha_thread.force_continue()
                self.label.setText("Force-resumed reroll from UI.")
            else:
                self.gacha_thread.set_pause_rules(self.saved_rule_sets)
                self.label.setText("Updated pause rules while running.")
        else:
            self.gacha_thread = GachaAutoThread("BrownDust II")
            self.gacha_thread.label_signal.connect(self.update_label)
            self.gacha_thread.update_execution_count_signal.connect(self.update_execution_count)

            if self.bot_thread:
                self.gacha_thread.notify_signal.connect(self.bot_thread.send_message_with_names)
                self.bot_thread.reroll_signal.connect(self.gacha_thread.handle_user_response)

            self.gacha_thread.set_pause_rules(self.saved_rule_sets)
            self.gacha_thread.start()
            self.label.setText("Started rerolling.")
            self.start_button.setText("Update Rules")

    def stop_gacha(self):
        if self.bot_thread:
            self.bot_thread.stop()
        self.gacha_thread.stop()
        sys.exit(app.exec_())
        
    def show_class_names(self):
        try:
            names = self.gacha_thread.image_processor.get_class_names()
            self.show_glossary(names)
        except Exception as e:
            self.label.setText(f"Error: {str(e)}")
            
    def show_glossary(self, class_names):
        dialog = QDialog(self)
        dialog.setWindowTitle("Costume Name Glossary")
        dialog.setMinimumSize(400, 500)

        layout = QVBoxLayout()

        text_area = QTextEdit()
        text_area.setReadOnly(True)

        glossary_text = "\n".join(class_names.values())
        text_area.setText(glossary_text)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)

        layout.addWidget(text_area)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()

    def check_connect_bot(self):
        try:
            if self.bot_thread and self.bot_thread.isRunning():
                self.bot_thread.stop()
                self.bot_thread.wait()

            user_id = int(self.discord_user_id_input.text())

            self.bot_thread = DiscordBotThread(user_id)
            self.bot_thread.log_signal.connect(self.update_connect)
            self.bot_thread.reroll_signal.connect(self.gacha_thread.handle_user_response)
            self.gacha_thread.notify_signal.connect(self.bot_thread.send_message_with_names)
            self.bot_thread.start()

        except ValueError:
            self.update_connect("Invalid input: Discord User ID and Channel ID must be numbers.")
        except Exception as e:
            self.update_connect(f"Error: {str(e)}")

    def update_connect(self, message):
        self.connect_check.setText(message)

        # Only respond to actual connection events
        msg = message.lower()
        if "connected to" in msg:
            if self.gacha_thread and self.gacha_thread.isRunning():
                self.start_button.setEnabled(False)
                self.label.setText("Reroll in progress — update locked.")
            else:
                self.start_button.setEnabled(True)
                self.label.setText("Discord bot connected — ready.")
        
        elif "channel not found" in msg or "failed to connect" in msg:
            self.start_button.setEnabled(False)
            self.label.setText("Cannot start until Discord bot is connected.")

    def on_press(self, key):
        try:
            if key.char == 'q':
                self.label.setText("Stopped by 'q'")
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
