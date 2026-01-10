import numpy as np
import matplotlib.pyplot as plt


def verify_audio_signals(s1, s2, threshold=0.15):
    n, m = len(s1), len(s2)

    # 1. Standard DTW for alignment (Numerical Levenshtein)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(s1[i - 1] - s2[j - 1])
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j], dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1]
            )

    # 2. Backtrack to find the optimal path
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
    path.reverse()

    # 3. Create Aligned Signal B (Mapping B's indices to A's timeline)
    aligned_s2 = np.zeros(len(s1))
    for idx_a, idx_b in path:
        aligned_s2[idx_a] = s2[idx_b]

    # 4. Calculate Difference and identify Glitch indices
    diff = np.abs(s1 - aligned_s2)
    glitches = diff > threshold

    # 5. Visualization
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    # --- View 1: Original (Before Alignment) ---
    ax1.plot(s1, label="Reference A", color="blue", alpha=0.5)
    ax1.plot(
        s2,
        label="Original Target B (Un-aligned)",
        color="red",
        alpha=0.5,
        linestyle="--",
    )
    ax1.set_title("1. Original Signals (Shows Time/Phase Shift)")
    ax1.legend(loc="upper right")

    # --- View 2: Aligned (After Time-Warping) ---
    ax2.plot(s1, label="Reference A", color="blue", alpha=0.6)
    ax2.plot(aligned_s2, label="Aligned Target B", color="orange", alpha=0.8)
    ax2.set_title("2. Aligned Signals (Temporal shifts removed)")
    ax2.legend(loc="upper right")

    # --- View 3: Glitch Map ---
    ax3.fill_between(range(len(diff)), diff, color="red", alpha=0.2)
    ax3.plot(diff, color="red", linewidth=0.8, label="Difference Magnitude")

    # Highlight the specific glitch zones
    ax3.fill_between(
        range(len(diff)),
        0,
        1,
        where=glitches,
        color="darkred",
        alpha=0.6,
        label="Glitch Detected",
    )

    ax3.set_title("3. Verification Result (Glitches Highlighted)")
    ax3.set_ylim(0, max(diff) * 1.5)
    ax3.legend(loc="upper right")
    ax3.set_xlabel("Sample Index (on Reference Timeline)")

    plt.tight_layout()
    plt.show()


# --- Example Usage with Simulated Data ---
t = np.linspace(0, 1, 800)
# Reference A: A simple decaying sine wave
sig_a = np.sin(2 * np.pi * 5 * t) * np.exp(-t)

# Target B: Delayed (shifted index), different frequency, and added glitches
sig_b = np.sin(2 * np.pi * 5.2 * t + 0.3) * np.exp(-t)
sig_b[300:320] += 0.4  # Glitch 1: Spike
sig_b[600:630] = 0  # Glitch 2: Signal Dropout

verify_audio_signals(sig_a, sig_b)
