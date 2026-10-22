"""Real windtrader-java batch-export integration (single JVM, writes next to source)."""

import logging
import os
import re
import subprocess
from shutil import which

logger = logging.getLogger("windstorm")

WINDTRADER_REPO_URL = "https://github.com/Westfall-io/windtrader-java"
MIN_JAVA_MAJOR = 21
_JAVA_VERSION_RE = re.compile(r'version "(\d+)(?:\.(\d+))?')


def _java_version() -> int:
    """Return the detected java major version, or 0 if it cannot be determined."""
    try:
        proc = subprocess.run(["java", "-version"], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    text = proc.stderr.decode(errors="replace") + proc.stdout.decode(errors="replace")
    m = _JAVA_VERSION_RE.search(text)
    if not m:
        return 0
    major = int(m.group(1))
    if major == 1:  # Java 8 reports "1.8.0_..."
        return int(m.group(2) or 0)
    return major


def _java_available() -> bool:
    return which("java") is not None


def _jar_path() -> str:
    """Resolve the WINDTRADER_JAR path, raising a clear preflight error if unusable."""
    if not _java_available():
        raise RuntimeError(
            "Offline .sysml export requires a Java {} runtime on PATH but `java` "
            "was not found.\n"
            "  Install a JDK {} (e.g. Temurin) or point PATH at one, then retry.".format(
                MIN_JAVA_MAJOR, MIN_JAVA_MAJOR
            )
        )
    detected = _java_version()
    if detected and detected < MIN_JAVA_MAJOR:
        raise RuntimeError(
            "Offline .sysml export requires Java {} but found Java {} on PATH.\n"
            "  Install a JDK {} (e.g. Temurin) or point PATH at one, then retry.".format(
                MIN_JAVA_MAJOR, detected, MIN_JAVA_MAJOR
            )
        )
    jar = os.environ.get("WINDTRADER_JAR", "")
    if not jar:
        raise RuntimeError(
            "Offline .sysml export requires the windtrader-java JAR.\n"
            "  Set the WINDTRADER_JAR environment variable to the jar path.\n"
            "  Obtain it from: {} (release asset, e.g. windtrader-java-0.1.0.jar).".format(
                WINDTRADER_REPO_URL
            )
        )
    if not os.path.isfile(jar):
        raise RuntimeError(
            "WINDTRADER_JAR points to a missing file: {}\n"
            "  Download the jar from {} and set WINDTRADER_JAR to its path.".format(
                jar, WINDTRADER_REPO_URL
            )
        )
    return jar


def _stat_sig(path):
    """Return a signature of ``path`` or None if it does not exist.

    Uses (size, mtime_ns) so that a rewrite landing in the same filesystem
    timestamp tick is still detected, and so a file the jar intentionally
    skips (already current) is not misreported as a failure.
    """
    try:
        st = os.stat(path)
        return (st.st_size, st.st_mtime_ns)
    except OSError:
        return None


def _assert_no_newlines(sysml_paths):
    """Reject paths containing newlines before they hit the newline-delimited stdin."""
    for p in sysml_paths:
        if "\n" in p or "\r" in p:
            raise ValueError(
                "Refusing to export a .sysml path containing a newline "
                "character (would break the batch-export stdin protocol): {!r}".format(
                    p
                )
            )


def batch_export(sysml_paths):
    """Run windtrader-java batch-export over all .sysml paths in ONE JVM invocation.

    The jar reads newline-separated .sysml paths on stdin and writes
    ``<path>.export.json`` next to each source file. Returns the list of
    export paths actually written (fresh for this run). A stale export left
    over from an earlier run is NOT counted as produced.
    """
    sysml_paths = list(sysml_paths)
    _assert_no_newlines(sysml_paths)
    jar = _jar_path()
    # -Dfile.encoding=UTF-8: paths are sent as UTF-8 on stdin; a Windows JVM
    # defaulting to windows-1252 would mis-decode non-ASCII model paths.
    cmd = ["java", "-Dfile.encoding=UTF-8", "-jar", jar, "batch-export"]
    logger.info("Running: %s", " ".join(cmd))
    logger.debug("batch-export paths: %r", sysml_paths)

    # Snapshot expected-output state BEFORE the run so stale files from a
    # previous (possibly crashed) run can't be mistaken for fresh output.
    before = {p: _stat_sig(p + ".export.json") for p in sysml_paths}
    # Trailing newline so every path (incl. the last) is a complete stdin line —
    # the batch-export reader relies on newline-delimited lines.
    stdin_data = "\n".join(sysml_paths) + "\n"
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_data.encode(),
            capture_output=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired as e:
        # subprocess.TimeoutExpired carries any output captured before the
        # timeout — log it, because "see --debug" would otherwise point at
        # nothing on this path (the post-run logging below is unreachable).
        partial_out = (e.stdout or b"").decode(errors="replace")
        partial_err = (e.stderr or b"").decode(errors="replace")
        if partial_out:
            logger.debug("batch-export partial stdout before timeout:\n%s", partial_out)
        if partial_err:
            logger.debug("batch-export partial stderr before timeout:\n%s", partial_err)
        raise RuntimeError(
            "windtrader batch-export timed out after 600s while exporting "
            "{} file(s).\n"
            "  JAR: {}\n"
            "  Outputs written before timeout are treated as stale (see --debug).".format(
                len(sysml_paths), jar
            )
        ) from e
    except OSError as e:
        raise RuntimeError(
            "Failed to run the windtrader-java JAR: {}\n"
            "  JAR: {}\n"
            "  (java may have vanished between preflight and run)".format(e, jar)
        ) from e

    stderr = proc.stderr.decode(errors="replace")
    logger.debug("batch-export stdout:\n%s", proc.stdout.decode(errors="replace"))
    logger.debug("batch-export stderr:\n%s", stderr)

    # The jar writes <path>.export.json next to each source on success. Only
    # count as produced files that exist now AND changed (or appeared) this
    # run. A file that exists but is UNCHANGED is not a failure — the jar
    # considered it already current (NB-5); only a MISSING output after a
    # successful run is a real failure.
    produced = []
    missing = []
    for path in sysml_paths:
        out = path + ".export.json"
        sig = _stat_sig(out)
        if sig is not None and sig != before[path]:
            produced.append(out)
        elif sig is None:
            missing.append(path)

    if proc.returncode != 0 or missing:
        fail_lines = [line for line in stderr.splitlines() if line.startswith("FAIL ")]
        detail = "\n".join(fail_lines) if fail_lines else stderr.strip()[-500:]
        if not missing:
            message = (
                "windtrader jar batch-export exited with status {} but all "
                "expected outputs are present.".format(proc.returncode)
            )
        else:
            message = "windtrader batch-export failed for {}/{} file(s).".format(
                len(missing), len(sysml_paths)
            )
        err = RuntimeError(
            "{}\n"
            "  JAR: {}\n"
            "{}\n"
            "  Re-run with --debug for full output.".format(message, jar, detail)
        )
        # Attach the outputs that DID succeed so a caller handling partial
        # failure (--skip-export-errors) can still load them instead of
        # discarding the successful part of the batch.
        err.produced = produced  # type: ignore[attr-defined]
        raise err
    return produced
