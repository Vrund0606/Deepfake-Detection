# Deepfake Detection System - Semester 6 Project

## 1. Project Objective
The objective of this project is to build an advanced, highly accurate, and visually compelling web application that determines whether a given video contains manipulated human faces (Deepfakes) or authentic footage. 

It accomplishes this by extracting temporal frame data and passing faces through an **Ensemble Deep Learning Architecture**, wrapped in a modern Glassmorphism User Interface.

---

## 2. Technology Stack
**Frontend (Client-Side)**
*   **HTML5 & CSS3**: Core structure, utilizing advanced CSS properties like `backdrop-filter` for glassmorphism and `@keyframes` for floating UI animations.
*   **Vanilla Javascript**: Client-side logic bypassing complex frameworks, handling rapid DOM manipulation, file validation, and asynchronous API `fetch` requests.
*   **Chart.js**: Renders interactive data visualizations (Model parameter comparisons and Confidence Distribution Donut charts).
*   **Particles.js**: Renders the background interactive node-mesh, contributing to the futuristic aesthetic.

**Backend (Server-Side)**
*   **Python 3**: Core execution language.
*   **Flask Web Framework**: Handles HTTP routing, REST API endpoints (`/upload`), and Session mapping (`users.json`).
*   **PyTorch**: The foundational tensor library running the Artificial Intelligence neural networks.
*   **HuggingFace Transformers**: Used to securely download and construct the neural architectures without requiring gigabytes of local storage.

---

## 3. The Artificial Intelligence Engine
The system uses an **Ensemble Configuration** to achieve maximum accuracy. No single model catches everything, so combining them yields vastly superior results.

### A. Preprocessing Pipeline (`MTCNN`)
The first step of analysis is **Face Extraction**. 
Instead of sending an entire video frame to the AI (which is slow and introduces noise from the background), the system uses **Multi-task Cascaded Convolutional Network (MTCNN)**. MTCNN draws a bounding box exclusively around human facial structures, crops the image, and forwards only the face to the classification nets.

### B. Classification Model 1: Vision Transformer (ViT)
*   **Model Source**: `dima806/deepfake_vs_real_image_detection`
*   **How it Works**: Transformers split the face into "patches" and analyze the relationship between all patches simultaneously. It is incredible at catching global inconsistencies (e.g., if lighting on the left cheek does not mathematically align with lighting on the forehead).

### C. Classification Model 2: Convolutional Neural Network (CNN)
*   **Model Source**: `prithivMLmods/Deep-Fake-Detector-v2-Model`
*   **How it Works**: CNNs excel at local pixel analysis. They scan the image using sliding matrices to find micro-anomalies, such as edge-blurring around the lips (a common artifact in Deepfake mouth-syncing) or unnatural pixel blending at the jawline.

### D. The Synthesis Logic
The backend analyzes multiple frames from the video. It averages the score of both models for each frame. The system then isolates the **Top 50% most anomalous frames**. If those highly-suspicious frames cross a 50% confidence threshold, the overall video is flagged as `FAKE`.

## 4. Complete Project File Structure

```text
DeepFake Detection/
│
├── app.py                     # The main Flask server application. Handles routes & auth.
├── users.json                 # Persistent database storing login credentials.
│
├── src/                       # Artificial Intelligence Core
│   ├── preprocessing.py       # Handles CV2 frame extraction and MTCNN face cropping.
│   └── processing_service.py  # Loads the PyTorch Models & runs the Ensemble Logic.
│
├── templates/
│   ├── index.html             # The main Deepfake Analysis Dashboard UI.
│   └── login.html             # The secure System Authentication gateway.
│
├── static/
│   ├── style.css              # The active CSS defining Glassmorphism rendering.
│   ├── script.js              # The active JS controlling API calls, Charts, and UX.
│   ├── master.css             # (Legacy) Historical CSS layout file.
│   └── app.js                 # (Legacy) Historical Javascript file.
│
├── uploads/                   # Temporary storage for user-uploaded videos.
└── venv/                      # The isolated Python Virtual Environment for dependencies.
```

---

## 5. User Interface & Experience Details
The UI was meticulously designed to look like a premium, enterprise-grade AI tool.
*   **Float Effects**: Cards slowly levitate vertically to create a dynamic, living interface.
*   **Glassmorphism**: Panels possess a frosted-glass transparency blur (`rgba` + `backdrop-filter`), layering beautifully over the dark starry background.
*   **Color Tracking**: Based on the AI's final verdict, the entire UI theme dynamically changes state. If `REAL`, the UI projects a secure Emerald Neon Green. If `FAKE`, the UI flashes an emergency Crimson Neon Red.

---

## 6. Future Expansion Capabilities
While the project is fully complete, its architecture supports rapid expansion:
*   **Database Migration**: The `users.json` system can be instantly swapped for `MySQL` or `PostgreSQL` using `Flask-SQLAlchemy`.
*   **Background Processing**: `Celery` & `Redis` could be installed to allow users to scan massive 4K hour-long videos asynchronously without freezing the frontend. 
*   **Mobile Variant**: A decoupled mobile frontend can tie directly into the existing `app.py` `/upload` backend for cross-platform support.
