import numpy as np
import matplotlib.pyplot as plt

def analyze(path):
    data = np.genfromtxt(path, delimiter=",", names=True)

    t = data["t_us"] * 1e-6
    dt = np.median(np.diff(t))
    fs = 1 / dt

    axes = {
        "X": data["x_g"],
        "Y": data["y_g"],
        "Z": data["z_g"],
    }

    results = {}

    for name, signal in axes.items():
        vibration = signal - np.mean(signal)

        rms = np.sqrt(np.mean(vibration**2))
        peak = np.max(np.abs(vibration))
        crest = peak / rms

        window = np.hanning(len(vibration))
        spectrum = np.abs(np.fft.rfft(vibration * window))
        freq = np.fft.rfftfreq(len(vibration), dt)

        valid = freq >= 2
        dom = freq[valid][np.argmax(spectrum[valid])]

        results[name] = (rms, crest, dom, freq, spectrum)

    return fs, results

fs_b, base = analyze("../data/baseline/baseline_fan.csv")
fs_f, fault = analyze("../data/fault/fault_fan.csv")

print(f"Baseline sample rate: {fs_b:.2f} Hz")
print(f"Fault sample rate:    {fs_f:.2f} Hz\n")

for axis in ["X", "Y", "Z"]:
    brms, bc, bf, _, _ = base[axis]
    frms, fc, ff, _, _ = fault[axis]

    change = 100 * (frms - brms) / brms

    print(
        f"{axis}: "
        f"RMS {brms:.4f} -> {frms:.4f} g "
        f"({change:+.1f}%), "
        f"Crest {bc:.2f} -> {fc:.2f}, "
        f"Dominant {bf:.2f} -> {ff:.2f} Hz"
    )

# Plot Z axis because it was strongest in baseline
_, _, _, fb, sb = base["Z"]
_, _, _, ff, sf = fault["Z"]

plt.figure(figsize=(10, 5))
plt.plot(fb, sb, label="Baseline")
plt.plot(ff, sf, label="Imbalance")
plt.xlim(0, 200)
plt.xlabel("Frequency (Hz)")
plt.ylabel("FFT magnitude")
plt.title("SpectraGuard — Baseline vs. Imbalance")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("../figures/baseline_vs_fault.png", dpi=200)
plt.close()

print("\nSaved comparison plot to ../figures/baseline_vs_fault.png")
