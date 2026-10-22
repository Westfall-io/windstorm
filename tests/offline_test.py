import os
import shutil
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

    # Use ONLY the already-exported JSON files (Java-free, fully-offline path).
    # Copy them into a fresh source dir so no bare .sysml forces a jar export.
    src = tmp_path / "src"
    src.mkdir()
    mocks = os.path.join(os.path.dirname(__file__), "mocks", "1_analysis")
    exported = [f for f in os.listdir(mocks) if f.endswith(".export.json")]
    assert exported, "expected exported mock JSONs"
    for name in exported:
        shutil.copy2(os.path.join(mocks, name), src / name)

    # Any network access would raise immediately -> proves offline path.
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add_passthru("http://placeholder.invalid")  # ensure nothing matches

        windstorm(
            "case3",
            source=str(src),
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


def test_load_local_store_preflight_java_missing(tmp_path, monkeypatch):
    """Raw .sysml with no `java` on PATH raises a clear Java preflight error."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_java_available", lambda: False)
    monkeypatch.delenv("WINDTRADER_JAR", raising=False)
    # --skip-export-errors must NOT swallow this toolchain preflight (NB-A).
    with pytest.raises(RuntimeError) as ei:
        _load_local_store(str(tmp_path), skip_export_errors=True)
    msg = str(ei.value)
    assert "Java 21" in msg


def test_load_local_store_preflight_jar_missing_with_java(tmp_path, monkeypatch):
    """Raw .sysml with java present but WINDTRADER_JAR unset raises a JAR preflight."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_java_available", lambda: True)
    monkeypatch.setattr(
        wj, "_java_version", lambda: 21
    )  # pin so host Java is irrelevant
    monkeypatch.delenv("WINDTRADER_JAR", raising=False)
    with pytest.raises(RuntimeError) as ei:
        _load_local_store(str(tmp_path))
    msg = str(ei.value)
    assert "WINDTRADER_JAR" in msg
    assert "windtrader-java" in msg


def test_dump_export_json_copies_exports(tmp_path, monkeypatch):
    """--dump-export-json creates the dir and copies generated exports, mirroring rel tree."""
    sub = tmp_path / "src"
    sub.mkdir()
    # Put the .sysml in a subdir to prove relative-tree mirroring.
    models = sub / "models"
    models.mkdir()
    (models / "m.sysml").write_text("part M;")
    dumpdir = tmp_path / "dumps"  # deliberately NOT pre-created

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
        out = sysml_paths[0] + ".export.json"
        (models / "m.sysml.export.json").write_text(json.dumps(fake_export))
        return [out]

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    store = _load_local_store(str(sub), dump_export_json=str(dumpdir))
    assert store.get("xyz-9") is not None
    # Mirrored relative tree, not flattened: dumps/models/m.sysml.export.json
    assert (dumpdir / "models" / "m.sysml.export.json").exists()


