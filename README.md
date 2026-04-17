# wave-diff

Waveform and text difference analysis using Levenshtein distance and Dynamic Time Warping (DTW).

## Installation

```bash
pip install -e .
```

## Usage

Compare two text files:

```bash
wave-diff file1.txt file2.txt
```

Options:
- `-d, --detailed` - Show detailed edit operations
- `-m, --matrix` - Show DP matrix
- `-s, --summary` - Show only summary statistics

## Testing

```bash
pytest
```

## Project Structure

- `experiments/diff_distance.py` - Levenshtein distance implementation
- `experiments/diff_tool.py` - Standard library diff wrappers
- `experiments/waveform_diff.py` - Waveform comparison using DTW
