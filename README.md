# windstorm

SysML 2.0 Analysis Toolset — model-driven templating for any text-based file.

[![PyPI version](https://badge.fury.io/py/sysml-windstorm.svg)](https://badge.fury.io/py/sysml-windstorm)
[![PyPI status](https://img.shields.io/pypi/status/sysml-windstorm.svg)](https://pypi.python.org/pypi/sysml-windstorm/)
[![Coverage Status](https://coveralls.io/repos/github/Westfall-io/windstorm/badge.svg)](https://coveralls.io/github/Westfall-io/windstorm)
![Docstring Coverage](https://raw.githubusercontent.com/Westfall-io/windstorm/main/doc-cov.svg)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

---

## Overview

**windstorm** reads a SysML v2 analysis model — either from a live
[SysMLv2 API](https://github.com/Systems-Modeling/SysML-v2-API-Services)
or from **local `.sysml` files** — and turns the model's parameter values
into variables you can use inside any text-based template.

It extends [Jinja2](https://jinja.palletsprojects.com) with a custom
`windstorm(...)` function, so anything Jinja can render (files, code,
config, Excel workbooks) can be driven from your SysML model.

---

## Installation

```bash
pip install sysml-windstorm
```

Requires Python 3.9+.

---

## Quick start

Point windstorm at a model and render a template:

```bash
# Live API mode: pull parameters from a SysMLv2 API
windstorm -a http://your_api_address:9000 -p project_uuid element_name

# Local-file mode: use a directory of .sysml files (or exported JSON) instead
windstorm --source ./models element_name
```

Inside any text file, reference model values with Jinja:

```
{{ windstorm('myVar') }}
```

Run windstorm with that file's directory as the input:

```bash
windstorm --source ./models --in_directory ./templates --out_directory ./output element_name
```

---

## Modes

### 1. Live SysMLv2 API (default)

When pointed at an appropriate SysMLv2 API, windstorm pulls all parameter
values for the requested analysis element and makes them available to the
Jinja templates.

```
windstorm -a http://your_api_address:9000 -p project_uuid element_name
```

### 2. Local files / offline (`--source`)

Since **v0.6.0**, windstorm can read a model entirely from local files —
no API address and no network required:

```
windstorm --source ./models element_name
```

`--source DIR` accepts a directory that may contain **both**:

- **Raw `.sysml` files** — windstorm runs the
  [windtrader-java](https://github.com/Westfall-io/windtrader-java)
  `batch-export` CLI (Java 21+) to produce the export JSON next to each
  source, then loads it. Set the jar location with the `WINDTRADER_JAR`
  environment variable.
- **Already-exported JSON** (`*.export.json`) — loaded directly, no Java
  needed. This is the fastest path and is fully offline.

The two are **complementary**: a `.sysml` whose export is missing or older
than the source is (re-)exported; an up-to-date export is reused. Mixing
both in one tree is fine.

All files build an in-memory element store (the same API-shaped graph
windstorm uses in live mode), so templating behaves identically.

> **Note:** `--source` is deterministic *given a stable set of exports*.
> The jar writes `<path>.export.json` **next to each source** (the tree must
> be writable), and re-export happens only when an export is missing or
> older than its `.sysml`. `--dump-export-json DIR` (must be **outside**
> `--source`) copies the full export bundle to a directory you can reuse as
> a Java-free `--source` on later runs.

---

## Templating

Any text-based file (`.json`, `.py`, `.txt`, `.m`, ...) can be templated
with Jinja. Versions after 0.4.0 also support **Excel files**, even though
they are not pure text.

windstorm supports all Jinja features (for loops, if statements, filters,
etc.) and adds the custom `windstorm()` function to resolve a model value
by tool-variable name.

Example template (`template.txt`):

```
{{ windstorm('deltaT') }}
```

Example with a loop:

```
{% for w in windstorm('weights') %}{{ w }}{% if not loop.last %},{% endif %}{% endfor %}
```

Run windstorm with `--in_directory` (template folder) and `--out_directory`
(rendered output):

```bash
windstorm -a http://your_api_address:9000 -p project_uuid \
  --in_directory ./templates --out_directory ./output \
  element_name
```

---

## CLI reference

```
windstorm [element_name] [options]

Options:
  -a, --api URL              SysMLv2 API address (default: http://sysml2-dev.intercax.com:9000)
  -p, --project_id UUID      Specific project UUID (default: latest project)
  --source DIR               Read from local .sysml / .export.json files instead of an API
  --dump-export-json DIR     Copy the full export bundle to DIR (must be outside --source)
  -t, --element_type TYPE    Analysis element type (default: AnalysisCaseDefinition)
  --in_directory DIR         Template input directory (default: .)
  --out_directory DIR        Rendered output directory (default: .)
  --insecure                 Disable TLS verification
  --debug                    Enable debug logging
  --force_render_error_continue  Keep rendering sibling files after an error
```

---

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests
```

The test suite uses **committed mocks** (API-shaped JSON under
`tests/mocks/`) — no live API or Jupyter kernel required. To regenerate
the mocks from the `.sysml` fixtures, run:

```bash
python ./tests/mocks/make_mocks.py
```

(Requires a SysML Jupyter kernel; CI does not do this — the committed
mocks are authoritative for tests.)

### Release

Releases are automated by the GitHub Release Workflow on every push to
`main`:

1. Tests + coverage must pass.
2. `python-semantic-release` parses commit messages (emoji parser) to
   decide the next version:
   - `:boom:` → major bump
   - `:sparkles:` (and friends) → minor bump
   - `:bug:`, `:ambulance:`, etc. → patch bump
3. On a release, the package is published to **PyPI** and a **GitHub
   Release** is created.

---

## License

MIT
