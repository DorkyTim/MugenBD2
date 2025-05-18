# yolov8_detector.py
from ultralytics import YOLO

class YOLOv8Detector:
    def __init__(self, model_path='best.pt', conf_threshold=0.5):
        self.model = YOLO(model_path)              # Load YOLOv8 model
        self.conf_threshold = conf_threshold       # Minimum confidence to count detection

    def get_ur_info(self, img):
        results = self.model.predict(img, iou=0.7, verbose=False)
        detections = results[0].boxes

        count = 0
        detected_classes = []

        for conf, cls in zip(detections.conf, detections.cls):
            if conf > self.conf_threshold:
                count += 1
                class_id = int(cls.item())
                class_name = self.model.names[class_id]
                detected_classes.append(class_name)

        print(f"UR Number (YOLO): {count}, Names: {detected_classes}")
        return count, detected_classes