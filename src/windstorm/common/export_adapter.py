"""Adapter from windtrader-java export JSON to the SysMLv2 API query-result shape.

windtrader-java's `export` mode emits the pilot's raw EMF relationship graph:
a flat list of ``{payload, identity}`` elements where children are reached via
``ownedRelationship`` memberships, and relationship elements (``OwningMembership``,
``FeatureMembership``, ``FeatureTyping``, ...) live as their own top-level entries.

windstorm's templating core (`verify_tool` / `init_variables` in
``windstorm.common.api``) walks the *API query-result shape*: elements carry
``ownedAction`` / ``ownedElement`` / ``metadataDefinition`` / ``value`` /
``qualifiedName`` directly on the payload.

This module converts the export graph into the API shape, so offline source
(raw ``.sysml`` -> export JSON) drives the same templating path as a live API.

Conversion rules (per design review on windstorm#88):
- Build an ``@id`` -> element index first; relationships are separate top-level elements.
- Never assume ``target`` is populated; prefer ``memberElement`` (memberships) and
  ``ownedRelatedElement`` (other relationships).
- Reconstruct ``qualifiedName`` by walking owned memberships *and* ``NamespaceImport``
  references (imported namespace -> its members).
- Literal ``value`` is on the leaf; rebuild feature chains via
  ``FeatureMembership`` -> ``FeatureValue`` -> literal and
  ``FeatureTyping`` -> definition.

The adapter is a pure, dependency-free consumer. It runs in windstorm's Python
process only; the EPL-2.0 Java JAR remains an external black-box behind the
``windtrader`` wrapper.
"""

from __future__ import annotations

from typing import Any

# Relationship @types that carry an owned child / semantic member.
_MEMBERSHIP_TYPES = {
    "OwningMembership",
    "FeatureMembership",
    "SubjectMembership",
    "ParameterMembership",
    "ReturnParameterMembership",
    "Membership",
}
_IMPORT_TYPES = {"NamespaceImport"}
_TYPING_TYPES = {"FeatureTyping", "Subclassification"}
_VALUE_TYPES = {"FeatureValue"}


def _resolve(ref: Any, index: dict[str, dict]) -> dict | None:
    """Resolve a reference (``{"@id": ...}`` or list of such) via the @id index."""
    if isinstance(ref, dict) and "@id" in ref:
        return index.get(ref["@id"])
    if isinstance(ref, list):
        for r in ref:
            item = _resolve(r, index)
            if item is not None:
                return item
    return None


def _resolve_related(rel_payload: dict, index: dict[str, dict]) -> list[dict]:
    """Return the child element(s) of a relationship, using the correct field."""
    # Prefer the semantic member (membership types) or ownedRelatedElement.
    for key in ("memberElement", "ownedRelatedElement"):
        if key in rel_payload:
            val = rel_payload[key]
            if isinstance(val, dict) and val.get("@id") in index:
                return [index[val["@id"]]]
            if isinstance(val, list):
                out = []
                for r in val:
                    item = _resolve(r, index)
                    if item is not None:
                        out.append(item)
                if out:
                    return out
    # Fall back to target (often empty in this export).
    if "target" in rel_payload:
        out = _resolve(rel_payload["target"], index)
        if out is not None:
            return [out]
    return []


def _namespace_qualified_name(pkg: dict, index: dict[str, dict]) -> str:
    """Reconstruct the qualified name for a package/namespace element."""
    payload = pkg.get("payload", {})
    # Walk the owner chain collecting declared names.
    names = []
    seen = set()
    cur = pkg
    while cur is not None and cur.get("payload", {}).get("@id") not in seen:
        seen.add(cur["payload"].get("@id"))
        p = cur.get("payload", {})
        dn = p.get("declaredName")
        if dn:
            names.append(dn)
        owner_ref = p.get("owner") or p.get("owningRelatedElement")
        cur = _resolve(owner_ref, index) if owner_ref else None
    # Member names can be on the membership, but use declaredName chain.
    return "::".join(reversed(names)) if names else ""


def _collect_imported_members(pkg: dict, index: dict[str, dict]) -> dict[str, dict]:
    """For a namespace, gather members from NamespaceImport references."""
    payload = pkg.get("payload", {})
    out: dict[str, dict] = {}
    for rel_ref in payload.get("ownedRelationship", []):
        rel = _resolve(rel_ref, index)
        if rel is None:
            continue
        rp = rel.get("payload", {})
        if rp.get("@type") in _IMPORT_TYPES:
            imported = _resolve(rp.get("memberElement"), index) or _resolve(
                rp.get("importedNamespace"), index
            )
            if imported is not None:
                for child in _children_of(imported, index):
                    out[child.get("payload", {}).get("declaredName", "")] = child
    return out


