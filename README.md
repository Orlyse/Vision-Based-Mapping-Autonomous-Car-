# Vision-Based ESP32 Car Robot with 2D Mapping

This project implements a small autonomous car robot that uses a Freenove ESP32-S3 WROOM board and an onboard OV2640 camera to navigate indoor environments while building a simple 2D map of its trajectory.

The core of the system is a Python program running on a host computer. It:

- Streams images from an HTTP server hosted on the ESP32.
- Processes the images using OpenCV to detect obstacles.
- Decides how the robot should move (forward, left, or right).
- Sends motor commands back to the ESP32 over HTTP.
- Logs each motion command to reconstruct a 2D map of the environment.

---

## Features
- **Hardware**: ESP32-S3 board, two DC motors, a simple H-bridge, and a 3D-printed chassis.
- **Vision-based navigation**: Uses only a single camera (no lidar or encoders).
- **Lightweight perception pipeline**:
  - Resize + grayscale conversion  
  - Local variance (texture) map  
  - Thresholding and inversion to find smoother floor regions  
  - Gaussian blur and Canny edge detection  
  - Masking edges to highlight obstacle-like boundaries
- **Reactive control**:
  - Splits the processed image into left/center/right regions.
  - Uses edge density in each region as a proxy for obstacle presence.
  - Selects forward/turn-left/turn-right commands using a simple decision rule.
- **Trajectory logging & mapping**: Stores motion commands to CSV and reconstructs a 2D “map” of the robot’s path.
---

## Hardware

- **Controller**: Freenove ESP32-S3 WROOM board  
- **Camera**: OV2640 pre-mounted on the ESP32 board  
- **Motors**: 2× DC motors in a rear differential-drive configuration  
- **Motor driver**: H-bridge (e.g., L298N or similar)  
- **Power**: 9 V battery (motors powered from battery, ESP32 via onboard regulator)  
- **Chassis**:
  - 3D-printed base  
  - Two 65 mm rubber rear wheels (SparkFun)  
  - One front caster / free-rolling wheel  

The ESP32 hosts an HTTP server for:

- Streaming JPEG frames from the OV2640 camera.
- Receiving motor commands (e.g., “forward”, “left”, “right”, “stop”) on a separate endpoint/port.

The H-bridge inputs are connected to ESP32 GPIOs for PWM control of motor speed and direction.

---

## Software

### Host PC

- **Language**: Python 3
- **Main dependencies**:
  - `opencv-python` (image processing)
  - `numpy` (numerical operations)
  - `requests` or `http.client` (HTTP communication with ESP32)
  - `matplotlib` (optional, for plotting the 2D map)
  - `pandas` (optional, for handling CSV logs)

### ESP32

- **Environment**: Arduino IDE / PlatformIO / ESP-IDF (whichever you used)
- Responsibilities:
  - Initialize camera (OV2640).
  - Connect to Wi-Fi network.
  - Run HTTP server for:
    - `/stream` or similar: serve JPEG frames.
    - `/cmd` or similar: accept control commands and update motor PWM outputs.

> **Note:** Update endpoint names and ports in this README to match your actual firmware.

---

## How It Works

1. **Image Streaming & Processing**
   - The Python script periodically requests JPEG frames from the ESP32 camera server.
   - Each frame is decoded into an OpenCV image and passed through the perception pipeline:
     1. Resize and convert to grayscale.
     2. Compute a local variance (texture) map.
     3. Threshold and invert to isolate relatively smooth floor regions.
     4. Apply Gaussian blur and Canny edge detection.
     5. Mask the edges using the smooth-region map to emphasize obstacles.

2. **Decision Making**
   - The processed image is divided into three vertical regions: **left**, **center**, **right**.
   - The script sums edge intensity in each region to estimate obstacle density.
   - Simple rule:
     - If the center region has low edge density → move **forward**.
     - Otherwise → turn toward the side (left/right) with lower edge density.
   - The chosen command is sent back to the ESP32 via an HTTP request.

3. **Logging & Mapping**
   - Each time a motion command is sent, the script logs:
     - Timestamp
     - Command (forward, left, right, stop)
     - Any additional metadata (e.g., step index)
   - A separate mapping function/script interprets the sequence of commands as a path in 2D:
     - Forward = step forward by a fixed distance
     - Left/right = rotate by a fixed angle
   - The reconstructed path is plotted to produce a simple 2D map of the robot’s trajectory in the environment.

---

## Setup

### 1. ESP32 Firmware

1. Flash the ESP32 with firmware that:
   - Initializes the OV2640 camera.
   - Connects to your Wi-Fi network.
   - Starts an HTTP server with:
     - One endpoint for frame streaming.
     - One endpoint for motor commands.

2. Note the ESP32’s:
   - **IP address**
   - **Port numbers**
   - **Endpoint paths**

You’ll need these in the Python script.

### 2. Python Environment

```bash
# Create and activate a virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install opencv-python numpy requests matplotlib pandas
