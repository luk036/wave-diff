import argparse

# import matplotlib.patches as mpatches
import sys
import warnings
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from scipy import signal

warnings.filterwarnings("ignore")


class EditOperation(Enum):
    """Enum for edit operations in waveform comparison"""

    MATCH = 0
    INSERT = 1  # Additional samples in waveform2
    DELETE = 2  # Missing samples in waveform2
    SUBSTITUTE = 3  # Different amplitude
    TIME_SHIFT = 4  # Time alignment difference


class WaveformComparator:
    """Main class for waveform comparison using edit distance techniques"""

    def __init__(self, window_size=50, threshold=0.1, time_warping=True):
        """
        Initialize waveform comparator

        Parameters:
        window_size: Size of sliding window for comparison
        threshold: Amplitude difference threshold for substitution
        time_warping: Enable dynamic time warping for alignment
        """
        self.window_size = window_size
        self.threshold = threshold
        self.time_warping = time_warping

    def load_waveform(self, filepath, is_signal=False, sampling_rate=1000):
        """
        Load waveform from file or generate synthetic signal

        Parameters:
        filepath: Path to waveform file or signal type
        is_signal: If True, generate synthetic signal
        sampling_rate: Sampling rate in Hz
        """
        if is_signal:
            # Generate synthetic waveform
            duration = 2.0  # seconds
            t = np.linspace(0, duration, int(sampling_rate * duration))

            if filepath == "sine":
                waveform = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
            elif filepath == "square":
                waveform = signal.square(2 * np.pi * 3 * t)  # 3 Hz square wave
            elif filepath == "triangle":
                waveform = signal.sawtooth(
                    2 * np.pi * 4 * t, width=0.5
                )  # 4 Hz triangle
            elif filepath == "chirp":
                waveform = signal.chirp(t, f0=1, f1=20, t1=duration, method="linear")
            elif filepath == "ecg":
                # Simulated ECG-like signal
                waveform = np.sin(2 * np.pi * 1.2 * t)
                waveform += 0.5 * np.sin(2 * np.pi * 5 * t)
                waveform += 0.2 * np.sin(2 * np.pi * 20 * t)
                waveform += 0.1 * np.random.randn(len(t))
            else:
                # Default sine with noise
                waveform = np.sin(2 * np.pi * 5 * t) + 0.1 * np.random.randn(len(t))

            return waveform, t, sampling_rate

        else:
            # Load from text file (assumes time, amplitude columns)
            try:
                data = np.loadtxt(filepath)
                if data.ndim == 1:
                    # Single column, assume amplitude only
                    waveform = data
                    t = np.arange(len(waveform))
                    sampling_rate = 1000  # default
                else:
                    # Two columns: time and amplitude
                    t = data[:, 0]
                    waveform = data[:, 1]
                    if len(t) > 1:
                        sampling_rate = 1.0 / (t[1] - t[0])
                    else:
                        sampling_rate = 1000
                return waveform, t, sampling_rate
            except Exception:
                # Try CSV
                data = np.genfromtxt(filepath, delimiter=",", skip_header=1)
                if data.ndim == 1:
                    waveform = data
                    t = np.arange(len(waveform))
                    sampling_rate = 1000
                else:
                    t = data[:, 0]
                    waveform = data[:, 1]
                    if len(t) > 1:
                        sampling_rate = 1.0 / (t[1] - t[0])
                    else:
                        sampling_rate = 1000
                return waveform, t, sampling_rate

    def normalize_waveform(self, waveform):
        """Normalize waveform to range [-1, 1]"""
        if len(waveform) == 0:
            return waveform
        min_val = np.min(waveform)
        max_val = np.max(waveform)
        if max_val - min_val > 0:
            return 2 * (waveform - min_val) / (max_val - min_val) - 1
        return waveform

    def dynamic_time_warping(self, w1, w2):
        """
        Perform Dynamic Time Warping for waveform alignment

        Returns:
        warp_path: Alignment path between waveforms
        cost: DTW distance
        """
        n, m = len(w1), len(w2)
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0

        # Compute DTW matrix
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(w1[i - 1] - w2[j - 1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i - 1, j],  # deletion
                    dtw_matrix[i, j - 1],  # insertion
                    dtw_matrix[i - 1, j - 1],  # match/substitute
                )

        # Backtrack to find warp path
        i, j = n, m
        warp_path = []

        while i > 0 or j > 0:
            warp_path.append((i - 1, j - 1))
            if i > 0 and j > 0:
                min_val = min(
                    dtw_matrix[i - 1, j - 1], dtw_matrix[i - 1, j], dtw_matrix[i, j - 1]
                )
                if dtw_matrix[i - 1, j - 1] == min_val:
                    i -= 1
                    j -= 1
                elif dtw_matrix[i - 1, j] == min_val:
                    i -= 1
                else:
                    j -= 1
            elif i > 0:
                i -= 1
            else:
                j -= 1

        warp_path.reverse()
        return warp_path, dtw_matrix[n, m]

    def sliding_window_distance(self, w1, w2):
        """
        Calculate edit distance using sliding window approach

        Returns:
        operations: List of edit operations
        aligned_w1, aligned_w2: Aligned waveforms
        """
        if self.time_warping and len(w1) > 0 and len(w2) > 0:
            # Use DTW for alignment
            warp_path, distance = self.dynamic_time_warping(w1, w2)

            # Create aligned waveforms
            aligned_w1 = []
            aligned_w2 = []
            operations = []

            for i, j in warp_path:
                aligned_w1.append(w1[i])
                aligned_w2.append(w2[j])

                if i >= len(w1) or j >= len(w2):
                    operations.append(EditOperation.TIME_SHIFT)
                else:
                    diff = abs(w1[i] - w2[j])
                    if diff < self.threshold:
                        operations.append(EditOperation.MATCH)
                    else:
                        operations.append(EditOperation.SUBSTITUTE)

            return operations, np.array(aligned_w1), np.array(aligned_w2), distance

        else:
            # Simple sliding window comparison
            n, m = len(w1), len(w2)
            max_len = max(n, m)

            aligned_w1 = []
            aligned_w2 = []
            operations = []

            for k in range(max_len):
                if k < n and k < m:
                    val1 = w1[k]
                    val2 = w2[k]
                    aligned_w1.append(val1)
                    aligned_w2.append(val2)

                    diff = abs(val1 - val2)
                    if diff < self.threshold:
                        operations.append(EditOperation.MATCH)
                    else:
                        operations.append(EditOperation.SUBSTITUTE)

                elif k < n:
                    # Deletion in w2
                    aligned_w1.append(w1[k])
                    aligned_w2.append(0)  # Padding
                    operations.append(EditOperation.DELETE)

                else:
                    # Insertion in w2
                    aligned_w1.append(0)  # Padding
                    aligned_w2.append(w2[k])
                    operations.append(EditOperation.INSERT)

            # Calculate simple edit distance
            distance = sum(1 for op in operations if op != EditOperation.MATCH)

            return operations, np.array(aligned_w1), np.array(aligned_w2), distance

    def visualize_comparison(
        self,
        w1,
        w2,
        t1,
        t2,
        operations,
        filename1="Waveform 1",
        filename2="Waveform 2",
        show_operations=True,
        show_matrix=True,
        save_plot=False,
        output_file="waveform_comparison.png",
    ):
        """
        Create comprehensive visualization of waveform comparison
        """
        fig = plt.figure(figsize=(16, 12))

        # Create layout
        if show_matrix:
            gs = plt.GridSpec(3, 2, height_ratios=[2, 2, 1], hspace=0.3, wspace=0.3)
        else:
            gs = plt.GridSpec(2, 2, height_ratios=[2, 1], hspace=0.3, wspace=0.3)

        # Color mapping for operations
        op_colors = {
            EditOperation.MATCH: "green",
            EditOperation.INSERT: "blue",
            EditOperation.DELETE: "red",
            EditOperation.SUBSTITUTE: "orange",
            EditOperation.TIME_SHIFT: "purple",
        }

        op_labels = {
            EditOperation.MATCH: "Match",
            EditOperation.INSERT: "Insertion",
            EditOperation.DELETE: "Deletion",
            EditOperation.SUBSTITUTE: "Substitution",
            EditOperation.TIME_SHIFT: "Time Shift",
        }

        # 1. Original waveforms (side by side)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(
            t1[: len(w1)], w1[: len(w1)], "b-", linewidth=2, alpha=0.7, label=filename1
        )
        ax1.set_title(f"Original {filename1}", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Amplitude")
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim(-1.2, 1.2)

        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(
            t2[: len(w2)], w2[: len(w2)], "r-", linewidth=2, alpha=0.7, label=filename2
        )
        ax2.set_title(f"Original {filename2}", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Amplitude")
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_ylim(-1.2, 1.2)

        # 2. Aligned waveforms with edit operations
        ax3 = fig.add_subplot(gs[1, :])

        # Create time axis for aligned waveforms
        t_aligned = np.arange(len(operations))

        # Plot aligned waveforms
        ax3.plot(
            t_aligned,
            w1[: len(operations)],
            "b-",
            linewidth=2,
            alpha=0.6,
            label=f"Aligned {filename1}",
        )
        ax3.plot(
            t_aligned,
            w2[: len(operations)],
            "r-",
            linewidth=2,
            alpha=0.6,
            label=f"Aligned {filename2}",
        )

        # Highlight differences
        if show_operations:
            for i, op in enumerate(operations):
                if op != EditOperation.MATCH:
                    # Add colored region
                    color = op_colors[op]
                    rect = Rectangle(
                        (i - 0.5, -1.2), 1, 2.4, alpha=0.2, color=color, zorder=0
                    )
                    ax3.add_patch(rect)

                    # Add marker at the difference point
                    ax3.plot(i, w1[i] if i < len(w1) else 0, "b.", markersize=8)
                    ax3.plot(i, w2[i] if i < len(w2) else 0, "r.", markersize=8)

                    # Connect with line if substitution
                    if op == EditOperation.SUBSTITUTE and i < min(len(w1), len(w2)):
                        ax3.plot([i, i], [w1[i], w2[i]], "k--", alpha=0.5, linewidth=1)

        ax3.set_title(
            "Aligned Waveforms with Edit Operations Highlighted",
            fontsize=14,
            fontweight="bold",
        )
        ax3.set_xlabel("Aligned Time Index")
        ax3.set_ylabel("Amplitude (Normalized)")
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_ylim(-1.2, 1.2)

        # 3. Operation statistics
        ax4 = fig.add_subplot(gs[2, 0]) if show_matrix else fig.add_subplot(gs[1, 0])

        # Count operations
        op_counts = {op: operations.count(op) for op in EditOperation}

        # Create bar chart
        ops_list = [op for op in EditOperation]
        counts = [op_counts[op] for op in ops_list]
        colors = [op_colors[op] for op in ops_list]
        labels = [op_labels[op] for op in ops_list]

        bars = ax4.bar(labels, counts, color=colors, alpha=0.7)
        ax4.set_title("Edit Operation Statistics", fontsize=12, fontweight="bold")
        ax4.set_ylabel("Count")

        # Add count labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{count}",
                ha="center",
                va="bottom",
            )

        # Rotate x labels for better fit
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha="right")

        # 4. Distance matrix (if enabled)
        if show_matrix and len(w1) > 0 and len(w2) > 0:
            ax5 = fig.add_subplot(gs[2, 1])

            # Create distance matrix for first 100 samples
            n_display = min(100, len(w1), len(w2))
            w1_display = w1[:n_display]
            w2_display = w2[:n_display]

            distance_matrix = np.zeros((n_display, n_display))
            for i in range(n_display):
                for j in range(n_display):
                    distance_matrix[i, j] = abs(w1_display[i] - w2_display[j])

            im = ax5.imshow(
                distance_matrix,
                cmap="hot",
                aspect="auto",
                origin="lower",
                interpolation="nearest",
            )
            ax5.set_title(
                "Distance Matrix (First 100 samples)", fontsize=12, fontweight="bold"
            )
            ax5.set_xlabel(f"{filename2} Sample Index")
            ax5.set_ylabel(f"{filename1} Sample Index")
            plt.colorbar(im, ax=ax5, label="Amplitude Difference")

        # Add overall title with distance metrics
        total_samples = len(operations)
        matches = operations.count(EditOperation.MATCH)
        similarity = (matches / total_samples * 100) if total_samples > 0 else 0

        # Calculate edit distance (non-match operations)
        edit_distance = total_samples - matches

        fig.suptitle(
            f"Waveform Comparison: {filename1} vs {filename2}\n"
            f"Similarity: {similarity:.1f}% | Edit Distance: {edit_distance} | Total Samples: {total_samples}",
            fontsize=16,
            fontweight="bold",
        )

        plt.tight_layout()

        if save_plot:
            plt.savefig(output_file, dpi=150, bbox_inches="tight")
            print(f"Plot saved to {output_file}")

        plt.show()

        return fig

    def generate_report(self, w1, w2, operations, filename1, filename2):
        """Generate text report of comparison results"""

        # Count operations
        op_counts = {op: operations.count(op) for op in EditOperation}

        # Calculate statistics
        total_ops = len(operations)
        matches = op_counts[EditOperation.MATCH]
        similarity = (matches / total_ops * 100) if total_ops > 0 else 0

        # Edit distance (non-match operations)
        edit_distance = total_ops - matches

        report = f"""
        WAVEFORM COMPARISON REPORT
        ===========================

        Files Compared:
        - {filename1}: {len(w1)} samples
        - {filename2}: {len(w2)} samples

        Comparison Parameters:
        - Window Size: {self.window_size}
        - Threshold: {self.threshold}
        - Time Warping: {"Enabled" if self.time_warping else "Disabled"}

        RESULTS:
        ========

        Edit Distance Metrics:
        - Total Operations: {total_ops}
        - Matches: {matches} ({similarity:.2f}%)
        - Edit Distance: {edit_distance}

        Operation Breakdown:
        - Matches: {op_counts[EditOperation.MATCH]}
        - Insertions: {op_counts[EditOperation.INSERT]}
        - Deletions: {op_counts[EditOperation.DELETE]}
        - Substitutions: {op_counts[EditOperation.SUBSTITUTE]}
        - Time Shifts: {op_counts.get(EditOperation.TIME_SHIFT, 0)}

        Similarity Assessment:
        """

        if similarity > 90:
            report += "- Waveforms are VERY SIMILAR (nearly identical)\n"
        elif similarity > 70:
            report += "- Waveforms are SIMILAR (minor differences)\n"
        elif similarity > 50:
            report += "- Waveforms are MODERATELY SIMILAR (significant differences)\n"
        elif similarity > 30:
            report += "- Waveforms are DIFFERENT (major differences)\n"
        else:
            report += "- Waveforms are VERY DIFFERENT (unrelated)\n"

        # Additional metrics
        if len(w1) > 0 and len(w2) > 0:
            mean1, mean2 = np.mean(w1), np.mean(w2)
            std1, std2 = np.std(w1), np.std(w2)

            report += f"""
        Statistical Comparison:
        - Mean Amplitude: {filename1}={mean1:.4f}, {filename2}={mean2:.4f}
        - Standard Deviation: {filename1}={std1:.4f}, {filename2}={std2:.4f}
        - Mean Difference: {abs(mean1 - mean2):.4f}
        - Standard Deviation Difference: {abs(std1 - std2):.4f}
            """

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Compare two waveforms using edit distance techniques with graphical output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two signal files
  python waveform_diff.py signal1.txt signal2.txt

  # Compare synthetic signals
  python waveform_diff.py sine square --synthetic

  # Customize comparison parameters
  python waveform_diff.py file1.txt file2.txt --threshold 0.05 --window 100 --no-warping

  # Save output to file
  python waveform_diff.py ecg1.txt ecg2.txt --save plot.png

  # Generate signal with specific sampling rate
  python waveform_diff.py sine triangle --synthetic --rate 2000
        """,
    )

    parser.add_argument(
        "waveform1", help="First waveform file or signal type (if --synthetic)"
    )
    parser.add_argument(
        "waveform2", help="Second waveform file or signal type (if --synthetic)"
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Generate synthetic signals instead of loading files",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1000,
        help="Sampling rate for synthetic signals (Hz)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="Amplitude difference threshold for substitution",
    )
    parser.add_argument(
        "--window", type=int, default=50, help="Window size for comparison"
    )
    parser.add_argument(
        "--no-warping", action="store_true", help="Disable dynamic time warping"
    )
    parser.add_argument("--save", type=str, help="Save plot to file")
    parser.add_argument(
        "--no-matrix", action="store_true", help="Hide distance matrix visualization"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed text report"
    )

    args = parser.parse_args()

    try:
        # Initialize comparator
        comparator = WaveformComparator(
            window_size=args.window,
            threshold=args.threshold,
            time_warping=not args.no_warping,
        )

        # Load or generate waveforms
        print(f"Loading waveform 1: {args.waveform1}")
        w1, t1, sr1 = comparator.load_waveform(
            args.waveform1, args.synthetic, args.rate
        )

        print(f"Loading waveform 2: {args.waveform2}")
        w2, t2, sr2 = comparator.load_waveform(
            args.waveform2, args.synthetic, args.rate
        )

        print(f"Waveform 1: {len(w1)} samples, sampling rate: {sr1:.0f} Hz")
        print(f"Waveform 2: {len(w2)} samples, sampling rate: {sr2:.0f} Hz")

        # Normalize waveforms
        w1_norm = comparator.normalize_waveform(w1)
        w2_norm = comparator.normalize_waveform(w2)

        # Perform comparison
        print("\nPerforming waveform comparison...")
        (
            operations,
            aligned_w1,
            aligned_w2,
            distance,
        ) = comparator.sliding_window_distance(w1_norm, w2_norm)

        print(f"Comparison complete. Edit distance: {distance}")

        # Generate report
        if args.report:
            report = comparator.generate_report(
                w1_norm, w2_norm, operations, args.waveform1, args.waveform2
            )
            print(report)

            # Save report to file
            with open("waveform_comparison_report.txt", "w") as f:
                f.write(report)
            print("Report saved to waveform_comparison_report.txt")

        # Visualize results
        print("\nGenerating visualization...")
        comparator.visualize_comparison(
            aligned_w1,
            aligned_w2,
            t1,
            t2,
            operations,
            filename1=args.waveform1,
            filename2=args.waveform2,
            show_operations=True,
            show_matrix=not args.no_matrix,
            save_plot=bool(args.save),
            output_file=args.save if args.save else "waveform_comparison.png",
        )

        print("\nOperation Legend:")
        print("  Green: Match")
        print("  Blue: Insertion (extra samples in waveform 2)")
        print("  Red: Deletion (missing samples in waveform 2)")
        print("  Orange: Substitution (different amplitude)")
        print("  Purple: Time Shift (alignment difference)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
