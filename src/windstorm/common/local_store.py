"""Local (offline) element store: serves API-shaped elements from memory.

windstorm's templating core (`init_variables`, `handle_feature_chain`, ...)
looks up every element through `get_element_by_id(api, project, eid)` and
`query_for_element(api, project, q)` in this module. Those functions are the
single seam where a live SysMLv2 API is assumed.

This module provides an in-memory ``ElementStore`` that the same core
functions can talk to, so windstorm can run from local ``.sysml`` / export
JSON files with **no API address and no network**. The store is filled from
:mod:`windstorm.common.export_adapter` output (API-shaped payloads keyed by
``@id``).

The store object intentionally quacks like the ``(api, project)`` pair the
core passes around: it exposes ``@id``, ``name``, ``declaredName`` on itself
so existing logging that reads ``project["name"]`` / ``project["@id"]``
keeps working.
"""

from __future__ import annotations

import logging
from typing import Any

from windstorm.common.errors import WindstormLookupError

logger = logging.getLogger("windstorm.common.api")


class ElementStore:
    """In-memory API-shaped element graph served by @id / name / query."""

    def __init__(self, elements: dict[str, dict] | None = None):
        # @id -> API-shaped payload (exactly what adapt() returns).
        self._elements: dict[str, dict] = dict(elements or {})
        # Project-lookalike so verify_tool-style logging reads project["name"]
        # / project["@id"]. Kept as instance attributes (NOT in _elements) so
        # the element graph stays purely @id -> payload.
        self._meta = {
            "@id": "local",
            "@type": "Project",
            "name": "local",
            "declaredName": "local",
        }

    def __getitem__(self, key: str) -> Any:
        if key in self._meta:
            return self._meta[key]
        return self._elements[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._meta:
            self._meta[key] = value
        else:
            self._elements[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._meta or key in self._elements

    def __len__(self) -> int:
        return len(self._elements)

    def add(self, eid: str, payload: dict) -> None:
        self._elements[eid] = payload

    def extend(self, elements: dict[str, dict]) -> None:
        self._elements.update(elements)

    def get(self, eid: str, default: Any = None) -> Any:
        return self._elements.get(eid, default)

    def get_element_by_id(self, eid: str) -> dict:
        try:
            return self._elements[eid]
        except KeyError:
            logger.error("Element not found in local store: {}".format(eid))
            raise WindstormLookupError(eid) from None

    def get_element_by_name_type(self, element_name: str, element_type: str) -> dict:
        """Find an element by (declaredName, @type) — mirrors the API query."""
        matches = []
        for payload in self._elements.values():
            if (
                payload.get("declaredName") == element_name
                and payload.get("@type") == element_type
            ):
                matches.append(payload)
        if len(matches) == 1:
            return matches[0]
        if len(matches) == 0:
            logger.error(
                "Failed to find {} named {} in local store.".format(
                    element_type, element_name
                )
            )
            raise WindstormLookupError(
                "No {} named {} in local store".format(element_type, element_name)
            ) from None
        logger.error(
            "Found {} matches for {} named {}; expected 1.".format(
                len(matches), element_type, element_name
            )
        )
        raise WindstormLookupError(
            "{} matches for {} named {}".format(
                len(matches), element_type, element_name
            )
        ) from None

    def query(self, base_query: dict) -> list[dict]:
        """Best-effort query resolver for the queries windstorm actually sends.

        Supports the shapes built by :func:`build_query`:
        - PrimitiveConstraint on ``@id`` (returns that one element)
        - CompositeConstraint on (``@type``, ``declaredName``) equality
        """
        where = base_query.get("where", {})
        if where.get("@type") == "PrimitiveConstraint":
            prop = where.get("property")
            val = where.get("value")
            if prop == "@id":
                try:
                    return [self._elements[val]]
                except KeyError:
                    return []
            # fall through to generic matching below
        if where.get("@type") == "CompositeConstraint":
            props = []
            vals = []
            for c in where.get("constraint", []):
                props.append(c.get("property"))
                vals.append(c.get("value"))
            if set(props) == {"@type", "declaredName"}:
                t = vals[props.index("@type")]
                dn = vals[props.index("declaredName")]
                out = []
                for payload in self._elements.values():
                    if payload.get("@type") == t and payload.get("declaredName") == dn:
                        out.append(payload)
                return out
        # Generic fallback: match all where constraints.
        out = []
        for payload in self._elements.values():
            ok = True
            for c in _flatten_constraints(where):
                if payload.get(c.get("property")) != c.get("value"):
                    ok = False
                    break
            if ok:
                out.append(payload)
        return out

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return "ElementStore({} elements)".format(len(self._elements))


def _flatten_constraints(where: dict):
    if where.get("@type") == "PrimitiveConstraint":
        yield where
    elif where.get("@type") == "CompositeConstraint":
        for c in where.get("constraint", []):
            yield from _flatten_constraints(c)
