#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""windstorm — SysML 2.0 templating (Westfall-io/windstorm)."""

from importlib import metadata

try:
    __version__ = metadata.version("sysml-windstorm")
except metadata.PackageNotFoundError:  # pragma: no cover - dev checkout fallback
    __version__ = "0.0.0.dev0"
