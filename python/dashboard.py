from pathlib import Path
from collections import deque
import glob
import threading
import time

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import serial


# -----------------------------
# Configuration
# -----------------------------
BAUD = 460800
FS = 400.0
WINDOW_SECONDS = 2
N = int(FS * WINDOW_SECONDS)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_FILE = ROOT / "data/baseline/combined_baseline.csv"
FAULT_FILE = ROOT / "data/fault/combined_fault.csv"


# -----------------------------
# Signal processing
# -----------------------------
def features(signal, fs=FS):
    signal = np.asarray(signal, dtype=float)
    centered = signal - np.mean(signal)

    rms = np.sqrt(np.mean(centered**2))

    peak = np.max(np.abs(centered))
    crest = peak / rms if rms > 0 else 0.0

    window = np.hanning(len(centered))
    spectrum = np.abs(np.fft.rfft(centered * window))
    freqs = np.fft.rfftfreq(len(centered), d=1.0 / fs)

    valid = freqs >= 2.0
    dominant = freqs[valid][np.argmax(spectrum[valid])]

    return rms, crest, dominant, freqs, spectrum


def vibration_rms(data):
    rx = features(data["x_g"])[0]
    ry = features(data["y_g"])[0]
    rz = features(data["z_g"])[0]

    return np.sqrt(rx**2 + ry**2 + rz**2)


def load_reference(path):
    return np.genfromtxt(path, delimiter=",", names=True)


# -----------------------------
# Automatic fault threshold
# -----------------------------
baseline = load_reference(BASELINE_FILE)
fault = load_reference(FAULT_FILE)

baseline_vibration = vibration_rms(baseline)
fault_vibration = vibration_rms(fault)

FAULT_THRESHOLD = (baseline_vibration + fault_vibration) / 2.0

axis_names = ["x_g", "y_g", "z_g"]

response_ratios = []

for axis in axis_names:
    base_rms = features(baseline[axis])[0]
    fault_rms = features(fault[axis])[0]
    response_ratios.append(fault_rms / base_rms)

DETECTION_AXIS = axis_names[np.argmax(response_ratios)]

axis_label = DETECTION_AXIS[0].upper()


# -----------------------------
# Find Arduino automatically
# -----------------------------
ports = glob.glob("/dev/cu.usbmodem*")

if not ports:
    raise RuntimeError("Arduino Due serial port not found.")

PORT = ports[0]

print(f"Arduino port: {PORT}")
print(f"Healthy reference RMS: {baseline_vibration:.4f} g")
print(f"Fault reference RMS:   {fault_vibration:.4f} g")
print(f"Detection threshold:   {FAULT_THRESHOLD:.4f} g")
print(f"Most responsive axis:  {axis_label}")


# -----------------------------
# Serial acquisition
# -----------------------------
t_data = deque(maxlen=N)
x_data = deque(maxlen=N)
y_data = deque(maxlen=N)
z_data = deque(maxlen=N)
mic_data = deque(maxlen=N)

lock = threading.Lock()
running = True

ser = serial.Serial(PORT, BAUD, timeout=1)

# Opening the Due programming port resets it
time.sleep(3)


def acquisition():
    global running

    while running:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            parts = line.split(",")

            if len(parts) != 5:
                continue

            t, x, y, z, mic = map(float, parts)

            with lock:
                t_data.append(t)
                x_data.append(x)
                y_data.append(y)
                z_data.append(z)
                mic_data.append(mic)

        except (ValueError, serial.SerialException):
            continue


thread = threading.Thread(target=acquisition, daemon=True)
thread.start()


# -----------------------------
# Dashboard
# -----------------------------
fig, axes = plt.subplots(2, 2, figsize=(13, 8))

ax_vib_time = axes[0, 0]
ax_mic_time = axes[0, 1]
ax_vib_fft = axes[1, 0]
ax_mic_fft = axes[1, 1]

vib_time_line, = ax_vib_time.plot([], [])
mic_time_line, = ax_mic_time.plot([], [])
vib_fft_line, = ax_vib_fft.plot([], [])
mic_fft_line, = ax_mic_fft.plot([], [])

ax_vib_time.set_title(f"Live vibration — {axis_label} axis")
ax_vib_time.set_xlabel("Time (s)")
ax_vib_time.set_ylabel("Acceleration (g)")
ax_vib_time.grid(True, alpha=0.3)

