"""Tests for the diff_tool CLI entry point (main)."""

import sys
from pathlib import Path

import pytest

from wave_diff.diff_tool import main


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_main_unified_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    _write_file(file1, "line1\nline2\nline3\n")
    _write_file(file2, "line1\nmodified\nline3\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(file1), str(file2)])

    main()

    captured = capsys.readouterr()
    assert "Summary:" in captured.out
    assert "@@" in captured.out


def test_main_simple(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    _write_file(file1, "line1\nline2\nline3\n")
    _write_file(file2, "line1\nmodified\nline3\n")
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "-f", "simple", str(file1), str(file2)]
    )

    main()

    captured = capsys.readouterr()
    assert "- line2" in captured.out
    assert "+ modified" in captured.out


def test_main_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    _write_file(file1, "line1\nline2\nline3\n")
    _write_file(file2, "line1\nmodified\nline3\n")
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "-f", "context", str(file1), str(file2)]
    )

    main()

    captured = capsys.readouterr()
    assert "***" in captured.out


def test_main_html_default_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    _write_file(file1, "hello\nworld\n")
    _write_file(file2, "hello\nthere\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "-f", "html", str(file1), str(file2)]
    )

    main()

    out_file = tmp_path / "diff_output.html"
    assert out_file.exists()
    assert "<html" in out_file.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "Diff saved to" in captured.out


def test_main_html_with_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    out_file = tmp_path / "report.html"
    _write_file(file1, "hello\nworld\n")
    _write_file(file2, "hello\nthere\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["wave-diff", "-f", "html", "-o", str(out_file), str(file1), str(file2)],
    )

    main()

    assert out_file.exists()
    assert "<html" in out_file.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "Diff saved to" in captured.out


def test_main_unified_context_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    _write_file(file1, "a\nb\nc\nd\ne\n")
    _write_file(file2, "a\nb\nx\nd\ne\n")
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "-f", "unified", "-n", "1", str(file1), str(file2)]
    )

    main()

    captured = capsys.readouterr()
    assert "@@" in captured.out


def test_main_simple_with_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    out_file = tmp_path / "diff.txt"
    _write_file(file1, "line1\nline2\nline3\n")
    _write_file(file2, "line1\nmodified\nline3\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["wave-diff", "-f", "simple", "-o", str(out_file), str(file1), str(file2)],
    )

    main()

    assert out_file.exists()
    assert "- line2" in out_file.read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert "Diff saved to" in captured.out


def test_main_file_not_found(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["wave-diff", "no_such_file.txt", "other_file.txt"]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: File not found" in captured.out


def test_main_os_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    dir_path = tmp_path / "somedir"
    dir_path.mkdir()
    file2 = tmp_path / "file2.txt"
    _write_file(file2, "content\n")
    monkeypatch.setattr(sys, "argv", ["wave-diff", str(dir_path), str(file2)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.out
