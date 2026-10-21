import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

import pytest
import responses

from windstorm.main import windstorm, _load_local_store, _collect_source_files
from windstorm.common.local_store import ElementStore


def test_offline_source_renders_without_api(tmp_path):
    """--source renders entirely offline: no HTTP, values from local export JSON."""
    # A template referencing a ToolVariable input.
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "template.txt").write_text('{{ windstorm("deltaT") }}')

    # Any network access would raise immediately -> proves offline path.
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add_passthru("http://placeholder.invalid")  # ensure nothing matches

        windstorm(
            "case3",
            source=os.path.join(os.path.dirname(__file__), "mocks", "1_analysis"),
            in_directory=str(tmp_path / "input"),
            out_directory=str(tmp_path / "output"),
        )

    out = tmp_path / "output" / "template.txt"
    assert out.exists()
    assert out.read_text().strip() == "No"


def test_collect_source_files_recurses_nested(tmp_path):
    """_collect_source_files walks subdirectories (nested Defias repos)."""
    models = tmp_path / "models"
    verification = tmp_path / "verification"
    models.mkdir()
    verification.mkdir()
    (models / "a.sysml").write_text("part A;")
    (verification / "b.sysml").write_text("part B;")
    (verification / "b.sysml.export.json").write_text("[]")

    exports, sysmls = _collect_source_files(str(tmp_path))
    # One export json (recurse found it in verification/), two sysml (both levels).
    assert any("b.sysml.export.json" in e for e in exports)
    assert len(sysmls) == 2
    assert any("models" in s for s in sysmls)
    assert any("verification" in s for s in sysmls)


def test_load_local_store_recurses_and_prefers_exports(tmp_path):
    """A nested dir with .export.json in a subdir loads elements (no jar needed)."""
    # Build a subdir and a tiny valid export JSON that adapt() can consume.
    sub = tmp_path / "models"
    sub.mkdir()
    # adapt() expects the merged element-JSON shape (list of {payload, identity}).
    export = [
        {
            "payload": {
                "@id": "abc-123",
                "@type": "PartUsage",
                "declaredName": "myPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "abc-123"},
        }
    ]
    (sub / "model.sysml.export.json").write_text(__import__("json").dumps(export))

    store = _load_local_store(str(tmp_path))
    assert isinstance(store, ElementStore)
    assert store.get("abc-123") is not None


def test_load_local_store_preflight_missing_jar(tmp_path, monkeypatch):
    """Raw .sysml with no toolchain preconditions raises a clear preflight error."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

    monkeypatch.delenv("WINDTRADER_JAR", raising=False)
    with pytest.raises(RuntimeError) as ei:
        _load_local_store(str(tmp_path))
    msg = str(ei.value)
    # A clear preflight error about the offline export toolchain must fire.
    assert ("WINDTRADER_JAR" in msg) or ("Java 21" in msg) or ("windtrader-java" in msg)


def test_load_local_store_preflight_java_missing(tmp_path, monkeypatch):
    """Raw .sysml with no `java` on PATH raises a clear Java preflight error."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

    import windstorm.common.windtrader_jar as wj
    monkeypatch.setattr(wj, "_java_available", lambda: False)
    monkeypatch.delenv("WINDTRADER_JAR", raising=False)
    with pytest.raises(RuntimeError) as ei:
        _load_local_store(str(tmp_path))
    msg = str(ei.value)
    assert "Java 21" in msg


def test_load_local_store_preflight_jar_missing_with_java(tmp_path, monkeypatch):
    """Raw .sysml with java present but WINDTRADER_JAR unset raises a JAR preflight."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

    import windstorm.common.windtrader_jar as wj
    monkeypatch.setattr(wj, "_java_available", lambda: True)
    monkeypatch.delenv("WINDTRADER_JAR", raising=False)
    with pytest.raises(RuntimeError) as ei:
        _load_local_store(str(tmp_path))
    msg = str(ei.value)
    assert "WINDTRADER_JAR" in msg
    assert "windtrader-java" in msg


def test_dump_export_json_copies_exports(tmp_path, monkeypatch):
    """--dump-export-json copies generated .export.json files to the target dir."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")
    dumpdir = tmp_path / "dumps"
    dumpdir.mkdir()

    # Fake batch_export to avoid needing a real jar/JVM in tests.
    fake_export = [
        {
            "payload": {
                "@id": "xyz-9",
                "@type": "PartUsage",
                "declaredName": "p9",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "xyz-9"},
        }
    ]
    import json

    def fake_batch_export(sysml_paths):
        # Write the export next to source (as the real jar does), return the path.
        out = sysml_paths[0] + ".export.json"
        (tmp_path / "src" / "m.sysml.export.json").write_text(json.dumps(fake_export))
        return [out]

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    store = _load_local_store(str(tmp_path), dump_export_json=str(dumpdir))
    assert store.get("xyz-9") is not None
    assert (dumpdir / "m.sysml.export.json").exists()


def test_batch_export_stdin_has_trailing_newline(monkeypatch):
    """Stdin for batch-export must end in a newline so the last path is read."""
    import subprocess as sp

    captured = {}

    def fake_run(cmd, input, capture_output, timeout):
        captured["input"] = input
        runner = sp.run  # real runner against a trivially-succeeding java

        class FakeProc:
            returncode = 0
            stderr = b"batch-export complete\n"
            stdout = b"OK\n"

        return FakeProc()

    import windstorm.common.windtrader_jar as wj
    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")
    monkeypatch.setattr(wj, "_java_available", lambda: True)
    monkeypatch.setattr(wj.subprocess, "run", fake_run)
    monkeypatch.setattr(wj.os.path, "exists", lambda p: True)

    produced = wj.batch_export(["/a.sysml", "/b.sysml"])
    assert captured["input"].endswith(b"\n"), "stdin must end with newline"
    assert captured["input"] == b"/a.sysml\n/b.sysml\n"

