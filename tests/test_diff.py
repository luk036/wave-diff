"""Tests for diff_distance module."""

from diff_distance import (
    compute_file_similarity,
    diff_lines,
    levenshtein_distance,
    levenshtein_distance_with_path,
)


def test_levenshtein_identical() -> None:
    distance, _ = levenshtein_distance("hello", "hello")
    assert distance == 0


def test_levenshtein_single_substitution() -> None:
    distance, _ = levenshtein_distance("hello", "hallo")
    assert distance == 1


def test_levenshtein_single_insertion() -> None:
    distance, _ = levenshtein_distance("hello", "hello world")
    assert distance == 6


def test_levenshtein_single_deletion() -> None:
    distance, _ = levenshtein_distance("hello", "helo")
    assert distance == 1


def test_levenshtein_empty_string() -> None:
    distance, _ = levenshtein_distance("", "abc")
    assert distance == 3


def test_levenshtein_both_empty() -> None:
    distance, _ = levenshtein_distance("", "")
    assert distance == 0


def test_levenshtein_with_path() -> None:
    distance, dp, ops, path = levenshtein_distance_with_path("abc", "abc")
    assert distance == 0
    assert len(path) > 0


def test_diff_lines_identical() -> None:
    lines1 = ["line1", "line2", "line3"]
    lines2 = ["line1", "line2", "line3"]
    distance, output = diff_lines(lines1, lines2)
    assert distance == 0


def test_diff_lines_different() -> None:
    lines1 = ["line1", "line2", "line3"]
    lines2 = ["line1", "modified", "line3"]
    distance, output = diff_lines(lines1, lines2)
    assert distance >= 1


def test_compute_file_similarity_identical() -> None:
    content = "Hello World"
    result = compute_file_similarity(content, content)
    assert result["char_distance"] == 0
    assert result["char_similarity"] == 100.0


def test_compute_file_similarity_different() -> None:
    content1 = "Hello World"
    content2 = "Hello There"
    result = compute_file_similarity(content1, content2)
    assert result["char_distance"] > 0
    assert result["char_similarity"] < 100.0
    assert result["char_similarity"] > 0
