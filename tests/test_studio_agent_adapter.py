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
        project_root=module.PROJECT_ROOT,
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
    assert "USER.md" in context
    assert "勿改 app.py" in context
    assert "Rerun" in context
    assert "Order.py" in context
    assert "側欄忽略" in context
    assert "load_page_data" in context
    assert "read_file" in context
    assert "edit_file" in context
    assert "write_file" in context
    assert "1_Home.py" in context
    assert "home.json" in context
    assert "【新增頁】" in context
    assert "playground.json" not in context
    assert "相對路徑會解析到 ~/.peas-agent/workspace" not in context
    assert "學生" not in context


def test_save_uploaded_chat_image_returns_absolute_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch)
    chat_image_dir = tmp_path / "uploads" / "chat_images"
    monkeypatch.setattr(module, "CHAT_IMAGE_DIR", chat_image_dir)
    monkeypatch.setattr(module, "PEAS_WORKSPACE", tmp_path)
    monkeypatch.setattr(module, "_ensure_peas_dirs", lambda: chat_image_dir.mkdir(parents=True, exist_ok=True))

    class FakeUpload:
        name = "shot.png"

        @staticmethod
        def getvalue() -> bytes:
            return b"fake-png"

    rel_or_abs, err = module._save_uploaded_chat_image(FakeUpload())
    assert err is None
    assert rel_or_abs is not None
    assert Path(rel_or_abs).is_absolute()
    assert Path(rel_or_abs).is_file()


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
    assert "使用者問題：" in chat_block
    assert "學生問題：" not in chat_block


def test_templates_avoid_task_in_extra_context() -> None:
    root = Path(__file__).parents[1] / "src" / "add_studio_shell" / "templates" / "studio_shell"
    paths = [
        root / "app.py",
        root / "pages" / "1_Home.py",
        root / "pages" / "2_Playground.py",
        root / "pages" / "3_UI_Cheatsheet.py",
    ]
    combined = "\n".join(p.read_text(encoding="utf-8") for p in paths)
    assert "【任務】" not in combined
    assert "【本頁焦點】" not in combined


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
