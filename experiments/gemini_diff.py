import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import resample


def load_and_preprocess(file_path, duration_sec=0.5, target_sr=1000):
    """Loads a wav file, converts to mono, clips duration, and downsamples."""
    sr, data = wavfile.read(file_path)

    # Convert to mono if stereo
    if len(data.shape) > 1:
        data = data.mean(axis=1)

    # Take only the first few seconds to keep the matrix manageable
    num_samples = int(sr * duration_sec)
    data = data[:num_samples]

    # Downsample significantly (e.g., from 44.1kHz to 1kHz)
    num_resampled = int(len(data) * target_sr / sr)
    resampled_data = resample(data, num_resampled)

    # Normalize amplitude to range [-1, 1] for fair comparison
    resampled_data = resampled_data / np.max(np.abs(resampled_data))

    return resampled_data


def compute_dtw_audio(s1, s2):
    """Standard DTW algorithm (numerical Levenshtein)."""
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
        steps = [dtw_matrix[i - 1, j - 1], dtw_matrix[i - 1, j], dtw_matrix[i, j - 1]]
        best_step = np.argmin(steps)
        if best_step == 0:
            i, j = i - 1, j - 1
        elif best_step == 1:
            i -= 1
        else:
            j -= 1
    return path, dtw_matrix[n, m]


# --- Execution ---
# Replace these with your actual .wav file paths
# audio_a = load_and_preprocess("recording1.wav")
# audio_b = load_and_preprocess("recording2.wav")

# For demonstration, we'll simulate audio-like signals
t = np.linspace(0, 1, 300)
audio_a = np.sin(2 * np.pi * 5 * t) * np.exp(-t)
audio_b = np.sin(2 * np.pi * 5.5 * t + 0.2) * np.exp(-t)

path, distance = compute_dtw_audio(audio_a, audio_b)

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(audio_a, label="Audio A", color="blue", alpha=0.7)
plt.plot(audio_b + 2, label="Audio B (Offset)", color="red", alpha=0.7)

# Draw alignment paths (the "diff" markers)
for i in range(0, len(path), 5):  # Plot every 5th link to avoid clutter
    idx_a, idx_b = path[i]
    plt.plot(
        [idx_a, idx_b],
        [audio_a[idx_a], audio_b[idx_b] + 2],
        color="black",
        alpha=0.2,
        linewidth=0.5,
    )

plt.title(f"Audio Waveform 'Diff' - Alignment Distance: {distance:.2f}")
plt.legend()
plt.show()
