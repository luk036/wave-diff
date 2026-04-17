"""Tests for diff_distance module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))

from diff_distance import (
    levenshtein_distance,
    levenshtein_distance_with_path,
    diff_lines,
    compute_file_similarity,
)


def test_levenshtein_identical():
    distance, _ = levenshtein_distance("hello", "hello")
    assert distance == 0


def test_levenshtein_single_substitution():
    distance, _ = levenshtein_distance("hello", "hallo")
    assert distance == 1


def test_levenshtein_single_insertion():
    distance, _ = levenshtein_distance("hello", "hello world")
    assert distance == 6


def test_levenshtein_single_deletion():
    distance, _ = levenshtein_distance("hello", "helo")
    assert distance == 1


def test_levenshtein_empty_string():
    distance, _ = levenshtein_distance("", "abc")
    assert distance == 3


def test_levenshtein_both_empty():
    distance, _ = levenshtein_distance("", "")
    assert distance == 0


def test_levenshtein_with_path():
    distance, dp, ops, path = levenshtein_distance_with_path("abc", "abc")
    assert distance == 0
    assert len(path) > 0


def test_diff_lines_identical():
    lines1 = ["line1", "line2", "line3"]
    lines2 = ["line1", "line2", "line3"]
    distance, output = diff_lines(lines1, lines2)
    assert distance == 0


def test_diff_lines_different():
    lines1 = ["line1", "line2", "line3"]
    lines2 = ["line1", "modified", "line3"]
    distance, output = diff_lines(lines1, lines2)
    assert distance >= 1


def test_compute_file_similarity_identical():
    content = "Hello World"
    result = compute_file_similarity(content, content)
    assert result["char_distance"] == 0
    assert result["char_similarity"] == 100.0


def test_compute_file_similarity_different():
    content1 = "Hello World"
    content2 = "Hello There"
    result = compute_file_similarity(content1, content2)
    assert result["char_distance"] > 0
    assert result["char_similarity"] < 100.0
    assert result["char_similarity"] > 0


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
