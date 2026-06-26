import torch
import torch.nn as nn
from transformers import AutoModelForImageClassification
import ssl


ssl._create_default_https_context = ssl._create_unverified_context


class EnsembleDeepFakeDetector(nn.Module):
    def __init__(self, device='cpu'):
        super(EnsembleDeepFakeDetector, self).__init__()
        print(f"Loading DL Model 1: ViT (dima806)...")
        self.model_vit = AutoModelForImageClassification.from_pretrained('dima806/deepfake_vs_real_image_detection').to(device)
        
        print(f"Loading DL Model 2: CNN/ViT (prithivMLmods)...")
        self.model_v2 = AutoModelForImageClassification.from_pretrained('prithivMLmods/Deep-Fake-Detector-v2-Model').to(device)
        self.device = device
        
    def forward(self, inputs_vit, inputs_v2):
        # Model 1 prediction
        outputs_vit = self.model_vit(**inputs_vit)
        probs_vit = torch.softmax(outputs_vit.logits, dim=1)[:, 1].item()
        
        # Model 2 prediction
        outputs_v2 = self.model_v2(**inputs_v2)
        probs_v2 = torch.softmax(outputs_v2.logits, dim=1)[:, 1].item()
        
        # Ensemble Average
        ensemble_prob = (probs_vit * 0.6) + (probs_v2 * 0.4) 
        
        return {
            'vit_prob': probs_vit,
            'v2_prob': probs_v2,
            'ensemble_prob': ensemble_prob
        }


def get_model(device='cpu'):
    model = EnsembleDeepFakeDetector(device=device)
    model.eval()
    return model