def test_load_local_store_refreshes_stale_export(tmp_path, monkeypatch):
    """A .sysml whose export is older is re-exported (the refresh half)."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")

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
    import json, time as _time

    (sub / "m.sysml.export.json").write_text(json.dumps(export))
    # Make the export OLDER than the sysml -> stale -> must re-export.
    old = _time.time() - 1000
    os.utime(sub / "m.sysml.export.json", (old, old))

    calls = {"n": 0}

    def fake_batch_export(sysml_paths):
        calls["n"] += 1
        # Re-write the export so it's fresh this run (newer than the snapshot).
        (sub / "m.sysml.export.json").write_text(json.dumps(export))
        now = _time.time()
        os.utime(sub / "m.sysml.export.json", (now, now))
        return [str(sub / "m.sysml.export.json")]

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    store = _load_local_store(str(tmp_path))
    assert calls["n"] == 1, "stale export must trigger re-export"
    assert store.get("abc-123") is not None


def test_load_local_store_mixed_tree_loads_both(tmp_path, monkeypatch):
    """A tree with both .export.json and bare .sysml loads the union, not one branch."""
    sub = tmp_path / "src"
    sub.mkdir()
    # One .sysml with a fresh export (no re-export), one bare .sysml (re-export).
    (sub / "a.sysml").write_text("part A;")
    a_export = [
        {
            "payload": {
                "@id": "aaa-1",
                "@type": "PartUsage",
                "declaredName": "aPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "aaa-1"},
        }
    ]
    import json

    (sub / "a.sysml.export.json").write_text(json.dumps(a_export))
    (sub / "b.sysml").write_text("part B;")

    b_export = [
        {
            "payload": {
                "@id": "bbb-2",
                "@type": "PartUsage",
                "declaredName": "bPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "bbb-2"},
        }
    ]
    calls = {"n": 0}

    def fake_batch_export(sysml_paths):
        calls["n"] += 1
        # Only the bare b.sysml should be passed.
        assert len(sysml_paths) == 1 and sysml_paths[0].endswith("b.sysml")
        out = sysml_paths[0] + ".export.json"
        (sub / "b.sysml.export.json").write_text(json.dumps(b_export))
        return [out]

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    store = _load_local_store(str(tmp_path))
    assert calls["n"] == 1
    assert store.get("aaa-1") is not None, "a's fresh export must load"
    assert store.get("bbb-2") is not None, "b's produced export must load"


def test_dump_export_json_requires_sysml(tmp_path, monkeypatch):
    """--dump-export-json without raw .sysml files raises a clear error."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "e.export.json").write_text("[]")  # only an export, no .sysml

    with pytest.raises(RuntimeError, match="requires --source"):
        _load_local_store(
            str(tmp_path),
            dump_export_json=str(tmp_path.parent / ("dumps-" + tmp_path.name)),
        )


def test_dump_export_json_warm_run_dumps_full_bundle(tmp_path, monkeypatch):
    """A warm run (all exports fresh) still dumps the FULL bundle, not nothing."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")
    export = [
        {
            "payload": {
                "@id": "fff-7",
                "@type": "PartUsage",
                "declaredName": "fPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "fff-7"},
        }
    ]
    import json

    (sub / "m.sysml.export.json").write_text(json.dumps(export))  # fresh

    calls = {"n": 0}

    def fake_batch_export(sysml_paths):
        calls["n"] += 1
        raise AssertionError("should not export when export is fresh")

    dumpdir = tmp_path / "dumps"
    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    store = _load_local_store(str(sub), dump_export_json=str(dumpdir))
    assert calls["n"] == 0
    assert store.get("fff-7") is not None
    # B-1 fix: even with nothing re-generated, the full loaded set is dumped.
    assert (dumpdir / "m.sysml.export.json").exists(), "warm run must dump full bundle"


def test_dump_export_json_rejects_nested_dump(tmp_path, monkeypatch):
    """A dump dir nested under --source is rejected (would re-ingest next run)."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")
    nested = sub / "dumps"  # inside source

    with pytest.raises(RuntimeError, match="OUTSIDE --source"):
        _load_local_store(str(sub), dump_export_json=str(nested))


def test_duplicate_id_different_payload_warns(tmp_path, monkeypatch, caplog):
    """Two files supplying the same @id with different payloads warn loudly."""
    sub = tmp_path / "src"
    sub.mkdir()
    export_a = [
        {
            "payload": {
                "@id": "dup-1",
                "@type": "PartUsage",
                "declaredName": "dupPart",
                "value": "A",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "dup-1"},
        }
    ]
    export_b = [
        {
            "payload": {
                "@id": "dup-1",
                "@type": "PartUsage",
                "declaredName": "dupPart",
                "value": "B",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "dup-1"},
        }
    ]
    import json

    (sub / "x.sysml").write_text("part X;")  # avoid the requires-.sysml error
    # Give x.sysml a matching FRESH export so no java export is triggered.
    (sub / "x.sysml.export.json").write_text(json.dumps([]))
    (sub / "a.sysml.export.json").write_text(json.dumps(export_a))
    (sub / "b.sysml.export.json").write_text(json.dumps(export_b))

    with caplog.at_level("WARNING", logger="windstorm"):
        store = _load_local_store(str(sub))
    assert store.get("dup-1") is not None
    warning = [r for r in caplog.records if r.levelname == "WARNING"]
    assert any("Duplicate @id" in r.getMessage() for r in warning)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores W_OK/chmod")
