"""Additional tests for the diff_distance module covering edge cases."""

from experiments.diff_distance import (
    EditOperation,
    compute_file_similarity,
    diff_lines,
    levenshtein_distance,
    levenshtein_distance_with_path,
    show_edit_operations,
)


def test_levenshtein_case_sensitive() -> None:
    distance, _ = levenshtein_distance("Hello", "hello")
    assert distance == 1


def test_levenshtein_completely_different() -> None:
    distance, _ = levenshtein_distance("abc", "xyz")
    assert distance == 3


def test_levenshtein_one_char() -> None:
    distance, _ = levenshtein_distance("a", "")
    assert distance == 1
    distance, _ = levenshtein_distance("", "a")
    assert distance == 1


def test_levenshtein_with_path_all_ops() -> None:
    """Test levenshtein with path for various edit operations."""
    distance, dp, ops, path = levenshtein_distance_with_path("kitten", "sitting")
    assert distance == 3


def test_levenshtein_with_path_identical() -> None:
    distance, dp, ops, path = levenshtein_distance_with_path("same", "same")
    assert distance == 0
    assert all(op == EditOperation.MATCH for op in [p[0] for p in path])


def test_levenshtein_with_path_empty_first() -> None:
    distance, dp, ops, path = levenshtein_distance_with_path("", "abc")
    assert distance == 3


def test_levenshtein_with_path_empty_second() -> None:
    distance, dp, ops, path = levenshtein_distance_with_path("abc", "")
    assert distance == 3


def test_levenshtein_with_path_both_empty() -> None:
    distance, dp, ops, path = levenshtein_distance_with_path("", "")
    assert distance == 0
    assert path == []


def test_diff_lines_empty() -> None:
    distance, output = diff_lines([], [])
    assert distance == 0
    assert output == ""


def test_diff_lines_empty_vs_content() -> None:
    distance, output = diff_lines([], ["a", "b"])
    assert distance == 2


def test_diff_lines_content_vs_empty() -> None:
    distance, output = diff_lines(["a", "b"], [])
    assert distance == 2


def test_diff_lines_all_different() -> None:
    lines1 = ["a", "b", "c"]
    lines2 = ["x", "y", "z"]
    distance, output = diff_lines(lines1, lines2)
    assert distance >= 3


def test_compute_file_similarity_empty_files() -> None:
    result = compute_file_similarity("", "")
    assert result["char_distance"] == 0
    assert result["char_similarity"] == 100.0


def test_compute_file_similarity_one_empty() -> None:
    result = compute_file_similarity("", "hello")
    assert result["char_distance"] == 5
    assert result["char_similarity"] == 0.0


def test_compute_file_similarity_word_level() -> None:
    result = compute_file_similarity("hello world", "hello there")
    assert "word_distance" in result
    assert "word_similarity" in result


def test_compute_file_similarity_line_counts() -> None:
    content1 = "a\nb\nc\n"
    content2 = "a\nb\nc\nd\n"
    result = compute_file_similarity(content1, content2)
    assert result["lines1_count"] == 3
    assert result["lines2_count"] == 4
    assert result["line_distance"] == 1


def test_edit_operation_enum_values() -> None:
    assert EditOperation.MATCH.value == 0
    assert EditOperation.INSERT.value == 1
    assert EditOperation.DELETE.value == 2
    assert EditOperation.REPLACE.value == 3


def test_show_edit_operations_basic() -> None:
    """Test that show_edit_operations returns the correct tuple."""
    distance, dp, ops, path = show_edit_operations("abc", "abc")
    assert distance == 0


def test_show_edit_operations_different() -> None:
    distance, dp, ops, path = show_edit_operations("abc", "adc")
    assert distance == 1