def _children_of(
    elem: dict, index: dict[str, dict], key: str = "ownedElement"
) -> list[dict]:
    """Return children of an element following the API shape, with named classification."""
    payload = elem.get("payload", {})
    rels = []
    for rel_ref in payload.get("ownedRelationship", []):
        rel = _resolve(rel_ref, index)
        if rel is None:
            continue
        rp = rel.get("payload", {})
        if rp.get("@type") in _MEMBERSHIP_TYPES:
            rels.append(rel)
    children = []
    for rel in rels:
        rp = rel.get("payload", {})
        member = _resolve_related(rp, index)
        children.extend(member)
    return children


def _is_action(p: dict) -> bool:
    return "Action" in p.get("@type", "") or p.get("@type") in (
        "ActionUsage",
        "ActionDefinition",
    )


def _is_metadata(p: dict) -> bool:
    return p.get("@type") == "MetadataUsage"


def adapt(export_json: dict | list) -> dict[str, dict]:
    """Convert export JSON to the API query-result shape keyed by @id.

    Returns a dict mapping ``@id`` -> API-shaped payload (with ``ownedAction`` /
    ``ownedElement`` / ``metadataDefinition`` / ``value`` / ``qualifiedName``
    resolved where applicable).
    """
    elements = (
        export_json
        if isinstance(export_json, list)
        else export_json.get("elements", [])
    )
    index = {}
    for el in elements:
        p = el.get("payload", {})
        i = el.get("identity", {})
        eid = p.get("@id") or i.get("@id")
        if eid and eid not in index:
            index[eid] = el

    api: dict[str, dict] = {}
    # First pass: copy payloads and backfill @id from identity.
    for el in elements:
        p = el.get("payload", {})
        i = el.get("identity", {})
        eid = p.get("@id") or i.get("@id")
        if not eid:
            continue
        payload = dict(p)
        if "@id" not in payload:
            payload["@id"] = i.get("@id")
        api[eid] = payload

    # Second pass: resolve owned relationships into ownedAction / ownedElement.
    for eid, payload in api.items():
        # API-shape alias: windstorm reads `.name` for ReferenceUsage etc.
        if "name" not in payload:
            for src_key in ("declaredName", "memberName"):
                if payload.get(src_key):
                    payload["name"] = payload[src_key]
                    break

        rels = []
        for rel_ref in payload.get("ownedRelationship", []):
            rel = _resolve(rel_ref, index)
            if rel is not None:
                rels.append(rel)

        action_children = []
        element_children = []
        for rel in rels:
            rp = rel.get("payload", {})
            if rp.get("@type") in _MEMBERSHIP_TYPES:
                for child in _resolve_related(rp, index):
                    cp = child.get("payload", {})
                    if _is_action(cp):
                        action_children.append(child)
                    else:
                        element_children.append(child)
            elif rp.get("@type") == "FeatureValue":
                # FeatureValue -> literal / chain: windstorm's init_variables walks an
                # input's ownedElement and calls handle_literals/handle_feature_chain on
                # each non-metadata child, so the value element (literal or chain
                # expression) must appear in ownedElement (API shape).
                for child in _resolve_related(rp, index):
                    cp = child.get("payload", {})
                    if (
                        cp.get("@type", "").startswith("Literal")
                        or "value" in cp
                        or cp.get("@type")
                        in (
                            "FeatureChainExpression",
                            "FeatureValue",
                            "OperatorExpression",
                        )
                    ):
                        element_children.append(child)

        if action_children:
            payload["ownedAction"] = [
                {"@id": c["payload"].get("@id")} for c in action_children
            ]
        if element_children:
            payload["ownedElement"] = [
                {"@id": c["payload"].get("@id")} for c in element_children
            ]

        # Reconstruct `input` (the API shape carries it directly on the analysis): the
        # named members carried by FeatureMembership relationships (the inputs), excluding
        # the subject (SubjectMembership) and metadata (MetadataUsage).
        if not payload.get("input"):
            inputs = []
            for rel in rels:
                rp = rel.get("payload", {})
                if rp.get("@type") != "FeatureMembership":
                    continue
                for mch in _resolve_related(rp, index):
                    cp = mch.get("payload", {})
                    if cp.get("@type") == "MetadataUsage":
                        continue
                    inputs.append({"@id": cp.get("@id")})
            if inputs:
                payload["input"] = inputs

        # metadataDefinition resolution
        is_analysis = payload.get("@type") in (
            "AnalysisCaseDefinition",
            "ActionUsage",
            "ActionDefinition",
        )
        for child in element_children:
            cp = child.get("payload", {})
            if cp.get("@type") == "MetadataUsage":
                cid = cp.get("@id")
                if not (cid and cid in api):
                    continue
                meta_api = api[cid]
                # Distinguish the two metadata kinds by the owning element:
                #   - owned directly by an analysis case / action -> AnalysisTooling::ToolExecution
                #     (the analysis-tool marker; its child reference carries toolName "Windstorm")
                #   - owned by an input feature -> AnalysisTooling::ToolVariable
                #     (its child reference carries the variable's name / value, e.g. name -> "deltaT")
                if is_analysis:
                    meta_api.setdefault(
                        "metadataDefinition", {"@id": "AnalysisTooling::ToolExecution"}
                    )
                else:
                    meta_api.setdefault(
                        "metadataDefinition", {"@id": "AnalysisTooling::ToolVariable"}
                    )

                # The MetadataUsage's child reference(s): the export carries the value chain
                # (ReferenceUsage -> FeatureValue -> literal) but not the API shape windstorm
                # reads (`.name`, `ownedElement[0]` -> literal). Rebuild it.
                for mdoe in cp.get("ownedRelationship", []):
                    rel = _resolve(mdoe, index)
                    if rel is None:
                        continue
                    rp = rel.get("payload", {})
                    if rp.get("@type") in _MEMBERSHIP_TYPES:
                        for mch in _resolve_related(rp, index):
                            mcp = mch.get("payload", {})
                            if mcp.get("@type") == "ReferenceUsage":
                                ref_eid = mcp.get("@id")
                                if ref_eid and ref_eid in api:
                                    ref_api = api[ref_eid]
                                    # Find the literal value chain.
                                    lit = None
                                    lit_eid = None
                                    for ref_rel_ref in mcp.get("ownedRelationship", []):
                                        ref_rel = _resolve(ref_rel_ref, index)
                                        if ref_rel is None:
                                            continue
                                        ref_rp = ref_rel.get("payload", {})
                                        if ref_rp.get("@type") == "FeatureValue":
                                            for lr in _resolve_related(ref_rp, index):
                                                lp = lr.get("payload", {})
                                                if "value" in lp:
                                                    lit = lp["value"]
                                                    lit_eid = lp.get("@id")
                                                    # LiteralString exports its quoted content
                                                    # ("..."). windstorm compares against the bare
                                                    # string; unquote here (export untouched).
                                                    if lp.get(
                                                        "@type"
                                                    ) == "LiteralString" and isinstance(
                                                        lit, str
                                                    ):
                                                        lit = lit.strip('"')
                                    if lit_eid is not None:
                                        # ReferenceUsage.ownedElement[0] -> literal value.
                                        ref_api["ownedElement"] = [{"@id": lit_eid}]
                                    # Assign the API `name` windstorm keys on:
                                    #   - ToolExecution child reference: name == "toolName"
                                    #   - ToolVariable child reference: name == "name"
                                    lit_str = (
                                        str(lit).strip('"') if lit is not None else None
                                    )
                                    if is_analysis and lit_str == "Windstorm":
                                        ref_api["name"] = "toolName"
                                    elif not is_analysis:
                                        ref_api["name"] = "name"
                                    elif lit is not None and "name" not in ref_api:
                                        ref_api.setdefault("name", "value")

        # value propagation: walk owned children for literal values
        for child in element_children:
            cp = child.get("payload", {})
            for rel_ref in cp.get("ownedRelationship", []):
                rel = _resolve(rel_ref, index)
                if rel is None:
                    continue
                rp = rel.get("payload", {})
                if rp.get("@type") == "FeatureValue":
                    for lr in _resolve_related(rp, index):
                        lp = lr.get("payload", {})
                        if "value" in lp:
                            val = lp["value"]
                            if lp.get("@type") == "LiteralString" and isinstance(
                                val, str
                            ):
                                val = val.strip('"')
                            payload["value"] = val

    # Third pass: unquote LiteralString elements' own `value` (the export serializes
    # them quoted, but windstorm compares/renders the bare string). Export untouched.
    for eid, payload in api.items():
        if payload.get("@type") == "LiteralString" and isinstance(
            payload.get("value"), str
        ):
            payload["value"] = payload["value"].strip('"')

    # Leaf FeatureChainExpression: the pilot export sometimes collapses a literal value
    # into a FeatureChainExpression with no relationships and a `value` field. windstorm's
    # init_variables expects literals (LiteralString) for handle_literals; a bare chain
    # expression would go to handle_feature_chain and fail (no targetFeature). Adapt it
    # to a LiteralString so the value flows through. Export untouched.
    for eid, payload in api.items():
        if (
            payload.get("@type") in ("FeatureChainExpression", "FeatureValue")
            and "value" in payload
            and not payload.get("ownedRelationship")
        ):
            payload["@type"] = "LiteralString"
            if isinstance(payload.get("value"), str):
                payload["value"] = payload["value"].strip('"')

    # Fourth pass: qualifiedName for namespaces/packages (walk owner chain + imports).
    for eid, payload in api.items():
        t = payload.get("@type", "")
        if t in ("Namespace", "Package", "AnalysisCaseDefinition", "AnalysisCaseUsage"):
            elem = index.get(eid, {})
            qn = _namespace_qualified_name(elem, index)
            if qn:
                payload["qualifiedName"] = qn
            # Also fold in imported members as ownedElement names for lookups.
            imported = _collect_imported_members(elem, index)
            for name, child in imported.items():
                if name:
                    pass  # available via index; the walker resolves by name elsewhere

    return api


def adapt_list(export_json: dict | list) -> list[dict]:
    """Return the adapted elements as a list (values of :func:`adapt`)."""
    return list(adapt(export_json).values())
