import cv2
import numpy as np

class ImageProcessor:
    def __init__(self):
        self.lower_hsv = np.array([50, 15, 230])
        self.upper_hsv = np.array([120, 255, 255])

    def convert_image(self, img):
        """RGB에서 BGR로 변환후 HSV 변환"""
        image = np.array(img)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        return hsv

    def create_mask(self, hsv):
        """HSV 범위내 마스크 생성"""
        return cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

    def clean_mask(self, mask):
        """노이즈 제거"""
        height, width = mask.shape
        mask_half = mask[:height//3, :]
        kernel = np.ones((11, 11), np.uint8)
        for _ in range(2):
            mask_half = cv2.morphologyEx(mask_half, cv2.MORPH_CLOSE, kernel)
            mask_half = cv2.morphologyEx(mask_half, cv2.MORPH_OPEN, kernel)
        return mask_half

    def count_contours(self, mask_half_cleaned):
        """컨투어 검출 및 갯수 리턴"""
        contours, _ = cv2.findContours(mask_half_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return len(contours)

    def get_ur_num(self, img):
        """UR 갯수 검출 리턴"""
        hsv = self.convert_image(img)
        mask = self.create_mask(hsv)
        mask_half_cleaned = self.clean_mask(mask)
        ur_count = self.count_contours(mask_half_cleaned)
        print(f'UR Number: {ur_count}')
        return ur_count