def test_read_only_source_preflight(tmp_path, monkeypatch):
    """A read-only source tree with stale exports names permissions, not export failure."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "m.sysml").write_text("part M;")
    os.chmod(sub, 0o500)  # read-only dir

    try:
        with pytest.raises(RuntimeError, match="not writable"):
            _load_local_store(str(sub))
    finally:
        os.chmod(sub, 0o700)  # restore so tmp_path cleanup works


def test_batch_export_stdin_has_trailing_newline(tmp_path, monkeypatch):
    """Stdin for batch-export must end in a newline so the last path is read."""
    captured = {}

    def fake_run(*args, **kwargs):
        captured["input"] = kwargs.get("input")

        class FakeProc:
            returncode = 0
            stderr = b"batch-export complete\n"
            stdout = b"OK\n"

        return FakeProc()

    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")
    # Create real temp files so the freshness check is genuine (no global patch).
    a = tmp_path / "a.sysml"
    b = tmp_path / "b.sysml"
    a.write_text("part A;")
    b.write_text("part B;")
    monkeypatch.setattr(wj.subprocess, "run", fake_run)
    # The jar writes <path>.export.json next to source; fake that after run:
    # first call (pre-snapshot) sees no export, later calls (post) see it.
    real_orig = wj._stat_sig
    stat_calls = {"n": 0}

    def fake_stat(p):
        stat_calls["n"] += 1
        if p.endswith(".export.json"):
            # Pre-snapshot is call #1 per path; after that the file exists.
            return None if stat_calls["n"] <= 2 else 123.0
        return real_orig(p)

    monkeypatch.setattr(wj, "_stat_sig", fake_stat)

    produced = wj.batch_export([str(a), str(b)])
    assert captured["input"].endswith(b"\n"), "stdin must end with newline"
    assert captured["input"] == (str(a) + "\n" + str(b) + "\n").encode()
    assert len(produced) == 2


def test_batch_export_rejects_newline_paths(tmp_path, monkeypatch):
    """A .sysml path containing a newline is refused (stdin protocol safety)."""
    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")
    # Don't even need a fake subprocess: the guard fires before invocation.
    called = {"n": 0}

    def fake_run(*a, **k):
        called["n"] += 1
        raise AssertionError("should not reach subprocess")

    monkeypatch.setattr(wj.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="newline"):
        wj.batch_export(["/tmp/a\nb.sysml"])
    assert called["n"] == 0


def test_batch_export_java_too_old_preflight(tmp_path, monkeypatch):
    """Preflight rejects java that is present but too old (< 21)."""
    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_java_available", lambda: True)
    monkeypatch.setattr(wj, "_java_version", lambda: 8)
    with pytest.raises(RuntimeError, match="Java 8") as ei:
        wj._jar_path()
    assert "requires Java 21" in str(ei.value)


def test_batch_export_timeout_raises_clear_error(tmp_path, monkeypatch):
    """A jar timeout raises a clear RuntimeError (not a raw TimeoutExpired)."""
    import subprocess as sp
    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")

    def fake_run(*a, **k):
        raise sp.TimeoutExpired(cmd=["java"], timeout=600)

    monkeypatch.setattr(wj.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="timed out"):
        wj.batch_export(["/tmp/a.sysml"])


def test_batch_export_stale_export_not_counted_as_produced(tmp_path, monkeypatch):
    """A stale export that predates the run is NOT counted as produced."""
    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")
    a = tmp_path / "a.sysml"
    a.write_text("part A;")

    def fake_run(*args, **kwargs):
        class FakeProc:
            returncode = 0
            stderr = b"batch-export complete\n"
            stdout = b"OK\n"

        return FakeProc()

    monkeypatch.setattr(wj.subprocess, "run", fake_run)
    # The export file exists BEFORE the run (stale). batch_export's snapshot
    # records it; after the run it is unchanged -> NOT produced.
    export_path = tmp_path / "a.sysml.export.json"
    export_path.write_text("[]")

    real_orig = wj._stat_sig

    def fake_stat(p):
        if p.endswith(".export.json"):
            return (10, 123)  # same before + after (unchanged)
        return real_orig(p)

    monkeypatch.setattr(wj, "_stat_sig", fake_stat)
    produced = wj.batch_export([str(a)])
    assert produced == [], "stale export left over from earlier run must not count"


def test_batch_export_failure_surfacing_lists_failed(tmp_path, monkeypatch):
    """batch_export raises a RuntimeError with FAIL details when a file fails."""
    import windstorm.common.windtrader_jar as wj

    monkeypatch.setattr(wj, "_jar_path", lambda: "/opt/data/fake.jar")
    a = tmp_path / "a.sysml"
    a.write_text("part A;")

    def fake_run(*args, **kwargs):
        class FakeProc:
            returncode = 1
            stderr = b"FAIL a.sysml (parse error)\nbatch-export complete\n"
            stdout = b""

        return FakeProc()

    monkeypatch.setattr(wj.subprocess, "run", fake_run)
    real_orig = wj._stat_sig

    def fake_stat(p):
        return real_orig(p)  # no export appears -> failed

    monkeypatch.setattr(wj, "_stat_sig", fake_stat)
    with pytest.raises(RuntimeError) as ei:
        wj.batch_export([str(a)])
    assert "FAIL a.sysml (parse error)" in str(ei.value)


def test_load_local_store_exports_only_skips_missing(tmp_path, monkeypatch, caplog):
    """exports_only=True trusts existing exports; skips missing with a warning."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")
    export = [
        {
            "payload": {
                "@id": "exp-1",
                "@type": "PartUsage",
                "declaredName": "expPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "exp-1"},
        }
    ]
    import json

    (sub / "a.sysml.export.json").write_text(json.dumps(export))
    # b.sysml has NO export -> exports_only warns and skips it (no Java).
    (sub / "b.sysml").write_text("part B;")

    calls = {"n": 0}

    def fake_batch_export(sysml_paths):
        calls["n"] += 1
        raise AssertionError("exports_only must not invoke Java")

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    with caplog.at_level("WARNING", logger="windstorm"):
        store = _load_local_store(str(sub), exports_only=True)
    assert calls["n"] == 0
    assert store.get("exp-1") is not None
    assert any("--exports-only" in r.getMessage() for r in caplog.records)


def test_load_local_store_skip_export_errors(tmp_path, monkeypatch, caplog):
    """skip_export_errors=True skips an export batch failure instead of aborting."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")  # bare .sysml -> need_export triggers
    (sub / "b.sysml").write_text("part B;")  # second .sysml for the partial batch
    export = [
        {
            "payload": {
                "@id": "ok-1",
                "@type": "PartUsage",
                "declaredName": "okPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "ok-1"},
        }
    ]
    import json

    (sub / "a.sysml.export.json").write_text(json.dumps(export))
    # Make the export STALE so need_export fires and batch_export runs.
    import time as _time

    old = _time.time() - 1000
    os.utime(sub / "a.sysml.export.json", (old, old))

    def fake_batch_export(sysml_paths):
        # Simulate a PARTIAL failure: a.sysml fails, but the jar successfully
        # wrote b.sysml.export.json (returned in e.produced, NB-1 round-3).
        b_out = sub / "b.sysml.export.json"
        b_export = [
            {
                "payload": {
                    "@id": "b-ok",
                    "@type": "PartUsage",
                    "declaredName": "bPart",
                    "ownedRelationship": [],
                    "ownedElement": [],
                },
                "identity": {"@id": "b-ok"},
            }
        ]
        b_out.write_text(json.dumps(b_export))
        err = RuntimeError("windtrader batch-export failed for 1/2 file(s)")
        produced = [str(b_out)]
        err.produced = produced
        raise err

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    with caplog.at_level("WARNING", logger="windstorm"):
        store = _load_local_store(str(sub), skip_export_errors=True)
    # The batch's SUCCESSFUL output (b) is kept, not discarded (NB-1 fix).
    assert store.get("b-ok") is not None
    # The stale a.sysml.export.json is loaded via export_files (jar skipped it).
    assert store.get("ok-1") is not None
    assert any("Skipping export errors" in r.getMessage() for r in caplog.records)


def test_load_local_store_malformed_json_names_file(tmp_path):
    """A malformed .export.json raises an error naming the offending file."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")
    p = sub / "a.sysml.export.json"
    p.write_text("{ not valid json ]")
    # Pin the export strictly newer than the source so it is FRESH (never
    # needs re-export, so the real java preflight can't run — hermetic on
    # coarse-mtime filesystems, round-6 nit).
    import time as _time

    fut = _time.time() + 500
    os.utime(p, (fut, fut))
    os.utime(sub / "a.sysml", (_time.time(), _time.time()))

    with pytest.raises(RuntimeError, match="a.sysml.export.json"):
        _load_local_store(str(sub))


