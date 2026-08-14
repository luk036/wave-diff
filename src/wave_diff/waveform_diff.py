import argparse
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np

# Suppress specific warnings
warnings.filterwarnings("ignore", message="A NumPy version")

try:
    from scipy import signal

    SCIPY_AVAILABLE = True
except (ImportError, UserWarning) as e:
    SCIPY_AVAILABLE = False
    print(f"Note: SciPy not available, some features limited: {e}")

    # Define simple signal functions if scipy not available
    def square_wave(t, freq):
        return np.sign(np.sin(2 * np.pi * freq * t))

    def sawtooth_wave(t, freq, width=0.5):
        return 2 * (t * freq - np.floor(t * freq + width)) - 1

    def chirp_signal(t, f0, f1, t1):
        return np.sin(2 * np.pi * (f0 + (f1 - f0) * t / (2 * t1)) * t)


class EditOperation:
    """Class for edit operations in waveform comparison"""

    # Use class instead of Enum for simpler handling
    MATCH = 0
    INSERT = 1  # Additional samples in waveform2
    DELETE = 2  # Missing samples in waveform2
    SUBSTITUTE = 3  # Different amplitude

    @staticmethod
    def get_label(op):
        labels = {0: "Match", 1: "Insertion", 2: "Deletion", 3: "Substitution"}
        return labels.get(op, "Unknown")

    @staticmethod
    def get_color(op):
        colors = {0: "green", 1: "blue", 2: "red", 3: "orange"}
        return colors.get(op, "gray")


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
                if SCIPY_AVAILABLE:
                    waveform = signal.square(2 * np.pi * 3 * t)  # 3 Hz square wave
                else:
                    waveform = square_wave(t, 3)
            elif filepath == "triangle":
                if SCIPY_AVAILABLE:
                    waveform = signal.sawtooth(
                        2 * np.pi * 4 * t, width=0.5
                    )  # 4 Hz triangle
                else:
                    waveform = sawtooth_wave(t, 4, width=0.5)
            elif filepath == "chirp":
                if SCIPY_AVAILABLE:
                    waveform = signal.chirp(
                        t, f0=1, f1=20, t1=duration, method="linear"
                    )
                else:
                    waveform = chirp_signal(t, f0=1, f1=20, t1=duration)
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
                try:
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
                except Exception:
                    # If all fails, create a simple waveform
                    print(
                        f"Warning: Could not load {filepath}, using default sine wave"
                    )
                    duration = 2.0
                    t = np.linspace(0, duration, int(sampling_rate * duration))
                    waveform = np.sin(2 * np.pi * 5 * t)
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

    def simple_dtw(self, w1, w2, max_len=1000):
        """
        Simplified Dynamic Time Warping for waveform alignment
        Limited to max_len samples to avoid memory issues
        """
        # Limit length for performance
        n = min(len(w1), max_len)
        m = min(len(w2), max_len)

        w1_sub = w1[:n]
        w2_sub = w2[:m]

        # Create cost matrix
        cost_matrix = np.zeros((n, m))

        # Initialize first row and column
        for i in range(n):
            cost_matrix[i, 0] = np.abs(w1_sub[i] - w2_sub[0]) + i
        for j in range(m):
            cost_matrix[0, j] = np.abs(w1_sub[0] - w2_sub[j]) + j

        # Fill the matrix
        for i in range(1, n):
            for j in range(1, m):
                cost = np.abs(w1_sub[i] - w2_sub[j])
                cost_matrix[i, j] = cost + min(
                    cost_matrix[i - 1, j],  # deletion
                    cost_matrix[i, j - 1],  # insertion
                    cost_matrix[i - 1, j - 1],  # match/substitute
                )

        # Simple path - just diagonal for now (simplified)
        warp_path = []
        min_len = min(n, m)
        for k in range(min_len):
            warp_path.append((k, k))

        distance = cost_matrix[n - 1, m - 1] / min_len  # Normalized distance

        return warp_path, distance

    def sliding_window_distance(self, w1, w2):
        """
        Calculate edit distance using sliding window approach

        Returns:
        operations: List of edit operations
        aligned_w1, aligned_w2: Aligned waveforms (same length)
        edit_distance: Integer count of non-match operations
        """
        n, m = len(w1), len(w2)

        if n == 0 or m == 0:
            # Handle empty waveforms
            max_len = max(n, m)
            operations = [
                EditOperation.INSERT if n == 0 else EditOperation.DELETE
            ] * max_len
            aligned_w1 = (
                np.zeros(max_len)
                if n == 0
                else np.concatenate([w1, np.zeros(max_len - n)])
            )
            aligned_w2 = (
                np.zeros(max_len)
                if m == 0
                else np.concatenate([w2, np.zeros(max_len - m)])
            )
            return operations, aligned_w1, aligned_w2, max_len

        # Ensure we work with numpy arrays
        w1 = np.array(w1)
        w2 = np.array(w2)

        if self.time_warping and n > 0 and m > 0:
            # Use simplified DTW for alignment
            try:
                warp_path, distance = self.simple_dtw(w1, w2)

                # Create aligned waveforms based on warp path
                aligned_w1 = []
                aligned_w2 = []
                operations = []

                for i, j in warp_path:
                    if i < n and j < m:
                        val1 = w1[i]
                        val2 = w2[j]
                        aligned_w1.append(val1)
                        aligned_w2.append(val2)

                        diff = abs(val1 - val2)
                        if diff < self.threshold:
                            operations.append(EditOperation.MATCH)
                        else:
                            operations.append(EditOperation.SUBSTITUTE)
                    elif i < n:
                        # Shouldn't happen with our simple diagonal path
                        aligned_w1.append(w1[i])
                        aligned_w2.append(0)
                        operations.append(EditOperation.DELETE)
                    else:
                        aligned_w1.append(0)
                        aligned_w2.append(w2[j])
                        operations.append(EditOperation.INSERT)

                aligned_w1 = np.array(aligned_w1)
                aligned_w2 = np.array(aligned_w2)
                edit_distance = sum(1 for op in operations if op != EditOperation.MATCH)

                return operations, aligned_w1, aligned_w2, edit_distance

            except Exception as e:
                print(f"Warning: DTW failed, using simple alignment: {e}")
                # Fall back to simple alignment

        # Simple alignment (pad to same length)
        max_len = max(n, m)

        aligned_w1 = np.zeros(max_len)
        aligned_w2 = np.zeros(max_len)
        aligned_w1[:n] = w1[:max_len] if n > max_len else w1
        aligned_w2[:m] = w2[:max_len] if m > max_len else w2

        operations = []

        for k in range(max_len):
            if k < n and k < m:
                val1 = aligned_w1[k]
                val2 = aligned_w2[k]
                diff = abs(val1 - val2)
                if diff < self.threshold:
                    operations.append(EditOperation.MATCH)
                else:
                    operations.append(EditOperation.SUBSTITUTE)
            elif k < n:
                operations.append(EditOperation.DELETE)
            else:
                operations.append(EditOperation.INSERT)

        edit_distance = sum(1 for op in operations if op != EditOperation.MATCH)

        return operations, aligned_w1, aligned_w2, edit_distance

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
        # Ensure we have proper time arrays for display
        if len(t1) != len(w1):
            t1 = np.arange(len(w1))
        if len(t2) != len(w2):
            t2 = np.arange(len(w2))

        # For aligned display, use indices
        t_aligned = np.arange(len(operations))

        # Create figure with appropriate size
        if show_matrix:
            fig, axes = plt.subplots(3, 2, figsize=(16, 12))
            ax1, ax2 = axes[0, 0], axes[0, 1]
            ax3 = axes[1, :]  # Span both columns
            ax4, ax5 = axes[2, 0], axes[2, 1]
        else:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            ax1, ax2 = axes[0, 0], axes[0, 1]
            ax3 = axes[1, 0]  # Aligned waveforms
            ax4 = axes[1, 1]  # Statistics

        # 1. Original waveforms
        # Plot only up to the length of the data
        plot_len1 = min(len(t1), len(w1))
        ax1.plot(
            t1[:plot_len1],
            w1[:plot_len1],
            "b-",
            linewidth=1.5,
            alpha=0.7,
            label=filename1,
        )
        ax1.set_title(f"Original {filename1}", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Time (s)" if len(t1) == plot_len1 else "Sample Index")
        ax1.set_ylabel("Amplitude")
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        plot_len2 = min(len(t2), len(w2))
        ax2.plot(
            t2[:plot_len2],
            w2[:plot_len2],
            "r-",
            linewidth=1.5,
            alpha=0.7,
            label=filename2,
        )
        ax2.set_title(f"Original {filename2}", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Time (s)" if len(t2) == plot_len2 else "Sample Index")
        ax2.set_ylabel("Amplitude")
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # 2. Aligned waveforms with edit operations
        # Use a single axis for aligned waveforms
        if show_matrix:
            ax3 = axes[1, 0]  # Use first subplot in second row
            ax3.set_position([0.1, 0.35, 0.8, 0.25])  # Make it span both columns
        else:
            ax3 = axes[1, 0]  # Aligned waveforms

        # Plot aligned waveforms (only up to min length)
        plot_len = min(len(t_aligned), len(w1), len(w2), 1000)  # Limit for display
        ax3.plot(
            t_aligned[:plot_len],
            w1[:plot_len],
            "b-",
            linewidth=1,
            alpha=0.6,
            label=f"Aligned {filename1}",
        )
        ax3.plot(
            t_aligned[:plot_len],
            w2[:plot_len],
            "r-",
            linewidth=1,
            alpha=0.6,
            label=f"Aligned {filename2}",
        )

        # Highlight differences
        if show_operations:
            # Only highlight first 500 differences for clarity
            highlight_limit = min(500, len(operations), plot_len)
            for i in range(highlight_limit):
                op = operations[i]
                if op != EditOperation.MATCH:
                    color = EditOperation.get_color(op)
                    # Add vertical shaded region
                    ax3.axvspan(i - 0.5, i + 0.5, alpha=0.1, color=color, zorder=0)

                    # Mark the points
                    if i < len(w1) and i < len(w2):
                        ax3.plot(i, w1[i], "b.", markersize=6, alpha=0.8)
                        ax3.plot(i, w2[i], "r.", markersize=6, alpha=0.8)

                        # Connect with line for substitutions
                        if op == EditOperation.SUBSTITUTE:
                            ax3.plot(
                                [i, i], [w1[i], w2[i]], "k--", alpha=0.3, linewidth=0.5
                            )

        ax3.set_title(
            "Aligned Waveforms with Edit Operations Highlighted",
            fontsize=12,
            fontweight="bold",
        )
        ax3.set_xlabel("Aligned Sample Index")
        ax3.set_ylabel("Amplitude")
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc="upper right")

        # 3. Operation statistics
        if show_matrix:
            ax4 = axes[2, 0]
        else:
            ax4 = axes[1, 1]

        # Count operations
        op_counts = {}
        for op in [
            EditOperation.MATCH,
            EditOperation.INSERT,
            EditOperation.DELETE,
            EditOperation.SUBSTITUTE,
        ]:
            op_counts[op] = operations.count(op)

        # Create bar chart
        ops_list = [
            EditOperation.MATCH,
            EditOperation.INSERT,
            EditOperation.DELETE,
            EditOperation.SUBSTITUTE,
        ]
        counts = [op_counts[op] for op in ops_list]
        colors = [EditOperation.get_color(op) for op in ops_list]
        labels = [EditOperation.get_label(op) for op in ops_list]

        bars = ax4.bar(labels, counts, color=colors, alpha=0.7)
        ax4.set_title("Edit Operation Statistics", fontsize=12, fontweight="bold")
        ax4.set_ylabel("Count")

        # Add count labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            if height > 0:  # Only add label if count > 0
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
        if show_matrix:
            ax5 = axes[2, 1]

            # Create distance matrix for first 50 samples (for performance)
            n_display = min(50, len(w1), len(w2))
            if n_display > 0:
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
                    f"Distance Matrix (First {n_display} samples)",
                    fontsize=12,
                    fontweight="bold",
                )
                ax5.set_xlabel(f"{filename2} Sample Index")
                ax5.set_ylabel(f"{filename1} Sample Index")
                plt.colorbar(im, ax=ax5, label="Amplitude Difference")
            else:
                ax5.text(
                    0.5,
                    0.5,
                    "Insufficient data\nfor distance matrix",
                    ha="center",
                    va="center",
                    transform=ax5.transAxes,
                )
                ax5.set_title("Distance Matrix", fontsize=12, fontweight="bold")

        # Calculate statistics for title
        total_samples = len(operations)
        matches = operations.count(EditOperation.MATCH)
        similarity = (matches / total_samples * 100) if total_samples > 0 else 0
        edit_distance = total_samples - matches

        fig.suptitle(
            f"Waveform Comparison: {filename1} vs {filename2}\n"
            f"Similarity: {similarity:.1f}% | Edit Distance: {edit_distance} | Total Samples: {total_samples}",
            fontsize=14,
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
        op_counts = {}
        for op in [
            EditOperation.MATCH,
            EditOperation.INSERT,
            EditOperation.DELETE,
            EditOperation.SUBSTITUTE,
        ]:
            op_counts[op] = operations.count(op)

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
    parser.add_argument(
        "--simple", action="store_true", help="Use simple visualization only"
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
            edit_distance,
        ) = comparator.sliding_window_distance(w1_norm, w2_norm)

        print("Comparison complete.")
        print(f"  Total operations: {len(operations)}")
        print(f"  Matches: {operations.count(EditOperation.MATCH)}")
        print(f"  Edit distance (non-matches): {edit_distance}")

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

        # Use original waveforms for first two plots, aligned for comparison
        comparator.visualize_comparison(
            w1_norm,
            w2_norm,
            t1,
            t2,
            operations,
            filename1=args.waveform1,
            filename2=args.waveform2,
            show_operations=True,
            show_matrix=(not args.no_matrix and not args.simple),
            save_plot=bool(args.save),
            output_file=args.save if args.save else "waveform_comparison.png",
        )

        print("\nOperation Legend:")
        print("  Green: Match (similar amplitude)")
        print("  Blue: Insertion (extra samples in waveform 2)")
        print("  Red: Deletion (missing samples in waveform 2)")
        print("  Orange: Substitution (different amplitude)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


def simple_example():
    """Simple standalone example for testing"""
    print("Running simple waveform comparison example...")

    # Create synthetic waveforms
    t = np.linspace(0, 2, 2000)  # 2 seconds, 2000 samples

    # Waveform 1: Sine wave
    w1 = np.sin(2 * np.pi * 5 * t)

    # Waveform 2: Modified square wave
    w2 = np.sign(np.sin(2 * np.pi * 5 * t))  # Square wave

    # Add some differences
    w2[500:600] = w2[500:600] * 0.5  # Reduced amplitude region
    w2[1000:1100] = 0  # Flat region (simulated deletion)

    # Create comparator
    comparator = WaveformComparator(threshold=0.2, time_warping=False)

    # Normalize
    w1_norm = comparator.normalize_waveform(w1)
    w2_norm = comparator.normalize_waveform(w2)

    # Compare
    (
        operations,
        aligned_w1,
        aligned_w2,
        edit_distance,
    ) = comparator.sliding_window_distance(w1_norm, w2_norm)

    # Visualize
    comparator.visualize_comparison(
        w1_norm,
        w2_norm,
        t,
        t,
        operations,
        filename1="Sine Wave",
        filename2="Modified Square Wave",
        show_matrix=False,
    )

    print("\nSimple Example Results:")
    print(f"  Edit distance: {edit_distance}")
    print(
        f"  Similarity: {(operations.count(EditOperation.MATCH) / len(operations) * 100):.1f}%"
    )


if __name__ == "__main__":
    # Test with simple example
    if len(sys.argv) == 1:
        simple_example()
    else:
        main()
