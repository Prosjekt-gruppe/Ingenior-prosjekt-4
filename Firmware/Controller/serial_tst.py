import serial
import threading
import time

def send_data(ser):
        msg = "Mining bitcoin...\n"
        ser.write(msg.encode('utf-8'))
        print(f"Data sendt")
        time.sleep(1) # Simulate some processing time

def receive_data(ser):
    while True:
        if ser.in_waiting > 0:
            received_data = ser.readline().decode().strip()
            print(f"Received: {received_data}")
            time.sleep(0.1) # Check for incoming data frequently

#init serial port and bound
# bound rate on two ports must be the same
ser = serial.Serial('/dev/ttyUSB0', 115200)
print(ser.portstr)
time.sleep(0.5)

tx = threading.Thread(target=send_data, args=(ser,))
rx = threading.Thread(target=receive_data, args=(ser,), daemon=True)

tx.start()
rx.start()

while True:
    time.sleep(1)