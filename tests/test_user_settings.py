from __future__ import annotations

import json
from pathlib import Path

import pytest


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