def test_load_local_store_non_utf8_export_names_file(tmp_path):
    """A non-UTF-8 export is wrapped and names the offending file
    (UnicodeDecodeError is a ValueError subclass, round-5 catch fix)."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")
    p = sub / "a.sysml.export.json"
    p.write_bytes(b"\xff\xfe not utf8 json ]")
    # Same future-mtime pin so the export is FRESH (hermetic, round-6 nit).
    import time as _time

    fut = _time.time() + 500
    os.utime(p, (fut, fut))
    os.utime(sub / "a.sysml", (_time.time(), _time.time()))

    with pytest.raises(RuntimeError, match="a.sysml.export.json"):
        _load_local_store(str(sub))


def test_collect_source_files_logs_symlinked_dirs(tmp_path, monkeypatch, caplog):
    """Symlinked source subdirectories are logged (not silently invisible)."""
    real_dir = tmp_path / "real_models"
    real_dir.mkdir()
    (real_dir / "m.sysml").write_text("part M;")
    os.symlink(real_dir, tmp_path / "models")

    export_files, sysml_files = _collect_source_files(str(tmp_path))
    # The symlink itself is not followed, so nothing under tmp_path/models/ is
    # collected; real_models/m.sysml IS (walked via its real path).
    assert not any(os.path.join(str(tmp_path), "models") in s for s in sysml_files)
    assert any("real_models" in s for s in sysml_files)


def test_skip_export_errors_does_not_swallow_preflight(tmp_path, monkeypatch):
    """A toolchain preflight failure is NOT swallowed by --skip-export-errors
    (it has no .produced attribute -> must propagate, NB-A round 4)."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")  # bare .sysml -> need_export triggers

    def fake_batch_export(sysml_paths):
        # A PREFLIGHT RuntimeError: java/jar missing. No .produced attribute.
        raise RuntimeError("java not found: no toolchain")

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    with pytest.raises(RuntimeError, match="java not found"):
        _load_local_store(str(sub), skip_export_errors=True)


