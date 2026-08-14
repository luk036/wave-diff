"""CLI and edge-case tests for the diff_distance module."""

import sys

import pytest

from wave_diff.diff_distance import (
    EditOperation,
    diff_lines,
    main,
    show_edit_operations,
)


def test_show_edit_operations_match(capsys) -> None:
    """MATCH operation path in show_edit_operations."""
    distance, dp, ops, path = show_edit_operations("abc", "abc")
    assert distance == 0
    assert len(dp) == 4
    assert len(ops) == 4
    assert all(op == EditOperation.MATCH for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Levenshtein Distance: 0" in out
    assert "Step" in out
    assert "Match" in out


def test_show_edit_operations_insert(capsys) -> None:
    """INSERT operation path in show_edit_operations."""
    distance, dp, ops, path = show_edit_operations("abc", "abcd")
    assert distance == 1
    assert any(op == EditOperation.INSERT for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Insert" in out
    assert "Step" in out


def test_show_edit_operations_delete(capsys) -> None:
    """DELETE operation path in show_edit_operations."""
    distance, dp, ops, path = show_edit_operations("abcd", "abc")
    assert distance == 1
    assert any(op == EditOperation.DELETE for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Delete" in out
    assert "Step" in out


def test_show_edit_operations_replace(capsys) -> None:
    """REPLACE operation path in show_edit_operations."""
    distance, dp, ops, path = show_edit_operations("abc", "axc")
    assert distance == 1
    assert any(op == EditOperation.REPLACE for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Replace" in out
    assert "Step" in out


def test_show_edit_operations_empty_first(capsys) -> None:
    """All-insert path when the first string is empty."""
    distance, dp, ops, path = show_edit_operations("", "ab")
    assert distance == 2
    assert all(op == EditOperation.INSERT for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Insert" in out


def test_show_edit_operations_empty_second(capsys) -> None:
    """All-delete path when the second string is empty."""
    distance, dp, ops, path = show_edit_operations("ab", "")
    assert distance == 2
    assert all(op == EditOperation.DELETE for op, _, _ in path)
    out, err = capsys.readouterr()
    assert "Delete" in out


def test_diff_lines_delete_plus_replace() -> None:
    """Both lists differ so backtracking takes the delete+replace path."""
    distance, output = diff_lines(["a", "b"], ["x", "y"])
    assert distance == 2
    assert "- b" in output
    assert "+ y" in output
    assert "- a" in output
    assert "+ x" in output


def test_diff_lines_deletions_after_match() -> None:
    """j == 0 branch after the common prefix has been matched."""
    distance, output = diff_lines(["a", "b", "c"], ["a"])
    assert distance == 2
    assert output == "  a\n- b\n- c"


def test_main_default(tmp_path, capsys, monkeypatch) -> None:
    """Default run prints the diff output and the summary."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("line one\nline two\n")
    file2.write_text("line one\nline changed\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "Comparing" in out
    assert "EDIT DISTANCE SUMMARY" in out
    assert "- line two" in out or "+ line changed" in out


def test_main_detailed(tmp_path, capsys, monkeypatch) -> None:
    """-d flag shows detailed edit operations for the first differing line."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("abc\nxyz\n")
    file2.write_text("abc\nxzz\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", "-d", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "DETAILED EDIT OPERATIONS FOR LINE 2" in out
    assert "Step" in out


def test_main_detailed_different_line_counts(tmp_path, capsys, monkeypatch) -> None:
    """-d flag with identical shared lines but different line counts."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("a\nb\n")
    file2.write_text("a\nb\nc\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", "-d", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES HAVE DIFFERENT NUMBER OF LINES" in out


def test_main_detailed_identical_files(tmp_path, capsys, monkeypatch) -> None:
    """-d flag with identical files has no differing line to show."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("a\nb\n")
    file2.write_text("a\nb\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", "-d", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "DETAILED EDIT OPERATIONS" not in out
    assert "FILES ARE IDENTICAL" in out


def test_main_matrix(tmp_path, capsys, monkeypatch) -> None:
    """-m flag prints the DP matrix sample."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("abcdefghijklmnop\n")
    file2.write_text("abcdefghijXYZop\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", "-m", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "DP MATRIX (first 10x10 characters):" in out
    assert "ε" in out


def test_main_summary(tmp_path, capsys, monkeypatch) -> None:
    """-s flag prints the summary only."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("hello world\n")
    file2.write_text("hello there\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", "-s", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "EDIT DISTANCE SUMMARY" in out
    assert "Comparing" not in out


def test_main_identical_files(tmp_path, capsys, monkeypatch) -> None:
    """Identical files print the identical verdict."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("same content\n")
    file2.write_text("same content\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES ARE IDENTICAL" in out


def test_main_very_similar(tmp_path, capsys, monkeypatch) -> None:
    """Files with high char similarity print the very similar verdict."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("hello world hello\n")
    file2.write_text("hello world hallo\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES ARE VERY SIMILAR" in out


def test_main_moderately_similar(tmp_path, capsys, monkeypatch) -> None:
    """Files with moderate char similarity print the moderate verdict."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("abcde\n")
    file2.write_text("abXde\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES ARE MODERATELY SIMILAR" in out


def test_main_somewhat_different(tmp_path, capsys, monkeypatch) -> None:
    """Files with lower char similarity print the somewhat different verdict."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("abcde\n")
    file2.write_text("abXYZ\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES ARE SOMEWHAT DIFFERENT" in out


def test_main_very_different(tmp_path, capsys, monkeypatch) -> None:
    """Files with very low char similarity print the very different verdict."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("abc\n")
    file2.write_text("xyz\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])
    main()
    out, err = capsys.readouterr()
    assert "FILES ARE VERY DIFFERENT" in out


def test_main_file_not_found(capsys, monkeypatch) -> None:
    """Missing files exit with code 1 and print an error to stderr."""
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "does_not_exist_1.txt", "does_not_exist_2.txt"]
    )
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert "Error: File not found" in err


def test_main_generic_exception(tmp_path, capsys, monkeypatch) -> None:
    """Unreadable input (a directory) exits with code 1 and prints an error."""
    dir_path = tmp_path / "somedir"
    dir_path.mkdir()
    file2 = tmp_path / "file2.txt"
    file2.write_text("content\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(dir_path), str(file2)])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert "Error:" in err
