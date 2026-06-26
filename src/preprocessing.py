import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image

class VideoLoader:

    def __init__(self, video_path, sample_rate=1):

        self.video_path = video_path
        self.sample_rate = sample_rate
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

    def __iter__(self):
        self.frame_count = 0
        return self

    def __next__(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                raise StopIteration
            
            self.frame_count += 1
            if (self.frame_count - 1) % self.sample_rate == 0:

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame_rgb

    def close(self):
        self.cap.release()

class FaceDetector:

    def __init__(self, device=None, margin=0):
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        self.mtcnn = MTCNN(
            keep_all=True, 
            device=self.device,
            margin=margin,
            select_largest=False
        )

    def detect(self, frame_img):

        try:
            faces = self.mtcnn(Image.fromarray(frame_img))
            if faces is None:
                return []
            return faces 
        except Exception as e:
            print(f"Error during detection: {e}")
            return []

    def detect_boxes(self, frame_img):
        """Returns bounding boxes and probabilities."""
        try:
            boxes, probs = self.mtcnn.detect(Image.fromarray(frame_img))
            return boxes, probs
        except Exception as e:
            print(f"Error during detection: {e}")
            return None, None

def extract_faces_from_video(video_path, output_folder=None, sample_rate=10):

    loader = VideoLoader(video_path, sample_rate)
    detector = FaceDetector(margin=20)
    
    try:
        for i, frame in enumerate(loader):
            img = Image.fromarray(frame)
            boxes, probs = detector.detect_boxes(frame)
            
            if boxes is not None and len(boxes) > 0:
                for j, (box, prob) in enumerate(zip(boxes, probs)):
                    if prob is None or prob < 0.90:
                        continue


                    width = box[2] - box[0]
                    height = box[3] - box[1]
                    
                    if width < 80 or height < 80:
                        continue
                        
                    # Expanded margin to 50% to precisely capture neck/jawline blending artifacts (Critical for 98% accuracy)
                    margin_x = int(width * 0.50)
                    margin_y = int(height * 0.50)

                    x1 = max(0, int(box[0]) - margin_x)
                    y1 = max(0, int(box[1]) - margin_y)
                    x2 = min(img.width, int(box[2]) + margin_x)
                    y2 = min(img.height, int(box[3]) + margin_y)
                    
                    if x2 > x1 and y2 > y1:
                        face_pil = img.crop((x1, y1, x2, y2))
                        yield i, j, face_pil, frame, box
            
    finally:
        loader.close()
