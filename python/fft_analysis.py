import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

DATA = Path("../data/baseline/baseline_fan.csv")
FIGURE = Path("../figures/baseline_fft.png")

data = np.genfromtxt(DATA, delimiter=",", names=True)

t = data["t_us"] * 1e-6
x = data["x_g"]
y = data["y_g"]
z = data["z_g"]

# Measure actual sampling rate from Arduino timestamps
dt = np.median(np.diff(t))
fs = 1.0 / dt

signals = {"X": x, "Y": y, "Z": z}

results = {}

for name, signal in signals.items():
    vibration = signal - np.mean(signal)

    rms = np.sqrt(np.mean(vibration**2))
    peak = np.max(np.abs(vibration))
    crest = peak / rms if rms > 0 else 0

    n = len(vibration)
    window = np.hanning(n)

    spectrum = np.fft.rfft(vibration * window)
    freqs = np.fft.rfftfreq(n, d=dt)
    amplitude = np.abs(spectrum)

    # Ignore near-DC components below 2 Hz
    valid = freqs >= 2
    dominant_index = np.argmax(amplitude[valid])
    dominant_freq = freqs[valid][dominant_index]

    results[name] = {
        "rms": rms,
        "crest": crest,
        "freq": dominant_freq,
        "amplitude": amplitude,
    }

# Select axis with strongest vibration RMS
best_axis = max(results, key=lambda k: results[k]["rms"])

print(f"Samples: {len(t)}")
print(f"Measured sample rate: {fs:.2f} Hz")

for axis in ["X", "Y", "Z"]:
    r = results[axis]
    print(
        f"{axis}: RMS={r['rms']:.4f} g, "
        f"Crest Factor={r['crest']:.2f}, "
        f"Dominant Frequency={r['freq']:.2f} Hz"
    )

print(f"Strongest vibration axis: {best_axis}")

plt.figure(figsize=(10, 5))

for axis in ["X", "Y", "Z"]:
    plt.plot(freqs, results[axis]["amplitude"], label=axis)

plt.xlim(0, min(200, fs / 2))
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT magnitude")
plt.title("SpectraGuard — Baseline Fan Vibration Spectrum")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

FIGURE.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(FIGURE, dpi=200)
plt.close()

print(f"Saved FFT plot to {FIGURE}")
