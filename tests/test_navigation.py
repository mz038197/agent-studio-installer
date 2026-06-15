from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path

import pytest


def _load_navigation_module():
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "add_studio_shell"
        / "templates"
        / "studio_shell"
        / "navigation.py"
    )
    spec = util.spec_from_file_location("navigation_test", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_page_title_from_path_builtin_override() -> None:
    nav = _load_navigation_module()
    assert nav.page_title_from_path(Path("3_UI_Cheatsheet.py")) == "UI 元件詞彙表"
    assert nav.page_title_from_path(Path("1_Home.py")) == "Home"


def test_page_title_from_path_derives_from_stem() -> None:
    nav = _load_navigation_module()
    assert nav.page_title_from_path(Path("4_Order.py")) == "Order"
    assert nav.page_title_from_path(Path("9_My_Page.py")) == "My Page"


def test_discover_file_pages_sorts_and_filters(tmp_path: Path) -> None:
    nav = _load_navigation_module()
    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    (pages_dir / "9_MyPage.py").write_text("# x\n", encoding="utf-8")
    (pages_dir / "4_Order.py").write_text("# x\n", encoding="utf-8")
    (pages_dir / "Order.py").write_text("# ignored\n", encoding="utf-8")
    (pages_dir / "_draft.py").write_text("# ignored\n", encoding="utf-8")
    (pages_dir / "helper.py").write_text("# ignored\n", encoding="utf-8")

    discovered = nav.discover_file_pages(pages_dir)

    assert [path.name for path in discovered] == ["4_Order.py", "9_MyPage.py"]


def test_discover_file_pages_empty_when_missing_dir(tmp_path: Path) -> None:
    nav = _load_navigation_module()
    assert nav.discover_file_pages(tmp_path / "missing") == []


def test_build_navigation_pages_includes_overview_and_custom_pages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shell_root = tmp_path / "studio_shell"
    pages_dir = shell_root / "pages"
    pages_dir.mkdir(parents=True)
    (pages_dir / "1_Home.py").write_text("# home\n", encoding="utf-8")
    (pages_dir / "9_MyPage.py").write_text("# custom\n", encoding="utf-8")

    fake_pages: list[object] = []

    class FakePage:
        def __init__(self, target: object, **kwargs: object) -> None:
            self.target = target
            self.kwargs = kwargs
            fake_pages.append(self)

    fake_streamlit = types.SimpleNamespace(Page=FakePage)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    nav = _load_navigation_module()

    def overview() -> None:
        return None

    pages = nav.build_navigation_pages(shell_root=shell_root, overview_callable=overview)

    assert list(pages) == ["Studio"]
    assert len(pages["Studio"]) == 3
    assert pages["Studio"][0].kwargs["title"] == "總覽"
    assert pages["Studio"][0].kwargs.get("default") is True
    assert pages["Studio"][1].kwargs["title"] == "Home"
    assert pages["Studio"][2].kwargs["title"] == "MyPage"
