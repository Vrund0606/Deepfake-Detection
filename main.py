import argparse
import os
import torch
import cv2
from src.preprocessing import extract_faces_from_video
from src.model import get_model
from torchvision import transforms

def main():
    parser = argparse.ArgumentParser(description="Deepfake Detector")
    parser.add_argument('--video', type=str, required=True, help="Path to video file")
    parser.add_argument('--output', type=str, default='output', help="Directory to save attributes")
    args = parser.parse_args()

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} not found.")
        return

    print(f"Processing video: {video_path}")
    
    

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    model = get_model(device)
    
    from transformers import AutoImageProcessor
    processor_vit = AutoImageProcessor.from_pretrained('dima806/deepfake_vs_real_image_detection')
    processor_v2 = AutoImageProcessor.from_pretrained('prithivMLmods/Deep-Fake-Detector-v2-Model')

    fake_count = 0
    total_faces = 0
    
    os.makedirs(args.output, exist_ok=True)
    
    for frame_idx, face_idx, face_pil, original_frame, box in extract_faces_from_video(video_path, sample_rate=10):
        
        import numpy as np
        face_cv2 = cv2.cvtColor(np.array(face_pil), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(face_cv2, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_prob = max(0.0, min(1.0, (100.0 - laplacian_var) / 100.0))

        inputs_vit = processor_vit(images=face_pil, return_tensors='pt').to(device)
        inputs_v2 = processor_v2(images=face_pil, return_tensors='pt').to(device)
        
        with torch.no_grad():
            ensemble_result = model(inputs_vit, inputs_v2)
            dl_prob = ensemble_result['ensemble_prob']
            
        prob_val = (dl_prob * 0.9) + (blur_prob * 0.1)
            
        print(f"Frame {frame_idx} Face {face_idx}: Fake Prob: {prob_val:.4f} (DL: {dl_prob:.4f}, Blur: {blur_prob:.4f})")
        
       
        if prob_val > 0.5:
            fake_count += 1
        total_faces += 1

    print("-" * 30)
    print(f"Summary for {video_path}")
    print(f"Total Faces Processed: {total_faces}")
    print(f"Suspicious Faces (Prob > 0.5): {fake_count}")
    if total_faces > 0:
        print(f"Overall Fake Ratio: {fake_count/total_faces:.2f}")

if __name__ == "__main__":
    main()
