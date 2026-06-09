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

    fake_agent_class.create.assert_called_once_with(
        session_name="session_test.jsonl",
        host_context=module.studio_base_context(),
    )
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


def test_ensure_valid_current_session_clears_stale_name_when_no_sessions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    session_dir = tmp_path / "sessions"
    session_dir.mkdir(parents=True)
    monkeypatch.setattr(module, "SESSION_DIR", session_dir)
    module.st.session_state["session_name"] = "session_missing.jsonl"

    assert module._ensure_valid_current_session([]) is None
    assert "session_name" not in module.st.session_state


def test_new_session_can_be_created_after_all_sessions_removed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    session_dir = tmp_path / "sessions"
    session_dir.mkdir(parents=True)
    monkeypatch.setattr(module, "SESSION_DIR", session_dir)
    monkeypatch.setattr(module, "_ensure_peas_dirs", lambda: None)

    assert module._ensure_valid_current_session([]) is None
    module._set_current_session(module._new_session_path())

    assert module.st.session_state["session_name"].endswith(".jsonl")
    assert (session_dir / module.st.session_state["session_name"]).is_file()


def test_studio_base_context_mentions_shared_data_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    context = module.studio_base_context()
    assert "studio_shell/pages" in context or "pages" in context
    assert "data" in context
    assert "load_page_data" in context
    assert "write_file" in context
    assert "home.json" in context
    assert "playground.json" in context


def test_render_chat_panel_user_prompt_uses_extra_context_only() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    ).read_text(encoding="utf-8")
    chat_block = source.split('if user_text := st.chat_input("詢問 Agent..."', 1)[1]
    assert "studio_base_context(page_name)" not in chat_block
    assert "【目前頁面狀態】" in chat_block


def test_render_chat_panel_reruns_after_successful_chat() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    ).read_text(encoding="utf-8")
    chat_block = source.split('if user_text := st.chat_input("詢問 Agent..."', 1)[1]
    assert "st.rerun()" in chat_block


def test_installer_preserves_data_directory_on_update() -> None:
    from add_studio_shell.installer import UPDATE_PRESERVE_DIRS

    assert "data" in UPDATE_PRESERVE_DIRS


def test_render_chat_panel_avoids_empty_selectbox() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    ).read_text(encoding="utf-8")
    toolbar = source.split("pick_col, new_col, del_col = st.columns([6, 1, 1])", 1)[1]
    assert "if ids:" in toolbar
    assert toolbar.index("if ids:") < toolbar.index("pick_col.selectbox")
