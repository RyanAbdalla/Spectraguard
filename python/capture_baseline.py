import csv
import time
import serial

PORT = "/dev/cu.usbmodem1101"
BAUD = 460800
NUM_SAMPLES = 4000

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
ser.reset_input_buffer()

output_file = "../data/baseline/baseline_fan.csv"

count = 0

with open(output_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["t_us", "x_g", "y_g", "z_g"])

    while count < NUM_SAMPLES:
        line = ser.readline().decode(errors="ignore").strip()
        parts = line.split(",")

        if len(parts) == 4:
            try:
                row = [float(v) for v in parts]
                writer.writerow(row)
                count += 1
            except ValueError:
                pass

ser.close()

print(f"Saved {count} samples to {output_file}")