ax_mic_time.set_title("Live acoustic signal")
ax_mic_time.set_xlabel("Time (s)")
ax_mic_time.set_ylabel("ADC value")
ax_mic_time.grid(True, alpha=0.3)

ax_vib_fft.set_title("Vibration FFT")
ax_vib_fft.set_xlabel("Frequency (Hz)")
ax_vib_fft.set_ylabel("FFT magnitude")
ax_vib_fft.set_xlim(0, 200)
ax_vib_fft.grid(True, alpha=0.3)

ax_mic_fft.set_title("Acoustic FFT")
ax_mic_fft.set_xlabel("Frequency (Hz)")
ax_mic_fft.set_ylabel("FFT magnitude")
ax_mic_fft.set_xlim(0, 200)
ax_mic_fft.grid(True, alpha=0.3)

status_text = fig.text(
    0.5,
    0.97,
    "Collecting data...",
    ha="center",
    va="top",
    fontsize=16,
)

metrics_text = fig.text(
    0.5,
    0.92,
    "",
    ha="center",
    va="top",
    fontsize=10,
)


def update(_):
    with lock:
        if len(x_data) < 128:
            status_text.set_text(
                f"Collecting data... {len(x_data)}/{N} samples"
            )
            return

        x = np.array(x_data)
        y = np.array(y_data)
        z = np.array(z_data)
        mic = np.array(mic_data)

    signals = {
        "X": x,
        "Y": y,
        "Z": z,
    }

    detection_signal = signals[axis_label]

    rx = features(x)[0]
    ry = features(y)[0]
    rz = features(z)[0]

    total_vibration_rms = np.sqrt(rx**2 + ry**2 + rz**2)

    vrms, vcrest, vdom, vf, vs = features(detection_signal)
    mrms, mcrest, mdom, mf, ms = features(mic)

    if total_vibration_rms > FAULT_THRESHOLD:
        status = "IMBALANCE DETECTED"
    else:
        status = "HEALTHY"

    status_text.set_text(
        f"SpectraGuard — {status}"
    )

    metrics_text.set_text(
        f"Vibration RMS: {total_vibration_rms:.4f} g   |   "
        f"{axis_label}-axis crest: {vcrest:.2f}   |   "
        f"Vibration dominant: {vdom:.1f} Hz   |   "
        f"Mic RMS: {mrms:.1f} ADC   |   "
        f"Mic crest: {mcrest:.2f}   |   "
        f"Acoustic dominant: {mdom:.1f} Hz"
    )

    seconds = np.arange(len(detection_signal)) / FS

    vib_time_line.set_data(seconds, detection_signal)
    mic_time_line.set_data(seconds, mic)

    ax_vib_time.set_xlim(0, max(WINDOW_SECONDS, seconds[-1]))

    vib_min = np.min(detection_signal)
    vib_max = np.max(detection_signal)
    vib_pad = max((vib_max - vib_min) * 0.10, 0.01)
    ax_vib_time.set_ylim(vib_min - vib_pad, vib_max + vib_pad)

    mic_min = np.min(mic)
    mic_max = np.max(mic)
    mic_pad = max((mic_max - mic_min) * 0.10, 20)
    ax_mic_time.set_xlim(0, max(WINDOW_SECONDS, seconds[-1]))
    ax_mic_time.set_ylim(mic_min - mic_pad, mic_max + mic_pad)

    vib_fft_line.set_data(vf, vs)
    mic_fft_line.set_data(mf, ms)

    vib_fft_max = np.max(vs[vf <= 200])
    mic_fft_max = np.max(ms[mf <= 200])

    ax_vib_fft.set_ylim(0, max(vib_fft_max * 1.10, 1))
    ax_mic_fft.set_ylim(0, max(mic_fft_max * 1.10, 1))

    return (
        vib_time_line,
        mic_time_line,
        vib_fft_line,
        mic_fft_line,
        status_text,
        metrics_text,
    )


ani = FuncAnimation(
    fig,
    update,
    interval=200,
    cache_frame_data=False,
)

plt.tight_layout(rect=[0, 0, 1, 0.88])


def close_dashboard(_):
    global running
    running = False

    if ser.is_open:
        ser.close()


fig.canvas.mpl_connect("close_event", close_dashboard)

plt.show()
