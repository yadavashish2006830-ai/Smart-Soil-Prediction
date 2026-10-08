import time
import serial
import csv
import os
import requests
from thingspeak_config import WRITE_API_KEY, UPDATE_URL

# settings
PORT = "/dev/ttyS0"
BAUDRATE = 4800
SENSOR_ID = 1
CSV_FILE = "sensor_data.csv"
THINGSPEAK_INTERVAL = 20   # seconds

ser = serial.Serial(
    port=PORT,
    baudrate=BAUDRATE,
    bytesize=8,
    parity=serial.PARITY_NONE,
    stopbits=1,
    timeout=1,
    xonxoff=True
)

request = bytes([SENSOR_ID, 0x03, 0x00, 0x00, 0x00, 0x07, 0x04, 0x08])

last_upload_time = 0

# csv header
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp", "Temperature_C", "Moisture_Pct",
            "EC", "pH", "Nitrogen", "Phosphorus", "Potassium"
        ])

# thingspeak function
def send_to_thingspeak(temp, moisture, ec, ph, n, p, k):
    payload = {
        "api_key": WRITE_API_KEY,
        "field1": temp,
        "field2": moisture,
        "field3": ec,
        "field4": ph,
        "field5": n,
        "field6": p,
        "field7": k
    }

    try:
        r = requests.post(UPDATE_URL, data=payload)
        print("ThingSpeak Entry ID:", r.text)
    except Exception as e:
        print("ThingSpeak Upload Error:", e)


print("\nPolling sensor and uploading to ThingSpeak...\n")

while True:
    try:
        ser.reset_input_buffer()
        ser.write(request)
        ser.flush()
        time.sleep(0.1)

        response = ser.read(19)

        if len(response) == 19:

            moisture = ((response[3] << 8) | response[4]) / 10
            temperature = ((response[5] << 8) | response[6]) / 10
            ec = (response[7] << 8) | response[8]
            ph = ((response[9] << 8) | response[10]) / 10
            nitrogen = (response[11] << 8) | response[12]
            phosphorus = (response[13] << 8) | response[14]
            potassium = (response[15] << 8) | response[16]

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # save csv
            with open(CSV_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, temperature, moisture,
                    ec, ph, nitrogen, phosphorus, potassium
                ])

            print(f"[{timestamp}] Temp={temperature}C Moisture={moisture}% EC={ec} pH={ph}")

            # thingspeak rate control
            current_time = time.time()
            if current_time - last_upload_time > THINGSPEAK_INTERVAL:
                send_to_thingspeak(
                    temperature, moisture, ec, ph,
                    nitrogen, phosphorus, potassium
                )
                last_upload_time = current_time

        else:
            print("Invalid sensor response")

    except Exception as e:
        print("Error:", e)

    time.sleep(2)
