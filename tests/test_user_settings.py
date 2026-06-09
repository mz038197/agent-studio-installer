from __future__ import annotations

import json
import sys
import types
from importlib import util
from pathlib import Path

import pytest


class _FakeSettings:
    def __init__(
        self,
        *,
        api_key: str = "",
        voice: str = "nova",
        instructions: str = "default instructions",
        speed: float | None = None,
        **kwargs: object,
    ) -> None:
        self.api_key = api_key
        self.voice = voice
        self.instructions = instructions
        self.speed = speed
        self.extra_kwargs = kwargs


def _load_agent_panel_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    fake_streamlit = types.SimpleNamespace(session_state={})
    fake_openai_tts = types.SimpleNamespace(
        Settings=_FakeSettings,
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
    spec = util.spec_from_file_location("agent_panel_under_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    peas_home = tmp_path / ".peas-agent"
    workspace = peas_home / "workspace"
    monkeypatch.setattr(module, "PEAS_AGENT_HOME", peas_home)
    monkeypatch.setattr(module, "PEAS_WORKSPACE", workspace)
    monkeypatch.setattr(module, "SESSION_DIR", workspace / "sessions")
    monkeypatch.setattr(module, "CHAT_IMAGE_DIR", workspace / "uploads" / "chat_images")
    monkeypatch.setattr(module, "TTS_CONFIG_PATH", peas_home / "tts.json")
    monkeypatch.setattr(module, "MIGRATION_MARKER_PATH", peas_home / ".studio_migration_done")
    return module


def _normalize_tts_config(
    raw: dict[str, object],
    defaults: dict[str, object],
    *,
    voice_options: set[str],
    min_speed: float,
    max_speed: float,
) -> dict[str, object]:
    voice = str(raw.get("voice", raw.get("tts_voice", defaults["voice"])))
    if voice not in voice_options:
        voice = str(defaults["voice"])

    try:
        speed = float(raw.get("speed", raw.get("tts_speed", defaults["speed"])))
    except (TypeError, ValueError):
        speed = float(defaults["speed"])
    speed = max(min_speed, min(max_speed, speed))

    enabled = raw.get("enabled", raw.get("tts_enabled", defaults["enabled"]))
    instructions = raw.get("instructions", raw.get("tts_instructions", defaults["instructions"]))

    return {
        "api_key": str(raw.get("api_key", defaults["api_key"])),
        "base_url": str(raw.get("base_url", defaults["base_url"])),
        "enabled": bool(enabled),
        "voice": voice,
        "instructions": str(instructions),
        "speed": speed,
    }


def test_tts_config_roundtrip(tmp_path: Path) -> None:
    settings_path = tmp_path / "tts.json"
    defaults = {
        "api_key": "",
        "base_url": "",
        "enabled": False,
        "voice": "nova",
        "instructions": "",
        "speed": 1.0,
    }
    voice_options = {"nova", "alloy"}

    payload = {
        "api_key": "sk-test",
        "enabled": True,
        "voice": "alloy",
        "instructions": "用輕快的語氣說話。",
        "speed": 1.25,
    }
    settings_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    normalized = _normalize_tts_config(
        loaded,
        defaults,
        voice_options=voice_options,
        min_speed=0.5,
        max_speed=2.0,
    )

    assert normalized == {
        "api_key": "sk-test",
        "base_url": "",
        "enabled": True,
        "voice": "alloy",
        "instructions": "用輕快的語氣說話。",
        "speed": 1.25,
    }

    settings_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    roundtrip = json.loads(settings_path.read_text(encoding="utf-8"))
    assert roundtrip["voice"] == "alloy"


def test_tts_config_invalid_voice_falls_back_to_default(tmp_path: Path) -> None:
    defaults = {
        "api_key": "",
        "base_url": "",
        "enabled": False,
        "voice": "nova",
        "instructions": "",
        "speed": 1.0,
    }
    normalized = _normalize_tts_config(
        {"voice": "unknown-voice", "speed": "bad"},
        defaults,
        voice_options={"nova"},
        min_speed=0.5,
        max_speed=2.0,
    )
    assert normalized["voice"] == "nova"
    assert normalized["speed"] == 1.0


def test_agent_panel_creates_default_tts_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)

    message = module._ensure_tts_config_file()

    assert message is None
    payload = json.loads((tmp_path / ".peas-agent" / "tts.json").read_text(encoding="utf-8"))
    assert payload == {
        "api_key": "",
        "base_url": "",
        "enabled": False,
        "voice": "nova",
        "instructions": "用台灣繁體中文說話。",
        "speed": 1.0,
    }


def test_agent_panel_repairs_empty_tts_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / ".peas-agent" / "tts.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("", encoding="utf-8")

    message = module._ensure_tts_config_file()

    assert message is None
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload == {
        "api_key": "",
        "base_url": "",
        "enabled": False,
        "voice": "nova",
        "instructions": "用台灣繁體中文說話。",
        "speed": 1.0,
    }


def test_agent_panel_save_tts_config_reports_write_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    original_write_text = Path.write_text

    def _fail_tts_write(self: Path, *args, **kwargs):
        if self.name == "tts.json":
            raise OSError("no access")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _fail_tts_write)

    message = module._save_tts_config({"voice": "nova"})

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
    settings_path = tmp_path / ".peas-agent" / "tts.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "voice": "alloy",
                "instructions": "from file",
                "speed": 1.5,
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


