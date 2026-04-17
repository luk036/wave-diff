# wave-diff

Waveform and text difference analysis using Levenshtein distance and Dynamic Time Warping (DTW).

## Installation

```bash
pip install -e .[testing]
```

## Usage

Compare two text files:

```bash
wave-diff file1.txt file2.txt
```

### Options

- `-d, --detailed` - Show detailed edit operations
- `-m, --matrix` - Show DP matrix
- `-s, --summary` - Show only summary statistics

### Examples

**Basic comparison:**
```bash
wave-diff original.txt modified.txt
```

**Show detailed operations:**
```bash
wave-diff -d file1.txt file2.txt
```

**Show DP matrix:**
```bash
wave-diff -m file1.txt file2.txt
```

**Summary only:**
```bash
wave-diff -s file1.txt file2.txt
```

## Python API

```python
from experiments.diff_distance import (
    levenshtein_distance,
    compute_file_similarity,
    diff_lines,
)

# Character-level distance
distance, dp_matrix = levenshtein_distance("kitten", "sitting")
print(f"Distance: {distance}")  # 3

# Compare files
results = compute_file_similarity(content1, content2)
print(f"Similarity: {results['char_similarity']:.2f}%")

# Line-level diff
distance, diff_output = diff_lines(lines1, lines2)
```

## Testing

```bash
pytest
```

With coverage report:
```bash
pytest --cov=experiments --cov-report=term-missing
```

## Project Structure

```
wave-diff/
├── experiments/
│   ├── __init__.py          # Package init
│   ├── diff_distance.py     # Levenshtein distance implementation
│   ├── diff_tool.py         # Standard library diff wrappers
│   └── waveform_diff.py     # Waveform comparison using DTW
├── tests/
│   ├── conftest.py
│   └── test_diff.py
├── setup.cfg                # Project configuration
├── setup.py                 # Setup script
└── README.md
```

## Requirements

- Python 3.9+
- typing_extensions