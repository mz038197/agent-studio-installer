from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_agent_panel_module(monkeypatch: pytest.MonkeyPatch):
    fake_streamlit = types.SimpleNamespace(session_state={})
    fake_openai_tts = types.SimpleNamespace(
        Settings=lambda **kwargs: types.SimpleNamespace(**kwargs),
        stream_tts_play=lambda *_args, **_kwargs: None,
    )
    fake_openai_tts_settings = types.SimpleNamespace(
        MIN_TTS_SPEED=0.25,
        MAX_TTS_SPEED=4.0,
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "openai_tts", fake_openai_tts)
    monkeypatch.setitem(sys.modules, "openai_tts.settings", fake_openai_tts_settings)

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    )
    spec = util.spec_from_file_location("agent_panel_adapter_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_create_agent_for_session_uses_agent_create(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    session_dir = tmp_path / "sessions"
    session_dir.mkdir(parents=True)
    session_file = session_dir / "session_test.jsonl"
    session_file.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(module, "SESSION_DIR", session_dir)

    fake_agent = MagicMock()
    fake_agent_class = MagicMock()
    fake_agent_class.create.return_value = fake_agent
    fake_peas = types.SimpleNamespace(Agent=fake_agent_class)
    monkeypatch.setitem(sys.modules, "peas_agent", fake_peas)

    agent = module._create_agent_for_session("session_test.jsonl")

    fake_agent_class.create.assert_called_once_with(session_name="session_test.jsonl")
    assert agent is fake_agent


def test_create_agent_for_session_import_error_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    session_dir = tmp_path / "sessions"
    session_dir.mkdir(parents=True)
    (session_dir / "session_test.jsonl").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(module, "SESSION_DIR", session_dir)
    monkeypatch.delitem(sys.modules, "peas_agent", raising=False)

    with patch.dict(sys.modules, {"peas_agent": None}):
        with pytest.raises(RuntimeError, match="peas-agent-core"):
            module._create_agent_for_session("session_test.jsonl")


def test_create_agent_for_session_rejects_invalid_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_agent_panel_module(monkeypatch)

    with pytest.raises(RuntimeError, match="對話紀錄無效"):
        module._create_agent_for_session("../escape.jsonl")
