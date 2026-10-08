import serial

ser = serial.Serial("/dev/ttyS0", 9600, timeout=1)

while True:
    data = ser.readline()
    print("Raw:", data)