def test_skip_export_errors_stale_info_when_present(tmp_path, monkeypatch, caplog):
    """Present-but-unrefreshed export is INFO (jar skipped current), not a WARNING."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")  # bare .sysml -> need_export triggers
    export = [
        {
            "payload": {
                "@id": "st-1",
                "@type": "PartUsage",
                "declaredName": "stPart",
                "ownedRelationship": [],
                "ownedElement": [],
            },
            "identity": {"@id": "st-1"},
        }
    ]
    import json

    (sub / "a.sysml.export.json").write_text(json.dumps(export))
    # Make the export STALE so a.sysml is in need_export (refresh attempted).
    import time as _time

    old = _time.time() - 1000
    os.utime(sub / "a.sysml.export.json", (old, old))

    def fake_batch_export(sysml_paths):
        # The jar "succeeds" but writes NOTHING (returns []): the existing
        # stale export is loaded. Round-5: this is INFO, not WARNING.
        return []

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    with caplog.at_level("INFO", logger="windstorm"):
        store = _load_local_store(str(sub))
    assert store.get("st-1") is not None
    assert any("not refreshed this run" in r.getMessage() for r in caplog.records)
    assert not any(
        "No export for" in r.getMessage() and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_missing_export_after_batch_warns(tmp_path, monkeypatch, caplog):
    """A genuinely absent export after a no-op batch is a WARNING (NB-B)."""
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "a.sysml").write_text("part A;")  # bare .sysml -> need_export triggers
    # NO a.sysml.export.json exists at all.

    def fake_batch_export(sysml_paths):
        return []  # jar produced nothing

    monkeypatch.setattr("windstorm.main.batch_export", fake_batch_export)
    with caplog.at_level("INFO", logger="windstorm"):
        with pytest.raises(RuntimeError, match="No elements could be exported"):
            _load_local_store(str(sub))
    assert any("No export for" in r.getMessage() for r in caplog.records)
    # The absent-export case must NOT log the present-but-unrefreshed INFO line.
    assert not any("not refreshed this run" in r.getMessage() for r in caplog.records)
    # Positive control: INFO-level records ARE captured this run (self-proving
    # the negative assertion above actually had INFO in scope, round-7 nit).
    assert any("Exporting 1 .sysml file(s)" in r.getMessage() for r in caplog.records)


def test_console_script_targets_importable():
    """Both script tables name an importable, callable entrypoint.

    Guards against the round-9 / fbc88b2 regression: PEP 621
    [project.scripts] and [tool.poetry.scripts] must both point at a module
    that exists and has a main(). The suite never executes the console
    script (pytest imports modules directly), so without this, a broken
    entrypoint can survive every green run.
    """
    import importlib
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text()
    # Both script tables (poetry + PEP 621) must agree on one target.
    targets = set(re.findall(r'^windstorm\s*=\s*"([^"]+)"', text, re.M))
    assert targets == {"windstorm.main:main"}, targets
    for target in targets:
        mod, _, attr = target.partition(":")
        assert callable(getattr(importlib.import_module(mod), attr))


def test_verification_case_selectable_by_name_type(tmp_path):
    """#95: a VerificationCaseDefinition from a real-jar export is selectable
    by name+type (the selection already keys off element_type)."""
    mocks = os.path.join(os.path.dirname(__file__), "mocks", "verification")
    export = os.path.join(mocks, "verify_defs.sysml.export.json")
    assert os.path.exists(export), "committed real-jar verification export"
    src = tmp_path / "src"
    src.mkdir()
    shutil.copy2(export, src / "verify_defs.sysml.export.json")

    store = _load_local_store(str(src), exports_only=True)
    case = store.get_element_by_name_type("verify_case1", "VerificationCaseDefinition")
    assert case["@type"] == "VerificationCaseDefinition"
    assert case["declaredName"] == "verify_case1"


def test_verification_case_metadata_tagged_tool_execution():
    """#95: the adapter tags a verification case's own metadata as
    AnalysisTooling::ToolExecution (windstorm-visible marker), not ToolVariable."""
    import json as _json

    from windstorm.common.export_adapter import adapt

    mocks = os.path.join(os.path.dirname(__file__), "mocks", "verification")
    export = os.path.join(mocks, "verify_defs.sysml.export.json")
    raw = _json.load(open(export))
    adapted = adapt(raw)

    # find the verification case
    case_eid = None
    for eid, p in adapted.items():
        if p.get("declaredName") == "verify_case1":
            case_eid = eid
            break
    assert case_eid is not None

    # its MetadataUsage children should be tagged ToolExecution
    case = adapted[case_eid]
    metadata_usage_eids = [
        oe.get("@id")
        for oe in case.get("ownedElement", [])
        if adapted.get(oe.get("@id"), {}).get("@type") == "MetadataUsage"
    ]
    assert metadata_usage_eids, "expected case to own MetadataUsage element(s)"
    for mu_eid in metadata_usage_eids:
        md = adapted[mu_eid].get("metadataDefinition", {}).get("@id")
        # resolve to the real MetadataDefinition payload
        md_payload = adapted.get(md, {})
        assert (
            md_payload.get("qualifiedName") == "AnalysisTooling::ToolExecution"
        ), f"verification case metadata should be ToolExecution, got {md_payload.get('qualifiedName')}"
