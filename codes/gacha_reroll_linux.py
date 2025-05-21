# gacha_reroll_linux.py
import os
import random
import time
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from yolov8_detector import YOLOv8Detector
from PIL import Image
import pyautogui
import mss


def get_random_coordinates(bbox, x_range, y_range):
    x = random.randint(int(bbox[0] + x_range[0] * (bbox[2] - bbox[0])), int(bbox[0] + x_range[1] * (bbox[2] - bbox[0])))
    y = random.randint(int(bbox[1] + y_range[0] * (bbox[3] - bbox[1])), int(bbox[1] + y_range[1] * (bbox[3] - bbox[1])))
    return x, y


def click_random_coordinates(bbox, x_range, y_range, sleep_time=1.0):
    x, y = get_random_coordinates(bbox, x_range, y_range)
    pyautogui.click(x, y)
    time.sleep(sleep_time)


class GachaAutoThread(QThread):
    label_signal = pyqtSignal(str)
    notify_signal = pyqtSignal(list)
    update_execution_count_signal = pyqtSignal(int)
    user_response_signal = pyqtSignal(bool)

    def __init__(self, window_title):
        super().__init__()
        self.window_title = window_title
        self.image_processor = YOLOv8Detector(model_path='BD2_best.pt', conf_threshold=0.5)
        self.running = True
        self.target_ur_count = 3
        self.pending_response = None
        self.channel_id = None
        self.pause_rules = []

    def set_target_ur_count(self, ur_count):
        self.target_ur_count = ur_count

    def set_channel_id(self, id):
        self.channel_id = id

    def set_pause_rules(self, rules):
        self.pause_rules = rules

    def force_continue(self):
        if self.pending_response:
            self.pending_response = False
            self.label_signal.emit("Forced resume from UI.")

    def get_window_bbox(self):
        try:
            output = subprocess.check_output(["xdotool", "search", "--name", self.window_title]).decode().strip()
            win_id = output.split('\n')[0]
            geom = subprocess.check_output(["xdotool", "getwindowgeometry", "--shell", win_id]).decode()
            geom_dict = dict(line.split('=') for line in geom.strip().split('\n') if '=' in line)
            x, y = int(geom_dict['X']), int(geom_dict['Y'])
            width, height = int(geom_dict['WIDTH']), int(geom_dict['HEIGHT'])
            return (x, y, x + width, y + height)
        except Exception as e:
            self.label_signal.emit(f"Failed to find window: {e}")
            return None

    def run(self):
        count = 0
        while self.running:
            bbox = self.get_window_bbox()
            if not bbox:
                return

            click_random_coordinates(bbox, (0.73, 0.80), (0.90, 0.94))
            click_random_coordinates(bbox, (0.55, 0.56), (0.64, 0.65))

            for _ in range(5):
                click_random_coordinates(bbox, (0.90, 0.98), (0.1, 0.13), sleep_time=0.5)

            time.sleep(1)

            with mss.mss() as sct:
                monitor = {
                    "top": bbox[1],
                    "left": bbox[0],
                    "width": bbox[2] - bbox[0],
                    "height": bbox[3] - bbox[1]
                }
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

            self.save_image(img)
            ur_count, ur_names = self.image_processor.get_ur_info('./res/result.jpg')

            if any(rule.should_pause(ur_count, ur_names) for rule in self.pause_rules):
                self.label_signal.emit("Pause condition met.")
                self.notify_signal.emit(ur_names)
                self.pending_response = True

                while self.pending_response and self.running:
                    time.sleep(0.1)

                if not self.running:
                    break

            count += 1
            self.update_execution_count_signal.emit(count)

    def stop(self):
        self.running = False
        self.pending_response = False

    def handle_user_response(self, response):
        print(f"Received response: {response}")
        if response == "reroll":
            self.label_signal.emit("Continue running.")
        else:
            self.label_signal.emit("Stop execution.")
            self.stop()
        self.pending_response = False

    def save_image(self, img):
        if not os.path.exists('./res'):
            os.makedirs('./res')
        image_path = './res/result.jpg'
        try:
            img.save(image_path)
            self.label_signal.emit(f"You've saved the image: {image_path}")
        except Exception as e:
            self.label_signal.emit(f"Failed to save the image: {str(e)}")
