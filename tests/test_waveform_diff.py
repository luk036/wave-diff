"""Tests for wave_diff.waveform_diff module."""

import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

import wave_diff.waveform_diff as waveform_diff
from wave_diff.waveform_diff import (
    EditOperation,
    WaveformComparator,
    main,
    simple_example,
)

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def _headless_matplotlib(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure plt.show() never blocks on a GUI window and clean up figures."""
    monkeypatch.setattr(plt, "show", lambda: None)
    yield
    plt.close("all")


def _build_ops(
    total: int, matches: int, substitutes: int = 0, inserts: int = 0, deletes: int = 0
) -> list:
    ops = [EditOperation.MATCH] * matches
    ops += [EditOperation.SUBSTITUTE] * substitutes
    ops += [EditOperation.INSERT] * inserts
    ops += [EditOperation.DELETE] * deletes
    assert len(ops) == total
    return ops


class TestLoadWaveform:
    def test_synthetic_signals(self) -> None:
        comparator = WaveformComparator()
        for name in ("sine", "square", "triangle", "chirp", "ecg", "unknown"):
            w, t, sr = comparator.load_waveform(
                name, is_signal=True, sampling_rate=1000
            )
            assert w.shape == t.shape
            assert len(w) == 2000
            assert sr == 1000
            assert np.isclose(t[0], 0.0)
            assert np.isclose(t[-1], 2.0)

    def test_synthetic_scipy_fallback(self, monkeypatch) -> None:
        def square_wave(t, freq):
            return np.sign(np.sin(2 * np.pi * freq * t))

        def sawtooth_wave(t, freq, width=0.5):
            return 2 * (t * freq - np.floor(t * freq + width)) - 1

        def chirp_signal(t, f0, f1, t1):
            return np.sin(2 * np.pi * (f0 + (f1 - f0) * t / (2 * t1)) * t)

        monkeypatch.setattr(waveform_diff, "square_wave", square_wave, raising=False)
        monkeypatch.setattr(
            waveform_diff, "sawtooth_wave", sawtooth_wave, raising=False
        )
        monkeypatch.setattr(waveform_diff, "chirp_signal", chirp_signal, raising=False)
        monkeypatch.setattr(waveform_diff, "SCIPY_AVAILABLE", False)
        comparator = WaveformComparator()
        for name in ("square", "triangle", "chirp"):
            w, t, sr = comparator.load_waveform(name, is_signal=True, sampling_rate=100)
            assert w.shape == (200,)
            assert t.shape == (200,)
            assert sr == 100

    def test_load_single_column_file(self, tmp_path) -> None:
        path = tmp_path / "single.txt"
        np.savetxt(path, np.array([1.0, 2.0, 3.0, 4.0]))
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert w.shape == (4,)
        assert np.array_equal(t, np.arange(4))
        assert sr == 1000

    def test_load_two_column_file(self, tmp_path) -> None:
        path = tmp_path / "two.txt"
        np.savetxt(path, np.array([[0.0, 1.0], [1.0, 2.0], [2.0, 3.0]]))
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert np.array_equal(w, [1.0, 2.0, 3.0])
        assert np.array_equal(t, [0.0, 1.0, 2.0])
        assert np.isclose(sr, 1.0)

    def test_load_single_row_file(self, tmp_path) -> None:
        # A single row of two columns is squeezed to 1-D by np.loadtxt,
        # so it follows the amplitude-only path.
        path = tmp_path / "single_row.txt"
        np.savetxt(path, np.array([[5.0, 7.0]]))
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert np.array_equal(w, [5.0, 7.0])
        assert np.array_equal(t, [0, 1])
        assert sr == 1000

    def test_load_csv_two_column(self, tmp_path) -> None:
        path = tmp_path / "two.csv"
        path.write_text("time,amplitude\n0.0,1.0\n1.0,2.0\n2.0,3.0\n")
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert np.array_equal(w, [1.0, 2.0, 3.0])
        assert np.isclose(sr, 1.0)

    def test_load_csv_single_column(self, tmp_path) -> None:
        path = tmp_path / "single.csv"
        path.write_text("amplitude\n1.0\n2.0\n3.0\n")
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert w.shape == (3,)
        assert np.array_equal(t, np.arange(3))
        assert sr == 1000

    def test_load_csv_single_row(self, tmp_path) -> None:
        # A single row of two columns is squeezed to 1-D by np.genfromtxt,
        # so it follows the amplitude-only path.
        path = tmp_path / "one_row.csv"
        path.write_text("time,amplitude\n0.0,1.0\n")
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(path), is_signal=False)
        assert np.array_equal(w, [0.0, 1.0])
        assert np.array_equal(t, [0, 1])
        assert sr == 1000

    def test_load_fallback_warning(self, tmp_path, capsys) -> None:
        missing = tmp_path / "missing.txt"
        comparator = WaveformComparator()
        w, t, sr = comparator.load_waveform(str(missing), is_signal=False)
        captured = capsys.readouterr()
        assert "Warning: Could not load" in captured.out
        assert len(w) == 2000
        assert sr == 1000


class TestNormalizeWaveform:
    def test_scales_to_unit_range(self) -> None:
        comparator = WaveformComparator()
        result = comparator.normalize_waveform(np.array([0.0, 1.0, 2.0]))
        assert np.allclose(result, [-1.0, 0.0, 1.0])

    def test_empty_waveform(self) -> None:
        comparator = WaveformComparator()
        result = comparator.normalize_waveform(np.array([]))
        assert result.shape == (0,)

    def test_constant_waveform(self) -> None:
        comparator = WaveformComparator()
        w = np.array([3.0, 3.0, 3.0])
        result = comparator.normalize_waveform(w)
        assert np.array_equal(result, w)


class TestSimpleDtw:
    def test_short_arrays(self) -> None:
        comparator = WaveformComparator()
        w1 = np.array([0.0, 1.0, 0.5, -0.5, 0.0])
        w2 = np.array([0.0, 0.8, 0.4, -0.4, 0.1, 0.0, -0.2])
        path, distance = comparator.simple_dtw(w1, w2)
        assert path == [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        assert distance >= 0

    def test_max_len_slicing(self) -> None:
        comparator = WaveformComparator()
        w1 = np.linspace(0.0, 1.0, 8)
        w2 = np.array([0.0, 1.0])
        path, distance = comparator.simple_dtw(w1, w2, max_len=3)
        assert path == [(0, 0), (1, 1)]
        assert distance >= 0


class TestSlidingWindowDistance:
    def test_both_empty(self) -> None:
        comparator = WaveformComparator()
        ops, a1, a2, dist = comparator.sliding_window_distance([], [])
        assert ops == []
        assert len(a1) == len(a2) == 0
        assert dist == 0

    def test_first_empty(self) -> None:
        comparator = WaveformComparator()
        ops, a1, a2, dist = comparator.sliding_window_distance([], [1.0, 2.0])
        assert len(ops) == 2
        assert all(op == EditOperation.INSERT for op in ops)
        assert np.array_equal(a1, [0.0, 0.0])
        assert np.array_equal(a2, [1.0, 2.0])
        assert dist == 2

    def test_second_empty(self) -> None:
        comparator = WaveformComparator()
        ops, a1, a2, dist = comparator.sliding_window_distance([1.0, 2.0, 3.0], [])
        assert len(ops) == 3
        assert all(op == EditOperation.DELETE for op in ops)
        assert np.array_equal(a1, [1.0, 2.0, 3.0])
        assert dist == 3

    def test_time_warping_dtw(self) -> None:
        comparator = WaveformComparator(time_warping=True)
        w1 = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
        w2 = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
        ops, a1, a2, dist = comparator.sliding_window_distance(w1, w2)
        assert len(ops) == len(a1) == len(a2)
        assert all(op == EditOperation.MATCH for op in ops)
        assert dist == 0

    def test_simple_alignment_no_warping(self) -> None:
        comparator = WaveformComparator(time_warping=False)
        w1 = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        w2 = np.array([0.0, 0.1, 0.2])
        ops, a1, a2, dist = comparator.sliding_window_distance(w1, w2)
        assert len(a1) == len(a2) == 5
        assert len(ops) == 5
        assert any(op == EditOperation.DELETE for op in ops)
        assert dist >= 0

    def test_dtw_failure_falls_back(self, monkeypatch, capsys) -> None:
        def boom(w1, w2, max_len=1000):
            raise RuntimeError("dtw boom")

        monkeypatch.setattr(WaveformComparator, "simple_dtw", boom)
        comparator = WaveformComparator(time_warping=True)
        ops, a1, a2, dist = comparator.sliding_window_distance(
            np.array([0.0, 1.0, 2.0]), np.array([0.0, 1.0])
        )
        captured = capsys.readouterr()
        assert "Warning: DTW failed" in captured.out
        assert len(a1) == len(a2) == len(ops)
        assert dist >= 0

    def test_dtw_custom_warp_path(self, monkeypatch) -> None:
        def custom_path(w1, w2, max_len=1000):
            return [(0, 2), (0, 3), (3, 0)], 1.0

        monkeypatch.setattr(WaveformComparator, "simple_dtw", custom_path)
        comparator = WaveformComparator(time_warping=True)
        ops, a1, a2, dist = comparator.sliding_window_distance(
            np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0])
        )
        assert len(ops) == 3
        assert len(a1) == len(a2) == 3
        assert EditOperation.DELETE in ops
        assert EditOperation.INSERT in ops
        assert dist >= 0


class TestVisualizeComparison:
    def test_show_matrix_true(self) -> None:
        comparator = WaveformComparator()
        w1 = np.linspace(-1.0, 1.0, 20)
        w2 = np.linspace(-1.0, 1.0, 20)
        ops = _build_ops(8, matches=4, substitutes=2, inserts=1, deletes=1)
        fig = comparator.visualize_comparison(w1, w2, np.arange(20), np.arange(20), ops)
        assert fig is not None

    def test_show_matrix_false(self) -> None:
        comparator = WaveformComparator()
        w1 = np.linspace(-1.0, 1.0, 15)
        w2 = np.linspace(-1.0, 1.0, 15)
        fig = comparator.visualize_comparison(
            w1,
            w2,
            np.arange(15),
            np.arange(15),
            _build_ops(15, matches=15),
            show_matrix=False,
        )
        assert fig is not None

    def test_save_plot(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        comparator = WaveformComparator()
        w1 = np.linspace(-1.0, 1.0, 20)
        w2 = np.linspace(-1.0, 1.0, 20)
        fig = comparator.visualize_comparison(
            w1,
            w2,
            np.arange(20),
            np.arange(20),
            _build_ops(20, matches=20),
            save_plot=True,
            output_file="out.png",
        )
        assert fig is not None
        assert (tmp_path / "out.png").exists()

    def test_time_arrays_fallback(self) -> None:
        comparator = WaveformComparator()
        w1 = np.linspace(-1.0, 1.0, 10)
        w2 = np.linspace(-1.0, 1.0, 10)
        fig = comparator.visualize_comparison(
            w1, w2, np.arange(3), np.arange(7), _build_ops(10, matches=10)
        )
        assert fig is not None

    def test_insufficient_data(self) -> None:
        comparator = WaveformComparator()
        fig = comparator.visualize_comparison(
            np.array([]), np.array([]), np.array([]), np.array([]), []
        )
        assert fig is not None

    def test_show_operations_false(self) -> None:
        comparator = WaveformComparator()
        w1 = np.linspace(-1.0, 1.0, 12)
        w2 = np.linspace(-1.0, 1.0, 12)
        fig = comparator.visualize_comparison(
            w1,
            w2,
            np.arange(12),
            np.arange(12),
            _build_ops(12, matches=12),
            show_operations=False,
            show_matrix=False,
        )
        assert fig is not None

    def test_empty_operations_nonempty_waveforms(self) -> None:
        comparator = WaveformComparator()
        w1 = np.array([1.0, 2.0, 3.0])
        w2 = np.array([1.0, 2.0, 3.0])
        fig = comparator.visualize_comparison(
            w1, w2, np.array([0.0, 1.0, 2.0]), np.array([0.0, 1.0, 2.0]), []
        )
        assert fig is not None


class TestGenerateReport:
    @pytest.mark.parametrize(
        ("matches", "total", "expected"),
        [
            (4, 4, "VERY SIMILAR"),
            (3, 4, "SIMILAR"),
            (3, 5, "MODERATELY SIMILAR"),
            (2, 5, "DIFFERENT"),
            (1, 4, "VERY DIFFERENT"),
        ],
    )
    def test_similarity_verdicts(self, matches, total, expected) -> None:
        comparator = WaveformComparator()
        ops = [EditOperation.MATCH] * matches + [EditOperation.SUBSTITUTE] * (
            total - matches
        )
        report = comparator.generate_report(
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
            ops,
            "file1.txt",
            "file2.txt",
        )
        assert "WAVEFORM COMPARISON REPORT" in report
        assert expected in report

    def test_empty_operations_no_statistics(self) -> None:
        comparator = WaveformComparator()
        report = comparator.generate_report([], [], [], "file1.txt", "file2.txt")
        assert "WAVEFORM COMPARISON REPORT" in report
        assert "VERY DIFFERENT" in report
        assert "Statistical Comparison" not in report

    def test_report_with_statistics_section(self) -> None:
        comparator = WaveformComparator()
        report = comparator.generate_report(
            np.array([1.0, 2.0]),
            np.array([3.0, 4.0]),
            [EditOperation.MATCH],
            "a.txt",
            "b.txt",
        )
        assert "Statistical Comparison" in report
        assert "Mean Amplitude" in report


class TestMainCli:
    def test_synthetic_basic(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["wave_diff.py", "sine", "square", "--synthetic", "--rate", "100"],
        )
        main()
        out = capsys.readouterr().out
        assert "Loading waveform 1" in out

    def test_report_file(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "wave_diff.py",
                "sine",
                "square",
                "--synthetic",
                "--rate",
                "100",
                "--report",
            ],
        )
        main()
        assert (tmp_path / "waveform_comparison_report.txt").exists()
        out = capsys.readouterr().out
        assert "Report saved to waveform_comparison_report.txt" in out

    def test_save_plot(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "wave_diff.py",
                "sine",
                "triangle",
                "--synthetic",
                "--rate",
                "100",
                "--save",
                "out.png",
            ],
        )
        main()
        assert (tmp_path / "out.png").exists()

    def test_flag_combinations(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "wave_diff.py",
                "sine",
                "triangle",
                "--synthetic",
                "--rate",
                "50",
                "--threshold",
                "0.05",
                "--window",
                "10",
                "--no-warping",
                "--no-matrix",
            ],
        )
        main()
        out = capsys.readouterr().out
        assert "Performing waveform comparison" in out

    def test_simple_flag(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["wave_diff.py", "ecg", "sine", "--synthetic", "--rate", "50", "--simple"],
        )
        main()
        out = capsys.readouterr().out
        assert "Loading waveform 1: ecg" in out

    def test_file_input(self, tmp_path, monkeypatch, capsys) -> None:
        f1 = tmp_path / "w1.txt"
        f2 = tmp_path / "w2.txt"
        np.savetxt(f1, np.array([[0.0, 1.0], [1.0, 0.5], [2.0, 0.0]]))
        np.savetxt(f2, np.array([[0.0, 0.0], [1.0, 0.5], [2.0, 1.0]]))
        monkeypatch.setattr(sys, "argv", ["wave_diff.py", str(f1), str(f2)])
        main()
        out = capsys.readouterr().out
        assert "Loading waveform 1" in out

    def test_error_exit(self, monkeypatch, capsys) -> None:
        def fail_visualize(self, *args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(
            sys,
            "argv",
            ["wave_diff.py", "sine", "square", "--synthetic", "--rate", "50"],
        )
        monkeypatch.setattr(WaveformComparator, "visualize_comparison", fail_visualize)
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.err


def test_simple_example(capsys) -> None:
    simple_example()
    out = capsys.readouterr().out
    assert "Simple Example Results" in out
