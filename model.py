import warnings
warnings.filterwarnings("ignore")

import serial
import numpy as np
import joblib
import tensorflow as tf
import time
import csv
import os

tflite = tf.lite

CSV_FILE = "soil_ml_log.csv"

# create csv header
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Temperature_C",
            "Moisture_Percent",
            "pH",
            "EC",
            "Nitrogen",
            "Phosphorus",
            "Potassium",
            "Soil_Quality",
            "Recommended_Crop"
        ])


# load ML files
crop_scaler = joblib.load("crop_scaler.pkl")
crop_le = joblib.load("crop_label_encoder.pkl")

soil_scaler = joblib.load("soil_scaler.pkl")
soil_le = joblib.load("soil_label_encoder.pkl")

crop_int = tflite.Interpreter("crop_model.tflite")
crop_int.allocate_tensors()

soil_int = tflite.Interpreter("soil_model.tflite")
soil_int.allocate_tensors()


def run_tflite(interpreter, data):
    input_index = interpreter.get_input_details()[0]["index"]
    output_index = interpreter.get_output_details()[0]["index"]

    interpreter.set_tensor(input_index, data.astype(np.float32))
    interpreter.invoke()

    return interpreter.get_tensor(output_index)


# serial
ser = serial.Serial("/dev/ttyS0", 4800, timeout=1)

request = bytes([1, 0x03, 0x00, 0x00, 0x00, 0x07, 0x04, 0x08])

print("\n========== SMART SOIL ANALYSIS SYSTEM ==========\n")

# table header
header = (
    "| {0:<19} | {1:^6} | {2:^8} | {3:^4} | {4:^5} | {5:^12} | {6:^12} |"
    .format("Timestamp", "Temp", "Moisture", "pH", "EC", "Soil Quality", "Best Crop")
)

line = "-" * len(header)

print(line)
print(header)
print(line)


while True:

    try:
        ser.reset_input_buffer()
        ser.write(request)
        ser.flush()
        time.sleep(0.1)

        response = ser.read(19)

        if len(response) != 19:
            print("Sensor read failed")
            continue

        # parse sensor
        moisture = ((response[3] << 8) | response[4]) / 10
        temperature = ((response[5] << 8) | response[6]) / 10
        ec = (response[7] << 8) | response[8]
        ph = ((response[9] << 8) | response[10]) / 10
        nitrogen = (response[11] << 8) | response[12]
        phosphorus = (response[13] << 8) | response[14]
        potassium = (response[15] << 8) | response[16]

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # soil ML
        soil_features = np.array([[temperature, moisture, ec, ph, nitrogen, phosphorus, potassium]])
        soil_scaled = soil_scaler.transform(soil_features)
        soil_pred = run_tflite(soil_int, soil_scaled)
        soil_label = soil_le.inverse_transform([np.argmax(soil_pred)])[0]

        # crop ML
        humidity = 60
        crop_features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph]])
        crop_scaled = crop_scaler.transform(crop_features)
        crop_pred = run_tflite(crop_int, crop_scaled)
        crop_label = crop_le.inverse_transform([np.argmax(crop_pred)])[0]

        # terminal table output
        print(
            "| {0:<19} | {1:^6.1f} | {2:^8.1f} | {3:^4.1f} | {4:^5} | {5:^12} | {6:^12} |"
            .format(timestamp, temperature, moisture, ph, ec, soil_label, crop_label)
        )

        # csv logging
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                temperature,
                moisture,
                ph,
                ec,
                nitrogen,
                phosphorus,
                potassium,
                soil_label,
                crop_label
            ])

    except Exception as e:
        print("Error:", e)

    time.sleep(2)
