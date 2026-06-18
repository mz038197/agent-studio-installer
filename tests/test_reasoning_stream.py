from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path

import pytest


def _load_agent_panel_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_streamlit = types.SimpleNamespace(session_state={})
    fake_openai_tts = types.SimpleNamespace(
        Settings=types.SimpleNamespace(
            DEFAULT_INSTRUCTIONS="instructions",
            DEFAULT_SPEED=1.25,
            DEFAULT_VOICE="nova",
        ),
        stream_tts_play=lambda *_args, **_kwargs: None,
    )
    fake_openai_tts_settings = types.SimpleNamespace(
        MIN_TTS_SPEED=0.25,
        MAX_TTS_SPEED=4.0,
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "openai_tts", fake_openai_tts)
    monkeypatch.setitem(sys.modules, "openai_tts.settings", fake_openai_tts_settings)
    monkeypatch.setitem(
        sys.modules,
        "st_multimodal_chatinput",
        types.SimpleNamespace(multimodal_chatinput=lambda **_k: None),
    )

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    )
    spec = util.spec_from_file_location("agent_panel_reasoning_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_commit_reasoning_round_appends_and_clears_buffer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    segments: list[str] = []
    current = ["think", "ing"]

    module._commit_reasoning_round(segments, current)

    assert segments == ["thinking"]
    assert current == []


def test_commit_reasoning_round_skips_empty_buffer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    segments: list[str] = []
    current: list[str] = []

    module._commit_reasoning_round(segments, current)

    assert segments == []


def test_merged_reasoning_text_joins_segments_with_separator(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)

    merged = module._merged_reasoning_text(["round1"], ["round2"])

    assert merged == f"round1{module.REASONING_ROUND_SEPARATOR}round2"


def test_merged_reasoning_text_after_commit_sequence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    segments: list[str] = []
    current = ["a"]

    module._commit_reasoning_round(segments, current)
    current.extend(["b"])
    merged = module._merged_reasoning_text(segments, current)

    assert merged == f"a{module.REASONING_ROUND_SEPARATOR}b"


def test_on_stream_reset_does_not_clear_reasoning_segments_in_source() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    ).read_text(encoding="utf-8")
    block = source.split("def on_stream_reset() -> None:", 1)[1].split("try:", 1)[0]

    assert "reasoning_segments.clear()" not in block
    assert "reasoning_slot.empty()" not in block
    assert "reasoning_parts.clear()" not in block
    assert "_commit_reasoning_round(reasoning_segments, reasoning_parts)" in block
    assert "TOOL_RUN_PLACEHOLDER" in block
