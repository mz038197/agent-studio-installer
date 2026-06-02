from __future__ import annotations

import json
import sys
import types
from importlib import util
from pathlib import Path

import pytest


class _FakeSettings:
    voice = "nova"
    instructions = "default instructions"
    speed = None

    @classmethod
    def from_env(cls):
        return cls()


def _load_agent_panel_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_streamlit = types.SimpleNamespace(session_state={})
    fake_dotenv = types.SimpleNamespace(load_dotenv=lambda *_args, **_kwargs: None)
    fake_openai_tts = types.SimpleNamespace(
        Settings=_FakeSettings,
        stream_tts_play=lambda *_args, **_kwargs: None,
    )
    fake_openai_tts_settings = types.SimpleNamespace(
        MIN_TTS_SPEED=0.25,
        MAX_TTS_SPEED=4.0,
    )

    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    monkeypatch.setitem(sys.modules, "dotenv", fake_dotenv)
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
    spec = util.spec_from_file_location("agent_panel_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "WORKSPACE_DIR", tmp_path / "workspace")
    monkeypatch.setattr(module, "USER_SETTINGS_PATH", tmp_path / "workspace" / "user_settings.json")
    return module


def _normalize_tts_preferences(
    raw: dict[str, object],
    defaults: dict[str, object],
    *,
    voice_options: set[str],
    min_speed: float,
    max_speed: float,
) -> dict[str, object]:
    voice = str(raw.get("tts_voice", defaults["tts_voice"]))
    if voice not in voice_options:
        voice = str(defaults["tts_voice"])

    try:
        speed = float(raw.get("tts_speed", defaults["tts_speed"]))
    except (TypeError, ValueError):
        speed = float(defaults["tts_speed"])
    speed = max(min_speed, min(max_speed, speed))

    return {
        "tts_enabled": bool(raw.get("tts_enabled", defaults["tts_enabled"])),
        "tts_voice": voice,
        "tts_instructions": str(raw.get("tts_instructions", defaults["tts_instructions"])),
        "tts_speed": speed,
    }


def test_user_settings_roundtrip(tmp_path: Path) -> None:
    settings_path = tmp_path / "user_settings.json"
    defaults = {
        "tts_enabled": False,
        "tts_voice": "nova",
        "tts_instructions": "",
        "tts_speed": 1.0,
    }
    voice_options = {"nova", "alloy"}

    payload = {
        "tts_enabled": True,
        "tts_voice": "alloy",
        "tts_instructions": "用輕快的語氣說話。",
        "tts_speed": 1.25,
    }
    settings_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    normalized = _normalize_tts_preferences(
        loaded,
        defaults,
        voice_options=voice_options,
        min_speed=0.5,
        max_speed=2.0,
    )

    assert normalized == {
        "tts_enabled": True,
        "tts_voice": "alloy",
        "tts_instructions": "用輕快的語氣說話。",
        "tts_speed": 1.25,
    }

    settings_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    roundtrip = json.loads(settings_path.read_text(encoding="utf-8"))
    assert roundtrip["tts_voice"] == "alloy"


def test_user_settings_invalid_voice_falls_back_to_default(tmp_path: Path) -> None:
    defaults = {
        "tts_enabled": False,
        "tts_voice": "nova",
        "tts_instructions": "",
        "tts_speed": 1.0,
    }
    normalized = _normalize_tts_preferences(
        {"tts_voice": "unknown-voice", "tts_speed": "bad"},
        defaults,
        voice_options={"nova"},
        min_speed=0.5,
        max_speed=2.0,
    )
    assert normalized["tts_voice"] == "nova"
    assert normalized["tts_speed"] == 1.0


def test_agent_panel_creates_default_user_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)

    message = module._ensure_user_settings_file()

    assert message is None
    payload = json.loads((tmp_path / "workspace" / "user_settings.json").read_text(encoding="utf-8"))
    assert payload == {
        "tts_enabled": False,
        "tts_voice": "nova",
        "tts_instructions": "default instructions",
        "tts_speed": 1.0,
    }


def test_agent_panel_save_user_settings_reports_write_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    monkeypatch.setattr(module, "_ensure_workspace_dir", lambda: (_ for _ in ()).throw(OSError("no access")))

    message = module._save_user_settings({"tts_voice": "nova"})

    assert message is not None
    assert "無法寫入語音設定檔" in message


def test_should_reload_tts_for_page(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)

    assert module._should_reload_tts_for_page(None, "Home") is True
    assert module._should_reload_tts_for_page("Home", "Home") is False
    assert module._should_reload_tts_for_page("Home", "Playground") is True


def test_sync_tts_preferences_for_page_reloads_on_page_change(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / "workspace" / "user_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "tts_enabled": True,
                "tts_voice": "alloy",
                "tts_instructions": "from file",
                "tts_speed": 1.5,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    session_state = module.st.session_state
    session_state["_studio_tts_page_name"] = "Home"
    session_state["studio_tts_enabled"] = False
    session_state["studio_tts_voice"] = "nova"
    session_state["studio_tts_instructions"] = "stale"
    session_state["studio_tts_speed"] = 1.0

    module._sync_tts_preferences_for_page("Playground")

    assert session_state["studio_tts_enabled"] is True
    assert session_state["studio_tts_voice"] == "alloy"
    assert session_state["studio_tts_instructions"] == "from file"
    assert session_state["studio_tts_speed"] == 1.5
    assert session_state["_studio_tts_page_name"] == "Playground"


def test_sync_tts_preferences_for_page_skips_reload_on_same_page(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / "workspace" / "user_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "tts_enabled": True,
                "tts_voice": "alloy",
                "tts_instructions": "from file",
                "tts_speed": 1.5,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    session_state = module.st.session_state
    session_state["_studio_tts_page_name"] = "Home"
    session_state["studio_tts_enabled"] = False
    session_state["studio_tts_voice"] = "nova"
    session_state["studio_tts_instructions"] = "in progress"
    session_state["studio_tts_speed"] = 1.0

    module._sync_tts_preferences_for_page("Home")

    assert session_state["studio_tts_voice"] == "nova"
    assert session_state["studio_tts_instructions"] == "in progress"
