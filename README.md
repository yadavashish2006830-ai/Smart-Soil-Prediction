# Smart Soil Quality Prediction System

An IoT system that reads real-time soil parameters from a 7-in-1 NPK sensor over RS-485, runs on-device TFLite machine learning to classify soil quality and recommend crops, logs data to CSV, and streams readings to ThingSpeak for cloud monitoring.

---

## Table of Contents
- [Features](#features)
- [System Architecture](#system-architecture)
- [Hardware Requirements](#hardware-requirements)
- [File Structure](#file-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Output](#output)
- [ML Models](#ml-models)
- [ThingSpeak Integration](#thingspeak-integration)

---

## Features

- Real-time polling of 7 soil parameters: Temperature, Moisture, EC, pH, N, P, K
- On-device ML inference using TensorFlow Lite (no cloud compute required)
- Dual model pipeline: soil quality classification + crop recommendation
- Automatic CSV logging with timestamps
- ThingSpeak cloud upload every 20 seconds (rate-limited)
- Live structured terminal output table

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Sensing                                      │
│  7-in-1 NPK Sensor ──RS-485──► Raspberry Pi UART        │
│                                (/dev/ttyS0, 4800 baud)  │
└─────────────────────────┬───────────────────────────────┘
                          │ 19-byte Modbus RTU response
┌─────────────────────────▼───────────────────────────────┐
│  Layer 2 — Storage & Transmission                       │
│  ├─ Local CSV (sensor_data.csv / soil_ml_log.csv)       │
│  └─ ThingSpeak HTTP POST every 20s                      │
└─────────────────────────┬───────────────────────────────┘
                          │ NumPy feature array
┌─────────────────────────▼───────────────────────────────┐
│  Layer 3 — ML Inference (TFLite)                        │
│  ├─ soil_model.tflite  → Soil Quality label             │
│  └─ crop_model.tflite  → Recommended Crop               │
└─────────────────────────────────────────────────────────┘
```

---

## Hardware Requirements

| Component | Details |
|---|---|
| Single-Board Computer | Raspberry Pi (any model with UART) |
| Soil Sensor | 7-in-1 NPK Sensor, Modbus RTU over RS-485 |
| Interface | RS-485 to TTL/USB adapter |
| Network | Wi-Fi or Ethernet for ThingSpeak |

---

## File Structure

```
.
├── soil_main.py            # Sensor polling + CSV logging + ThingSpeak upload
├── model.py                # Sensor polling + ML inference + CSV logging
├── check_connection.py     # Serial connection test utility
├── thingspeak_config.py    # ThingSpeak API key and endpoint
│
├── crop_model.tflite       # Crop recommendation TFLite model
├── soil_model.tflite       # Soil quality classification TFLite model
├── crop_scaler.pkl         # MinMaxScaler for crop model inputs
├── soil_scaler.pkl         # MinMaxScaler for soil model inputs
├── crop_label_encoder.pkl  # LabelEncoder for crop output classes
├── soil_label_encoder.pkl  # LabelEncoder for soil quality classes
│
├── sensor_data.csv         # Raw sensor log (created automatically)
└── soil_ml_log.csv         # Sensor + ML prediction log (created automatically)
```

---

## Setup & Installation

### 1. Install Python dependencies

```bash
pip install pyserial numpy joblib tensorflow requests
```

### 2. Enable UART on Raspberry Pi

```bash
sudo raspi-config
# Interface Options → Serial Port
# Disable login shell over serial: No
# Enable serial port hardware: Yes
```

### 3. Clone / copy all project files

Ensure all `.tflite` and `.pkl` files are in the **same directory** as the Python scripts.

### 4. Verify serial connection

```bash
python3 check_connection.py
```

You should see raw bytes printed if the sensor is connected and powered correctly.

---

## Configuration

Edit `thingspeak_config.py` to set your ThingSpeak channel credentials:

```python
WRITE_API_KEY = "YOUR_WRITE_API_KEY"
UPDATE_URL    = "https://api.thingspeak.com/update"
```

To change the serial port or baud rate, edit the constants at the top of `soil_main.py` or `model.py`:

```python
PORT      = "/dev/ttyS0"   # Change to /dev/ttyUSB0 for USB-RS485 adapter
BAUDRATE  = 4800
```

---

## Running the System

### Sensor-only mode (with ThingSpeak upload)

```bash
python3 soil_main.py
```

### Full ML inference mode

```bash
python3 model.py
```

Both scripts run continuously. Press `Ctrl+C` to stop.

---

## Output

### Terminal (model.py)

```
========== SMART SOIL ANALYSIS SYSTEM ==========

----------------------------------------------------------------------
| Timestamp           |  Temp  | Moisture |  pH  |  EC   | Soil Quality | Best Crop  |
----------------------------------------------------------------------
| 2026-02-11 14:30:03 |  20.0  |  100.0   | 6.2  |  495  |   Moderate   |   grapes   |
```

### CSV Log (soil_ml_log.csv)

```
Timestamp,Temperature_C,Moisture_Percent,pH,EC,Nitrogen,Phosphorus,Potassium,Soil_Quality,Recommended_Crop
2026-02-11 14:30:03,20.0,100.0,6.2,495,64,195,189,Moderate,grapes
```

---

## ML Models

| Model | Input Features | Output |
|---|---|---|
| `soil_model.tflite` | Temperature, Moisture, EC, pH, N, P, K | Soil quality class (e.g., Moderate, Good) |
| `crop_model.tflite` | N, P, K, Temperature, Humidity (fixed 60%), pH | Recommended crop (e.g., grapes, rice) |

Both models require their corresponding `_scaler.pkl` and `_label_encoder.pkl` files to be present at runtime.

---

## ThingSpeak Integration

| ThingSpeak Field | Sensor Parameter |
|---|---|
| field1 | Temperature (°C) |
| field2 | Moisture (%) |
| field3 | EC (µS/cm) |
| field4 | pH |
| field5 | Nitrogen (mg/kg) |
| field6 | Phosphorus (mg/kg) |
| field7 | Potassium (mg/kg) |

Uploads are rate-limited to once every **20 seconds** (`THINGSPEAK_INTERVAL`) to comply with ThingSpeak's free-tier minimum interval.
