"""Tests for diff_tool module."""

from experiments.diff_tool import (
    context_diff,
    html_diff,
    simple_diff,
    unified_diff,
)


def test_simple_diff_identical() -> None:
    content = "line1\nline2\nline3\n"
    result = simple_diff(content, content)
    assert "line1" in result
    assert "line2" in result


def test_simple_diff_different() -> None:
    content1 = "line1\nline2\nline3\n"
    content2 = "line1\nmodified\nline3\n"
    result = simple_diff(content1, content2)
    assert "- line2" in result
    assert "+ modified" in result


def test_simple_diff_empty_first() -> None:
    result = simple_diff("", "line1\nline2\n")
    assert "+ line1" in result


def test_simple_diff_empty_second() -> None:
    result = simple_diff("line1\nline2\n", "")
    assert "- line1" in result


def test_simple_diff_both_empty() -> None:
    result = simple_diff("", "")
    assert result == ""


def test_unified_diff_identical() -> None:
    content = "line1\nline2\nline3\n"
    result = unified_diff(content, content)
    assert result == ""


def test_unified_diff_different() -> None:
    content1 = "line1\nline2\nline3\n"
    content2 = "line1\nmodified\nline3\n"
    result = unified_diff(content1, content2)
    assert "@@" in result
    assert "-line2" in result or "- line2" in result
    assert "+modified" in result or "+ modified" in result


def test_unified_diff_with_context_lines() -> None:
    content1 = "a\nb\nc\nd\ne\n"
    content2 = "a\nb\nx\nd\ne\n"
    result = unified_diff(content1, content2, n=1)
    assert "@@" in result


def test_context_diff_identical() -> None:
    content = "line1\nline2\n"
    result = context_diff(content, content)
    assert result == ""


def test_context_diff_different() -> None:
    content1 = "line1\nline2\nline3\n"
    content2 = "line1\nmodified\nline3\n"
    result = context_diff(content1, content2)
    assert "****" in result or "***" in result


def test_html_diff_identical() -> None:
    content = "line1\nline2\n"
    result = html_diff(content, content)
    assert "<html" in result or "<table" in result
    assert "diff" in result.lower() or "diff" in result


def test_html_diff_different() -> None:
    content1 = "hello\nworld\n"
    content2 = "hello\nthere\n"
    result = html_diff(content1, content2)
    assert "<html" in result or "<table" in result
