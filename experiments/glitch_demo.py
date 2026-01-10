import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import resample


def detect_audio_glitches(file1, file2, threshold=0.1):
    # 1. Load and normalize audio
    def process_audio(path):
        sr, data = wavfile.read(path)
        if len(data.shape) > 1:
            data = data.mean(axis=1)  # Mono
        data = data / np.max(np.abs(data))  # Normalize
        # Downsample to 2000Hz for performance
        return resample(data, int(len(data) * 2000 / sr))

    # s1 = process_audio(file1)
    # s2 = process_audio(file2)

    # FOR DEMO: Generating two signals with a "glitch"
    t = np.linspace(0, 1, 1000)
    s1 = np.sin(2 * np.pi * 5 * t)
    s2 = np.sin(2 * np.pi * 5.1 * t + 0.1)  # Frequency/phase shift
    s2[400:420] += 0.5  # Adding a "Glitch" in the middle of Signal B

    # 2. Compute DTW to find the alignment path
    n, m = len(s1), len(s2)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(s1[i - 1] - s2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j], dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1]
            )

    # Backtrack path
    path = []
    i, j = n, m
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        best_step = np.argmin(
            [dtw_matrix[i - 1, j - 1], dtw_matrix[i - 1, j], dtw_matrix[i, j - 1]]
        )
        if best_step == 0:
            i, j = i - 1, j - 1
        elif best_step == 1:
            i -= 1
        else:
            j -= 1
    path.reverse()

    # 3. Align signals using the path
    # We map Signal B's values onto Signal A's timeline
    aligned_s2 = np.zeros(len(s1))
    for idx_a, idx_b in path:
        aligned_s2[idx_a] = s2[idx_b]

    # 4. Calculate Difference (The "Glitch" Map)
    diff = np.abs(s1 - aligned_s2)
    glitches = diff > threshold

    # 5. Visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Top Plot: The Overlap
    ax1.plot(s1, label="Reference (A)", color="blue", alpha=0.6)
    ax1.plot(aligned_s2, label="Aligned Target (B)", color="orange", alpha=0.6)
    ax1.set_title("Aligned Waveforms (Time-shifted to match)")
    ax1.legend()

    # Bottom Plot: The Glitches
    ax2.fill_between(
        range(len(diff)), diff, color="red", alpha=0.3, label="Difference Magnitude"
    )
    ax2.plot(diff, color="red", linewidth=0.5)

    # Highlight specific glitch areas with a vertical bar
    ax2.fill_between(
        range(len(diff)),
        0,
        1,
        where=glitches,
        color="darkred",
        alpha=0.5,
        label="Glitch Detected",
    )

    ax2.set_title("Difference Map (Glitches highlighted in Red)")
    ax2.set_ylim(0, max(diff) * 1.2)
    ax2.legend()

    plt.tight_layout()
    plt.show()


# Run the detector
detect_audio_glitches(None, None)