def test_sync_tts_preferences_for_page_reloads_from_file_on_same_page(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / ".peas-agent" / "tts.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "voice": "alloy",
                "instructions": "from file",
                "speed": 1.5,
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

    assert session_state["studio_tts_voice"] == "alloy"
    assert session_state["studio_tts_instructions"] == "from file"
    assert session_state["studio_tts_speed"] == 1.5


def test_sync_tts_preferences_persists_pending_widget_changes_before_reload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / ".peas-agent" / "tts.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "voice": "alloy",
                "instructions": "from file",
                "speed": 1.5,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    session_state = module.st.session_state
    session_state["_studio_tts_page_name"] = "Home"
    session_state["_studio_tts_snapshot"] = {
        "api_key": "",
        "base_url": "",
        "enabled": True,
        "voice": "alloy",
        "instructions": "from file",
        "speed": 1.5,
    }
    session_state["studio_tts_enabled"] = True
    session_state["studio_tts_voice"] = "alloy"
    session_state["studio_tts_instructions"] = "changed in widget"
    session_state["studio_tts_speed"] = 1.25

    module._sync_tts_preferences_for_page("Home")

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload["instructions"] == "changed in widget"
    assert payload["speed"] == 1.25
    assert session_state["studio_tts_instructions"] == "changed in widget"
    assert session_state["studio_tts_speed"] == 1.25


def test_build_tts_settings_for_playback_passes_api_key_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    settings_path = tmp_path / ".peas-agent" / "tts.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "api_key": "sk-test",
                "base_url": "https://example.com/v1",
                "enabled": True,
                "voice": "alloy",
                "instructions": "test",
                "speed": 1.0,
            }
        ),
        encoding="utf-8",
    )
    session_state = module.st.session_state
    session_state["studio_tts_enabled"] = True
    session_state["studio_tts_voice"] = "alloy"
    session_state["studio_tts_instructions"] = "test"
    session_state["studio_tts_speed"] = 1.0

    result = module._build_tts_settings_for_playback()

    assert result is not None
    assert result.api_key == "sk-test"
    assert result.voice == "alloy"
    assert result.instructions == "test"
    assert result.speed == 1.0
    assert result.extra_kwargs == {}


def test_build_tts_settings_for_playback_returns_none_without_api_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_agent_panel_module(monkeypatch, tmp_path)
    module._ensure_tts_config_file()
    session_state = module.st.session_state
    session_state["studio_tts_enabled"] = True
    session_state["studio_tts_voice"] = "nova"
    session_state["studio_tts_instructions"] = "test"
    session_state["studio_tts_speed"] = 1.0

    assert module._build_tts_settings_for_playback() is None


def test_assistant_reply_is_saved_before_tts_playback() -> None:
    source = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "agent_panel.py"
    ).read_text(encoding="utf-8")
    user_message_flow = source.split('if user_text := st.chat_input("詢問 Agent...", key="studio_chat"):', 1)[1]

    save_index = user_message_flow.index('st.session_state["studio_chat_history"].append(("assistant", answer))')
    tts_index = user_message_flow.index("stream_tts_play(answer, tts_settings)")

    assert save_index < tts_index
