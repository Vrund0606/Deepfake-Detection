# DeepFake Detection System - Project Analysis

## 1. System Architecture overview
The project is a **Web-based Deepfake Detection System** utilizing a modular Python backend (Flask) and a client-side frontend (HTML/JS).

**Core Components:**
- **Frontend**: A modern dashboard for checking video authenticity.
- **API Layer**: Flask server handling file uploads and JSON responses.
- **Service Layer**: Business logic orchestration.
- **Core Logic**: Deep learning model (EfficientNet) and Computer Vision pipelines (MTCNN).

## 2. Directory Structure Breakdown
```
.
├── app.py                  # Entry point (Flask Server)
├── main.py                 # (Legacy) CLI entry point
├── requirements.txt        # Python Dependencies
├── src/                    # Core Logic Modules
│   ├── model.py            # Neural Network Definition (EfficientNet-B0)
│   ├── preprocessing.py    # Video Loading & Face Detection (MTCNN)
│   └── processing_service.py # Integration logic (Video -> Score)
├── static/                 # Frontend Assets (CSS/JS)
├── templates/              # HTML Templates
└── uploads/                # Temp storage for video processing
```

## 3. Detailed Component Analysis

### A. Frontend (`templates/index.html`, `static/*`)
- **Design**: Uses a dark-themed, glassmorphic UI (`style.css`).
- **Interaction**: `script.js` handles file Drag & Drop events.
- **Communication**: Sends `POST /upload` requests via `fetch` API.
- **Feedback**: Displays a loading spinner while the backend processes frames, then renders the Fake probability and verdict.

### B. Backend API (`app.py`)
- **Framework**: Flask.
- **Endpoints**:
    - `GET /`: Renders the dashboard.
    - `POST /upload`: Accepts video files, saves them temporarily, invokes the `processing_service`, and returns JSON results.
- **Configuration**: max upload size 50MB.

### C. Logic Layer (`src/processing_service.py`)
- Acts as the controller.
- **Initialization**: Loads the heavy PyTorch model *once* when the app starts, preventing latency per request.
- **Workflow**:
    1.  Receives video path.
    2.  Iterates through frames (sample rate: every 10th frame).
    3.  Extracts faces using MTCNN.
    4.  Normalizes faces (ImageNet stats in `preprocessing.py`/`service.py`).
    5.  Inference via `DeepFakeClassifier`.
    6.  Aggregates results (Average probability) to decide "REAL" vs "FAKE".

### D. Core Model (`src/model.py`)
- **Architecture**: **EfficientNet-B0**.
- **Modification**: The final classification layer is replaced with `nn.Linear(..., 1)` for binary output (Fake probability).
- **Weights**: Pre-trained on ImageNet (Transfer Learning). 
    - *Note:* Currently using generic pre-trained weights. For high accuracy on Deepfakes, this model needs fine-tuning on datasets like FaceForensics++.
- **Safety**: Includes an SSL context patch to bypass macOS certificate errors during weight download.

### E. Preprocessing (`src/preprocessing.py`)
- **VideoLoader**: OpenCV-based iterator for memory-efficient frame reading.
- **FaceDetector**: Wraps `facenet_pytorch.MTCNN`.
    - **Advantage**: Robust face alignment.
    - **Output**: Returns aligned face tensors ready for the classifier.

## 4. Data Flow
1.  **User** uploads `video.mp4`.
2.  **Flask** saves to `uploads/video.mp4`.
3.  **Service** opens video, reads Frame 0.
4.  **MTCNN** finds Face bounding box.
5.  **Service** crops face, resizes to 224x224.
6.  **EfficientNet** predicts: `0.85` (Fake).
7.  Repeats for frames 10, 20, 30...
8.  **Service** computes Average: `0.82`.
9.  **Frontend** displays "FAKE" badge.

## 5. Potential Improvements
- **Asynchronous Processing**: Currently, the request hangs until processing is done. For long videos, this might timeout. Using Celery/Redis would handle this better.
- **Model Training**: The current model uses generic weights. It effectively detects "artifacts" but isn't specifically trained on Deepfakes yet.
- **Security**: The `uploads` folder grows indefinitely. A cleanup job implies.
