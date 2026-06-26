# Raksha: Deepfake Detector

A Python-based system for detecting deepfake media using PyTorch and OpenCV.

## Setup

1.  **Clone the repository** (if applicable).
2.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

**Run the pipeline:**
```bash
python main.py --video path/to/video.mp4
```

This will extract faces from the video and run the detection model (currently in baseline mode).
