"""Tests for musicprod.tools.waveform_plotter."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def test_file_not_found():
    from musicprod.tools.waveform_plotter import plot_waveform

    with pytest.raises(FileNotFoundError, match="not found"):
        plot_waveform("/non/existent/file.mp3")


def test_invalid_dimensions(tmp_path):
    from musicprod.tools.waveform_plotter import plot_waveform

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with pytest.raises(ValueError, match="must be positive"):
        plot_waveform(str(src), width=0, height=4)


def test_plot_saves_png(tmp_path):
    from musicprod.tools.waveform_plotter import plot_waveform

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050
    fake_times = np.linspace(0, 1, 22050)

    mock_fig = MagicMock()
    mock_ax = MagicMock()

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.times_like", return_value=fake_times),
        patch("matplotlib.pyplot.subplots", return_value=(mock_fig, mock_ax)),
        patch("matplotlib.pyplot.close"),
    ):
        result = plot_waveform(str(src))

    assert result.suffix == ".png"
    assert "_waveform" in result.name
    mock_fig.savefig.assert_called_once()


def test_plot_custom_output(tmp_path):
    from musicprod.tools.waveform_plotter import plot_waveform

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)
    dest = tmp_path / "wave.png"

    fake_y = np.zeros(22050, dtype=np.float32)
    fake_sr = 22050
    fake_times = np.linspace(0, 1, 22050)

    mock_fig = MagicMock()
    mock_ax = MagicMock()

    with (
        patch("librosa.load", return_value=(fake_y, fake_sr)),
        patch("librosa.times_like", return_value=fake_times),
        patch("matplotlib.pyplot.subplots", return_value=(mock_fig, mock_ax)),
        patch("matplotlib.pyplot.close"),
    ):
        result = plot_waveform(str(src), output_path=str(dest))

    assert result == dest.resolve()


def test_plot_error_raises_runtime(tmp_path):
    from musicprod.tools.waveform_plotter import plot_waveform

    src = tmp_path / "audio.mp3"
    src.write_bytes(b"\x00" * 64)

    with patch("librosa.load", side_effect=Exception("decode error")):
        with pytest.raises(RuntimeError, match="Waveform plotting failed"):
            plot_waveform(str(src))
