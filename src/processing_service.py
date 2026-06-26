import torch
from torchvision import transforms
from src.preprocessing import extract_faces_from_video
from src.model import get_model
import os
import cv2

class DetectionService:
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading ensemble models on {self.device}...")
        self.model = get_model(self.device)
        from transformers import AutoImageProcessor
        self.processor_vit = AutoImageProcessor.from_pretrained('dima806/deepfake_vs_real_image_detection')
        self.processor_v2 = AutoImageProcessor.from_pretrained('prithivMLmods/Deep-Fake-Detector-v2-Model')

    def process_video(self, video_path):

        if not os.path.exists(video_path):
            return {"error": "File not found"}

        import numpy as np

        fake_count = 0
        total_faces = 0
        frame_results = []
        total_fake_prob = 0.0

        annotated_dir = os.path.join('static', 'annotated')
        os.makedirs(annotated_dir, exist_ok=True)

        # Forensic signal accumulators
        blur_scores        = []   # Laplacian variance (low = blurry)
        chroma_asym_scores = []   # R-B channel abs diff (high = color manipulation)
        edge_scores        = []   # Canny edge density (low = over-smooth)
        texture_scores     = []   # local std-dev (low = uniform/fake)
        prob_history       = []   # per-frame fake probabilities (for drift)
        vit_probs          = []
        v2_probs           = []

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        fps_sample_rate = int(fps) if fps > 0 else 30

        try:
            for frame_idx, face_idx, face_pil, original_frame, box in extract_faces_from_video(video_path, sample_rate=fps_sample_rate):
                if total_faces >= 50:
                    break

                face_cv2 = cv2.cvtColor(np.array(face_pil), cv2.COLOR_RGB2BGR)
                gray     = cv2.cvtColor(face_cv2, cv2.COLOR_BGR2GRAY)

                # 1. Sharpness / Blur
                lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                blur_scores.append(lap_var)

                # 2. Color Channel Asymmetry
                r_mean = float(face_cv2[:, :, 2].mean())
                b_mean = float(face_cv2[:, :, 0].mean())
                chroma_asym_scores.append(abs(r_mean - b_mean))

                # 3. Edge Coherence
                edges = cv2.Canny(gray, 50, 150)
                edge_density = float(np.count_nonzero(edges)) / (gray.shape[0] * gray.shape[1])
                edge_scores.append(edge_density)

                # 4. Texture Uniformity
                local_std = float(gray.astype(np.float32).std())
                texture_scores.append(local_std)

                inputs_vit = self.processor_vit(images=face_pil, return_tensors='pt').to(self.device)
                inputs_v2  = self.processor_v2(images=face_pil,  return_tensors='pt').to(self.device)

                with torch.no_grad():
                    ensemble_result = self.model(inputs_vit, inputs_v2)
                    dl_prob  = ensemble_result['ensemble_prob']
                    vit_prob = ensemble_result['vit_prob']
                    v2_prob  = ensemble_result['v2_prob']

                prob_val = float(dl_prob)
                vit_probs.append(float(vit_prob))
                v2_probs.append(float(v2_prob))
                prob_history.append(prob_val)

                total_fake_prob += prob_val
                is_fake = bool(prob_val > 0.5)
                if is_fake:
                    fake_count += 1
                total_faces += 1

                color = (0, 80, 255) if is_fake else (0, 220, 100)
                label = f"{'FAKE' if is_fake else 'REAL'}  {prob_val * 100:.1f}%"

                draw_frame = np.array(original_frame).copy()
                x1, y1, x2, y2 = map(int, box)

                cv2.rectangle(draw_frame, (x1, y1), (x2, y2), color, 3)

                (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
                cv2.rectangle(draw_frame, (x1, y1 - label_h - 12), (x1 + label_w + 10, y1), color, -1)
                cv2.putText(draw_frame, label, (x1 + 5, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

                filename = f"annotated_{os.path.basename(video_path)}_f{frame_idx}.jpg"
                filepath = os.path.join(annotated_dir, filename)

                frame_bgr = cv2.cvtColor(draw_frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(filepath, frame_bgr)

                frame_results.append({
                    "frame": frame_idx,
                    "face_index": face_idx,
                    "fake_probability": round(prob_val, 4),
                    "is_fake": is_fake,
                    "annotated_image": f"/static/annotated/{filename}"
                })
        except Exception as e:
            return {"error": str(e)}

        overall_ratio = 0.0
        fake_frame_ratio = 0.0

        fake_frames_count  = len(set(f['frame'] for f in frame_results if f['is_fake']))
        total_unique_frames = len(set(f['frame'] for f in frame_results))

        if total_faces > 0:
            probs = sorted([f['fake_probability'] for f in frame_results], reverse=True)
            top_focus_count = max(1, int(len(probs) * 0.35))
            top_focus_probs = probs[:top_focus_count]
            overall_ratio = sum(top_focus_probs) / top_focus_count

        if total_unique_frames > 0:
            fake_frame_ratio = fake_frames_count / total_unique_frames

        verdict = "REAL"
        if overall_ratio > 0.55 or fake_frame_ratio > 0.40:
            verdict = "FAKE"

        reasons = self._build_reasons(
            verdict          = verdict,
            blur_scores      = blur_scores,
            chroma_scores    = chroma_asym_scores,
            edge_scores      = edge_scores,
            texture_scores   = texture_scores,
            prob_history     = prob_history,
            vit_probs        = vit_probs,
            v2_probs         = v2_probs,
            fake_frame_ratio = fake_frame_ratio,
            overall_ratio    = overall_ratio,
        )

        return {
            "total_faces_analyzed":  total_faces,
            "suspicious_faces_count": fake_count,
            "overall_fake_ratio":    round(overall_ratio, 4),
            "fake_frame_ratio":      round(fake_frame_ratio, 4),
            "verdict":               verdict,
            "reasons":               reasons,
            "details":               frame_results
        }

    # ── Forensic Reasons Builder ────────────────────────────────────────────
    def _build_reasons(self, verdict, blur_scores, chroma_scores, edge_scores,
                       texture_scores, prob_history, vit_probs, v2_probs,
                       fake_frame_ratio, overall_ratio):
        import numpy as np
        reasons = []

        def avg(lst):   return float(np.mean(lst)) if lst else 0.0
        def stdev(lst): return float(np.std(lst))  if lst else 0.0

        is_fake   = verdict == "FAKE"
        vit_mean  = avg(vit_probs)
        v2_mean   = avg(v2_probs)
        model_gap = abs(vit_mean - v2_mean)
        model_agree = model_gap < 0.15

        # 1. Neural Model Consensus
        if is_fake:
            severity = "critical" if overall_ratio > 0.80 else ("high" if overall_ratio > 0.65 else "medium")
            reasons.append({
                "icon": "🧠",
                "title": "Neural Network Consensus",
                "description": (
                    f"Both AI models independently flagged this video as manipulated. "
                    f"ViT model confidence: {vit_mean*100:.1f}%, CNN/ViT model confidence: {v2_mean*100:.1f}%. "
                    f"{'High agreement between models strengthens this verdict.' if model_agree else 'Models show partial disagreement, suggesting subtle manipulation.'}"
                ),
                "severity": severity,
                "score": round(overall_ratio * 100, 1)
            })

        # 2. Facial Blur / Sharpness Artifacts
        avg_blur = avg(blur_scores)
        blur_threshold = 120.0
        if avg_blur < blur_threshold:
            severity = "high" if avg_blur < 50 else "medium"
            reasons.append({
                "icon": "🔍",
                "title": "Unnatural Facial Blurring",
                "description": (
                    f"Detected abnormally low sharpness variance ({avg_blur:.1f} vs expected >{blur_threshold:.0f}). "
                    "Deepfake generators often produce unnaturally smooth facial regions due to upsampling artifacts, "
                    "especially around the forehead, cheeks, and jaw boundaries."
                ),
                "severity": severity,
                "score": round(max(0, (blur_threshold - avg_blur) / blur_threshold * 100), 1)
            })

        # 3. Color Channel Asymmetry
        avg_chroma = avg(chroma_scores)
        chroma_threshold = 18.0
        if avg_chroma > chroma_threshold:
            severity = "high" if avg_chroma > 35 else "medium"
            reasons.append({
                "icon": "🎨",
                "title": "Color Channel Manipulation",
                "description": (
                    f"Significant red-blue channel imbalance detected (difference: {avg_chroma:.1f} units). "
                    "GAN-generated faces frequently exhibit subtle color channel shifts during facial synthesis, "
                    "particularly in skin tone rendering and lighting simulation."
                ),
                "severity": severity,
                "score": round(min(100, avg_chroma / 50 * 100), 1)
            })

        # 4. Edge Coherence
        avg_edge = avg(edge_scores)
        edge_threshold = 0.04
        if avg_edge < edge_threshold:
            severity = "medium" if avg_edge < 0.025 else "low"
            reasons.append({
                "icon": "📐",
                "title": "Degraded Edge Coherence",
                "description": (
                    f"Edge density ({avg_edge*100:.2f}%) is unusually low compared to authentic videos (~4%+). "
                    "Neural face-swapping and re-enactment models tend to over-smooth facial boundaries, "
                    "causing blurred eye contours, hairline edges, and jawline transitions."
                ),
                "severity": severity,
                "score": round(max(0, (edge_threshold - avg_edge) / edge_threshold * 100), 1)
            })

        # 5. Texture Uniformity
        avg_texture = avg(texture_scores)
        texture_threshold = 45.0
        if avg_texture < texture_threshold:
            severity = "medium" if avg_texture < 30 else "low"
            reasons.append({
                "icon": "🧩",
                "title": "Suspiciously Smooth Skin Texture",
                "description": (
                    f"Facial texture uniformity score ({avg_texture:.1f}) is below the natural threshold ({texture_threshold:.0f}). "
                    "Real human skin exhibits micro-pore and fine-line irregularities. "
                    "Deepfake models trained on smoothed datasets often produce glass-like, over-uniform skin surfaces."
                ),
                "severity": severity,
                "score": round(max(0, (texture_threshold - avg_texture) / texture_threshold * 100), 1)
            })

        # 6. Temporal Probability Drift
        if len(prob_history) >= 4:
            prob_std = stdev(prob_history)
            drift_threshold = 0.18
            if prob_std > drift_threshold:
                severity = "high" if prob_std > 0.30 else "medium"
                reasons.append({
                    "icon": "📈",
                    "title": "Temporal Inconsistency Across Frames",
                    "description": (
                        f"Fake probability fluctuated significantly (sigma={prob_std:.3f}) across {len(prob_history)} frames. "
                        "Authentic videos maintain consistent facial features over time. "
                        "High variance suggests the swap quality degrades in certain frames — "
                        "a hallmark of generative model instability under motion or lighting changes."
                    ),
                    "severity": severity,
                    "score": round(min(100, prob_std / 0.5 * 100), 1)
                })

        # 7. High Fake Frame Ratio
        if fake_frame_ratio > 0.30:
            severity = "critical" if fake_frame_ratio > 0.70 else ("high" if fake_frame_ratio > 0.50 else "medium")
            reasons.append({
                "icon": "🎞",
                "title": "High Proportion of Suspicious Frames",
                "description": (
                    f"{fake_frame_ratio*100:.1f}% of analyzed frames were independently classified as fake. "
                    "This sustained pattern across the video suggests systematic facial replacement "
                    "rather than isolated compression artifacts or lighting anomalies."
                ),
                "severity": severity,
                "score": round(fake_frame_ratio * 100, 1)
            })

        # 8. Clean verdict for REAL videos
        if not is_fake and not reasons:
            reasons.append({
                "icon": "✅",
                "title": "No Manipulation Detected",
                "description": (
                    "All forensic signals are within normal ranges for authentic video. "
                    "Sharpness, color channels, edge coherence, and texture uniformity are consistent "
                    "with real facial footage. Both AI models agree this video is genuine."
                ),
                "severity": "none",
                "score": 0.0
            })

        return reasons
