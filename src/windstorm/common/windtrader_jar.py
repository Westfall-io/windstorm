"""Real windtrader-java batch-export integration (single JVM, writes next to source)."""

import logging
import os
import subprocess

logger = logging.getLogger("windstorm")

WINDTRADER_REPO_URL = "https://github.com/Westfall-io/windtrader-java"


def _jar_path() -> str:
    """Resolve the WINDTRADER_JAR path, raising a clear preflight error if unset."""
    if not _java_available():
        raise RuntimeError(
            "Offline .sysml export requires a Java 21 runtime on PATH.\n"
            "  Install a JDK 21 (e.g. Temurin) or point PATH at one, then retry.\n"
            "  JAR to run with: {} ".format(_jar_candidate())
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


def _jar_candidate() -> str:
    return os.environ.get("WINDTRADER_JAR", "windtrader-java.jar")


def _java_available() -> bool:
    from shutil import which

    return which("java") is not None


def batch_export(sysml_paths):
    """Run windtrader-java batch-export over all .sysml paths in ONE JVM invocation.

    The jar reads newline-separated .sysml paths on stdin and writes
    ``<path>.export.json`` next to each source file. Returns the list of
    generated export paths.
    """
    jar = _jar_path()
    cmd = ["java", "-jar", jar, "batch-export"]
    logger.info("Running: {}".format(" ".join(cmd)))
    # Trailing newline so every path (incl. the last) is a complete stdin line —
    # the batch-export reader relies on newline-delimited lines.
    stdin_data = "\n".join(sysml_paths) + "\n"
    proc = subprocess.run(
        cmd,
        input=stdin_data.encode(),
        capture_output=True,
        timeout=600,
    )
    # The jar writes <path>.export.json next to each source on success.
    produced = []
    failed = []
    for path in sysml_paths:
        out = path + ".export.json"
        if os.path.exists(out):
            produced.append(out)
        else:
            failed.append(path)

    stderr = proc.stderr.decode(errors="replace")
    if proc.returncode != 0 or failed:
        # Surface every per-file failure line the jar reported.
        fail_lines = [l for l in stderr.splitlines() if l.startswith("FAIL ")]
        detail = "\n".join(fail_lines) if fail_lines else stderr.strip()[-500:]
        raise RuntimeError(
            "windtrader batch-export failed for {}/{} file(s).\n"
            "  JAR: {}\n"
            "{}\n"
            "  Re-run with --debug for full output.".format(
                len(failed), len(sysml_paths), jar, detail
            )
        )
    return produced
