import numpy as np
import matplotlib.pyplot as plt

BASE = "../data/baseline/combined_baseline.csv"
FAULT = "../data/fault/combined_fault.csv"

def load_and_analyze(path):
    data = np.genfromtxt(path, delimiter=",", names=True)

    t = data["t_us"] * 1e-6
    dt = np.median(np.diff(t))
    fs = 1.0 / dt

    signals = {
        "X": data["x_g"],
        "Y": data["y_g"],
        "Z": data["z_g"],
        "MIC": data["mic"],
    }

    results = {}

    for name, signal in signals.items():
        centered = signal - np.mean(signal)

        rms = np.sqrt(np.mean(centered**2))
        peak = np.max(np.abs(centered))
        crest = peak / rms if rms > 0 else 0

        window = np.hanning(len(centered))
        spectrum = np.abs(np.fft.rfft(centered * window))
        freqs = np.fft.rfftfreq(len(centered), dt)

        valid = freqs >= 2
        dominant_freq = freqs[valid][np.argmax(spectrum[valid])]

        results[name] = {
            "rms": rms,
            "crest": crest,
            "freq": dominant_freq,
            "freqs": freqs,
            "spectrum": spectrum,
        }

    return fs, results

fs_b, base = load_and_analyze(BASE)
fs_f, fault = load_and_analyze(FAULT)

print(f"Baseline sample rate: {fs_b:.2f} Hz")
print(f"Fault sample rate:    {fs_f:.2f} Hz\n")

for name in ["X", "Y", "Z", "MIC"]:
    b = base[name]
    f = fault[name]

    rms_change = 100 * (f["rms"] - b["rms"]) / b["rms"]

    print(
        f"{name}: "
        f"RMS {b['rms']:.4f} -> {f['rms']:.4f} "
        f"({rms_change:+.1f}%), "
        f"Crest {b['crest']:.2f} -> {f['crest']:.2f}, "
        f"Dominant {b['freq']:.2f} -> {f['freq']:.2f} Hz"
    )

# Vibration comparison — Z axis
plt.figure(figsize=(10, 5))
plt.plot(base["Z"]["freqs"], base["Z"]["spectrum"], label="Healthy")
plt.plot(fault["Z"]["freqs"], fault["Z"]["spectrum"], label="Imbalance")
plt.xlim(0, 200)
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT magnitude")
plt.title("SpectraGuard — Vibration: Healthy vs Imbalance")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../figures/combined_vibration_comparison.png", dpi=200)
plt.close()

# Acoustic comparison
plt.figure(figsize=(10, 5))
plt.plot(base["MIC"]["freqs"], base["MIC"]["spectrum"], label="Healthy")
plt.plot(fault["MIC"]["freqs"], fault["MIC"]["spectrum"], label="Imbalance")
plt.xlim(0, 200)
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT magnitude")
plt.title("SpectraGuard — Acoustic: Healthy vs Imbalance")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../figures/combined_acoustic_comparison.png", dpi=200)
plt.close()

print("\nSaved:")
print("../figures/combined_vibration_comparison.png")
print("../figures/combined_acoustic_comparison.png")
