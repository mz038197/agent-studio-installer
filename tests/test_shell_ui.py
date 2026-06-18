from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path

import pytest


def _load_shell_ui_module(monkeypatch: pytest.MonkeyPatch):
    fake_streamlit = types.SimpleNamespace(markdown=lambda *_a, **_k: None)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "shell_ui.py"
    )
    spec = util.spec_from_file_location("shell_ui_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_page_slug_lowercases_name(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_shell_ui_module(monkeypatch)
    assert module.page_slug("Playground") == "playground"


def test_shared_data_path_uses_data_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_shell_ui_module(monkeypatch)
    shell_root = tmp_path / "studio_shell"
    path = module.shared_data_path("Playground", shell_root=shell_root)
    assert path == shell_root / "data" / "playground.json"


def test_load_page_data_missing_file_returns_empty_dict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_shell_ui_module(monkeypatch)
    shell_root = tmp_path / "studio_shell"
    assert module.load_page_data("Home", shell_root=shell_root) == {}


def test_save_and_load_page_data_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_shell_ui_module(monkeypatch)
    shell_root = tmp_path / "studio_shell"
    payload = {"nickname": "小明", "goal": "心情儀表板"}
    module.save_page_data("Home", payload, shell_root=shell_root)
    assert module.load_page_data("Home", shell_root=shell_root) == payload


def test_load_page_data_invalid_json_returns_empty_dict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = _load_shell_ui_module(monkeypatch)
    shell_root = tmp_path / "studio_shell"
    data_dir = shell_root / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "home.json").write_text("{not json", encoding="utf-8")
    assert module.load_page_data("Home", shell_root=shell_root) == {}


def test_inject_multimodal_chatinput_theme_fix_targets_textarea_color(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_iframe(src: str, **kwargs: object) -> None:
        captured["src"] = src
        captured["kwargs"] = kwargs

    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.markdown = lambda *_a, **_k: None
    fake_streamlit.iframe = fake_iframe
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "shell_ui.py"
    )
    spec = util.spec_from_file_location("shell_ui_theme_fix_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)

    module.inject_multimodal_chatinput_theme_fix()
    html = str(captured["src"])
    assert "textarea" in html
    assert "var(--text-color)" in html
    assert captured["kwargs"] == {"height": 0}
