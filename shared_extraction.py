from typing import Dict, List, Tuple
import re


def s(value) -> str:
    return "" if value is None else str(value)


def unwrap(value):
    return getattr(value, "wrappedValue", value)


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def split_family_type(name: str) -> Tuple[str, str]:
    if ":" in name:
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    return name.strip(), ""


def parse_family_and_type_label(text: str) -> Tuple[str, str]:
    t = s(text).strip()
    if not t:
        return "", ""
    if ":" in t:
        left, right = t.split(":", 1)
        return left.strip(), right.strip()
    return t, ""


def is_flooring_text(text: str) -> bool:
    t = s(text).strip().lower()
    if not t:
        return False
    keys = [
        "tile",
        "tiles",
        "vitrified",
        "vitified",
        "ceramic",
        "marble",
        "granite",
        "skirting",
        "flooring",
        "floor",
    ]
    return any(k in t for k in keys)


def is_rcc_text(text: str) -> bool:
    t = s(text).strip().lower()
    if not t:
        return False
    return any(
        k in t
        for k in (
            "rcc",
            "reinforced concrete",
            "reinforced cement concrete",
            "m30",
            "m25",
            "m20",
        )
    )


def _first(psets: Dict[str, List[str]], name: str) -> str:
    vals = psets.get(name.lower(), [])
    return vals[0] if vals else ""


def _all(psets: Dict[str, List[str]], name: str) -> List[str]:
    return psets.get(name.lower(), [])


def _material_description(material, material_desc_cache: Dict[int, str]) -> str:
    mid = int(material.id())
    if mid in material_desc_cache:
        return material_desc_cache[mid]

    candidates: List[Tuple[str, str]] = []
    direct = s(getattr(material, "Description", "")).strip()
    if direct:
        candidates.append(("material.description", direct))

    for prop_set in getattr(material, "HasProperties", []) or []:
        pset_name = s(getattr(prop_set, "Name", "")).strip().lower()
        props = getattr(prop_set, "Properties", None) or getattr(prop_set, "ExtendedProperties", None)
        for prop in props or []:
            if not prop.is_a("IfcPropertySingleValue"):
                continue
            if s(prop.Name).strip().lower() != "description":
                continue
            text = s(unwrap(prop.NominalValue)).strip()
            if text:
                candidates.append((pset_name, text))

    if not candidates:
        material_desc_cache[mid] = ""
        return ""

    def _score(item: Tuple[str, str]) -> Tuple[int, int, int]:
        src, text = item
        t = text.lower()
        has_specific = int(
            any(
                k in t
                for k in (
                    "laying reinforced cement concrete",
                    "reinforced cement concrete",
                    "rcc",
                    "flooring finished",
                    "ceramic tiles",
                    "vitrified",
                    "marble",
                    "granite",
                )
            )
        )
        src_priority = int("identity" in src or "type comments" in src)
        generic_penalty = -int(any(k in t for k in ("basic structural asset", "structural asset")))
        return (has_specific, src_priority, generic_penalty)

    best = max(candidates, key=_score)[1]
    material_desc_cache[mid] = best
    return best


def _build_material_desc_index(model) -> Dict[str, str]:
    out: Dict[str, str] = {}
    cache: Dict[int, str] = {}
    for mat in model.by_type("IfcMaterial") or []:
        name = s(getattr(mat, "Name", "")).strip()
        if not name:
            continue
        desc = s(_material_description(mat, cache)).strip()
        if not desc:
            continue
        old = s(out.get(name, "")).strip()
        if not old or len(desc) > len(old):
            out[name] = desc
    return out


def _collect_elements(model) -> List:
    classes = [
        "IfcWall",
        "IfcWallStandardCase",
        "IfcColumn",
        "IfcSlab",
        "IfcBeam",
        "IfcFooting",
        "IfcMember",
        "IfcStair",
        "IfcStairFlight",
        "IfcRamp",
        "IfcCovering",
    ]
    out = []
    for cls in classes:
        out.extend(model.by_type(cls))
    return list({e.id(): e for e in out}.values())


def _build_context(model) -> List[Dict]:
    contexts: List[Dict] = []
    material_desc_cache: Dict[int, str] = {}

    for e in _collect_elements(model):
        psets: Dict[str, List[str]] = {}
        qto = {
            "Length": "",
            "Width": "",
            "Height": "",
            "GrossFootprintArea": "",
            "NetArea": "",
            "GrossArea": "",
            "NetSideArea": "",
            "GrossSideArea": "",
            "CrossSectionArea": "",
            "OuterSurfaceArea": "",
            "NetVolume": "",
            "GrossVolume": "",
            "Area": "",
            "Volume": "",
            "_AnyArea": "",
            "_AnyVolume": "",
            "_AnyLength": "",
            "_AnyWidth": "",
        }

        for rel in getattr(e, "IsDefinedBy", []) or []:
            if rel.is_a("IfcRelDefinesByProperties"):
                pdef = rel.RelatingPropertyDefinition
                if pdef and pdef.is_a("IfcPropertySet"):
                    for prop in pdef.HasProperties or []:
                        if not prop.is_a("IfcPropertySingleValue"):
                            continue
                        pname = s(prop.Name).strip().lower()
                        pval = s(unwrap(prop.NominalValue)).strip()
                        if pval:
                            psets.setdefault(pname, [])
                            if pval.lower() not in [x.lower() for x in psets[pname]]:
                                psets[pname].append(pval)
                if pdef and pdef.is_a("IfcElementQuantity"):
                    for q in pdef.Quantities or []:
                        name = s(getattr(q, "Name", ""))
                        lname = name.strip().lower()
                        if q.is_a("IfcQuantityLength"):
                            val = s(getattr(q, "LengthValue", ""))
                            if name in ("Length", "Width", "Height"):
                                qto[name] = val
                            if (not qto["_AnyLength"]) and ("length" in lname or lname in ("l", "len")) and val.strip():
                                qto["_AnyLength"] = val
                            if (not qto["_AnyWidth"]) and (
                                "width" in lname or "breadth" in lname or lname in ("w", "b")
                            ) and val.strip():
                                qto["_AnyWidth"] = val
                        elif q.is_a("IfcQuantityArea"):
                            val = s(getattr(q, "AreaValue", ""))
                            if name in qto:
                                qto[name] = val
                            if not qto["_AnyArea"] and val.strip():
                                qto["_AnyArea"] = val
                        elif q.is_a("IfcQuantityVolume"):
                            val = s(getattr(q, "VolumeValue", ""))
                            if name in qto:
                                qto[name] = val
                            if not qto["_AnyVolume"] and val.strip():
                                qto["_AnyVolume"] = val

            if rel.is_a("IfcRelDefinesByType"):
                rtype = getattr(rel, "RelatingType", None)
                for pset in getattr(rtype, "HasPropertySets", []) or []:
                    if not pset or not pset.is_a("IfcPropertySet"):
                        continue
                    for prop in pset.HasProperties or []:
                        if not prop.is_a("IfcPropertySingleValue"):
                            continue
                        pname = s(prop.Name).strip().lower()
                        pval = s(unwrap(prop.NominalValue)).strip()
                        if pval:
                            psets.setdefault(pname, [])
                            if pval.lower() not in [x.lower() for x in psets[pname]]:
                                psets[pname].append(pval)

        if not qto["Area"]:
            qto["Area"] = _first(psets, "Area") or _first(psets, "Net Area") or _first(psets, "Gross Area")
        if not qto["Volume"]:
            qto["Volume"] = _first(psets, "Volume") or _first(psets, "Net Volume") or _first(psets, "Gross Volume")
        if not qto["Length"]:
            qto["Length"] = _first(psets, "Length")
        if not qto["Width"]:
            qto["Width"] = _first(psets, "Width")
        if not qto["NetArea"]:
            qto["NetArea"] = qto["NetSideArea"] or qto["OuterSurfaceArea"] or qto["CrossSectionArea"]
        if not qto["GrossArea"]:
            qto["GrossArea"] = qto["GrossSideArea"] or qto["OuterSurfaceArea"] or qto["CrossSectionArea"]

        level = ""
        for rel in getattr(e, "ContainedInStructure", []) or []:
            st = getattr(rel, "RelatingStructure", None)
            if st and st.is_a("IfcBuildingStorey"):
                level = s(getattr(st, "Name", ""))
                break
        if not level:
            level = _first(psets, "Base Constraint")

        name = s(getattr(e, "Name", ""))
        fam_from_name, type_from_name = split_family_type(name)
        family = _first(psets, "Family") or fam_from_name
        type_name = _first(psets, "Type") or type_from_name
        fat = _first(psets, "Family and Type")
        if fat:
            f2, t2 = parse_family_and_type_label(fat)
            if not family and f2:
                family = f2
            if not type_name and t2:
                type_name = t2

        desc_candidates = []
        for pname in ("Description", "Type Comments", "Assembly Description", "Comments", "Original Type"):
            desc_candidates.extend(_all(psets, pname))
        native_desc = s(getattr(e, "Description", "")).strip()
        if native_desc:
            desc_candidates.append(native_desc)
        desc_candidates = [x for x in desc_candidates if str(x).strip()]

        material_defs: List[Dict] = []
        for rel in getattr(e, "HasAssociations", []) or []:
            if not rel.is_a("IfcRelAssociatesMaterial"):
                continue
            rel_mat = rel.RelatingMaterial
            if not rel_mat:
                continue
            if rel_mat.is_a("IfcMaterial"):
                material_defs.append(
                    {
                        "kind": "single",
                        "name": s(rel_mat.Name),
                        "desc": _material_description(rel_mat, material_desc_cache),
                    }
                )
            elif rel_mat.is_a("IfcMaterialLayerSetUsage"):
                layer_set = rel_mat.ForLayerSet
                for layer in getattr(layer_set, "MaterialLayers", []) or []:
                    mat = layer.Material
                    if not mat:
                        continue
                    thickness_m = float(layer.LayerThickness or 0.0) / 1000.0
                    material_defs.append(
                        {
                            "kind": "layer",
                            "name": s(mat.Name),
                            "desc": _material_description(mat, material_desc_cache),
                            "thickness_m": thickness_m,
                        }
                    )
            elif rel_mat.is_a("IfcMaterialLayerSet"):
                for layer in getattr(rel_mat, "MaterialLayers", []) or []:
                    mat = layer.Material
                    if not mat:
                        continue
                    thickness_m = float(layer.LayerThickness or 0.0) / 1000.0
                    material_defs.append(
                        {
                            "kind": "layer",
                            "name": s(mat.Name),
                            "desc": _material_description(mat, material_desc_cache),
                            "thickness_m": thickness_m,
                        }
                    )
            elif rel_mat.is_a("IfcMaterialList"):
                for mat in getattr(rel_mat, "Materials", []) or []:
                    if not mat:
                        continue
                    material_defs.append(
                        {
                            "kind": "single",
                            "name": s(mat.Name),
                            "desc": _material_description(mat, material_desc_cache),
                        }
                    )
            elif rel_mat.is_a("IfcMaterialConstituentSet"):
                for constituent in getattr(rel_mat, "MaterialConstituents", []) or []:
                    mat = constituent.Material
                    if not mat:
                        continue
                    material_defs.append(
                        {
                            "kind": "single",
                            "name": s(mat.Name),
                            "desc": _material_description(mat, material_desc_cache),
                        }
                    )

        contexts.append(
            {
                "element": e,
                "id": int(e.id()),
                "ifc_class": s(e.is_a()),
                "global_id": s(getattr(e, "GlobalId", "")),
                "name": name,
                "family": family,
                "type": type_name,
                "level": level,
                "psets": psets,
                "qto": qto,
                "descriptions": desc_candidates,
                "material_defs": material_defs,
                "structural_material": _first(psets, "Structural Material")
                or _first(psets, "Monolithic Material")
                or _first(psets, "Material"),
            }
        )

    return contexts


def _rcc_desc_score(text: str) -> Tuple[int, int, int]:
    t = s(text).strip().lower()
    if not t:
        return (0, 0, 0)
    has_rcc_phrase = int(
        any(
            k in t
            for k in (
                "laying reinforced cement concrete",
                "reinforced cement concrete",
                "rcc of",
                "rcc",
                "m30",
                "m25",
                "m20",
            )
        )
    )
    generic_penalty = -int(any(k in t for k in ("basic structural asset", "structural asset")))
    return (has_rcc_phrase, generic_penalty, len(t))


def _pick_element_description(ctx: Dict, mode: str) -> str:
    candidates = list(ctx.get("descriptions", []))
    if not candidates:
        return ""

    def _score(text: str) -> Tuple[int, int, int]:
        t = s(text).strip().lower()
        if mode == "floor":
            has_primary = int(
                any(
                    k in t
                    for k in (
                        "flooring finished",
                        "ceramic tiles",
                        "vitrified tiles",
                        "marble flooring",
                        "granite flooring",
                    )
                )
            )
            has_secondary = int(is_flooring_text(t))
            generic_penalty = -int(any(k in t for k in ("basic structural asset", "structural asset")))
            return (has_primary, has_secondary + generic_penalty, len(t))
        has_rcc = int(
            any(
                k in t
                for k in (
                    "laying reinforced cement concrete",
                    "reinforced cement concrete",
                    "rcc of",
                    "rcc",
                    "m30",
                    "m25",
                    "m20",
                )
            )
        )
        generic_penalty = -int(any(k in t for k in ("basic structural asset", "structural asset")))
        return (has_rcc, generic_penalty, len(t))

    return max(candidates, key=_score)


def _material_rows(ctx: Dict, area: float, volume: float, prefer_volume_for_layers: bool = False) -> List[Dict[str, str]]:
    out = []
    for m in ctx.get("material_defs", []):
        kind = m.get("kind")
        if kind == "layer":
            thickness = float(m.get("thickness_m") or 0.0)
            if prefer_volume_for_layers and volume > 0:
                mat_vol = volume
            else:
                mat_vol = area * thickness if area > 0 and thickness > 0 else 0.0
            out.append(
                {
                    "Material:Name": s(m.get("name", "")),
                    "Material:Description": s(m.get("desc", "")),
                    "Material:Area": s(area) if area else "",
                    "Material:Volume": s(mat_vol) if mat_vol else "",
                }
            )
        else:
            out.append(
                {
                    "Material:Name": s(m.get("name", "")),
                    "Material:Description": s(m.get("desc", "")),
                    "Material:Area": s(area) if area else "",
                    "Material:Volume": s(volume) if volume else "",
                }
            )
    return out


def _pick_area_for_floor(qto: Dict[str, str]) -> float:
    for key in (
        "NetArea",
        "GrossArea",
        "Area",
        "GrossFootprintArea",
        "NetSideArea",
        "GrossSideArea",
        "OuterSurfaceArea",
        "CrossSectionArea",
        "_AnyArea",
    ):
        if s(qto.get(key, "")).strip():
            return to_float(qto[key])
    l = to_float(s(qto.get("_AnyLength", "")))
    w = to_float(s(qto.get("_AnyWidth", "")))
    if l > 0 and w > 0:
        return l * w
    return 0.0


def _pick_volume_for_floor(qto: Dict[str, str]) -> float:
    for key in ("NetVolume", "GrossVolume", "Volume", "_AnyVolume"):
        if s(qto.get(key, "")).strip():
            return to_float(qto[key])
    return 0.0


def _pick_area_for_rcc(qto: Dict[str, str], ifc_class: str) -> float:
    if ifc_class == "IfcColumn":
        order = [
            "CrossSectionArea",
            "OuterSurfaceArea",
            "NetArea",
            "GrossArea",
            "Area",
            "GrossFootprintArea",
            "NetSideArea",
            "GrossSideArea",
        ]
    else:
        order = [
            "NetArea",
            "GrossArea",
            "GrossFootprintArea",
            "Area",
            "NetSideArea",
            "GrossSideArea",
            "OuterSurfaceArea",
            "CrossSectionArea",
        ]
    for k in order:
        if s(qto.get(k, "")).strip():
            return to_float(qto[k])
    return 0.0


def _infer_rcc_name(structural_material: str, *texts) -> str:
    blob = " ".join([s(structural_material)] + [s(t) for t in texts]).lower()
    m = re.search(r"\bm\s*([0-9]{2})\b", blob)
    if m:
        return f"RCC - M{m.group(1)}"
    return "RCC"


def _is_stair_rcc_candidate(*texts) -> bool:
    blob = " ".join(s(t).strip().lower() for t in texts)
    return (
        "cast-in-place stair" in blob
        or "m_monolithic stair" in blob
        or "m monolithic stair" in blob
    )


def _is_excluded_rcc_component(*texts) -> bool:
    blob = " ".join(s(t).strip().lower() for t in texts)
    return ("monolithic landing" in blob) or ("m_monolithic landing" in blob)


def build_rows(model) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    ctxs = _build_context(model)
    material_desc_index = _build_material_desc_index(model)
    wall_rows: List[Dict[str, str]] = []
    rcc_rows: List[Dict[str, str]] = []
    floor_rows: List[Dict[str, str]] = []

    seen_lift_global_ids = set()

    for ctx in ctxs:
        e = ctx["element"]
        ifc_class = ctx["ifc_class"]
        name = ctx["name"]
        family = ctx["family"]
        type_name = ctx["type"]
        level = ctx["level"]
        qto = ctx["qto"]
        psets = ctx["psets"]
        structural_material = ctx.get("structural_material", "")

        # Wall extraction (IfcWall only)
        if ifc_class in ("IfcWall", "IfcWallStandardCase"):
            element_desc = _pick_element_description(ctx, mode="floor")
            length_val = _first(psets, "Length") or qto["Length"]
            width_val = _first(psets, "Width") or qto["Width"]
            area_val = _first(psets, "Area")
            volume_val = _first(psets, "Volume")
            wall_area = to_float(qto["NetSideArea"] or qto["GrossSideArea"] or area_val)
            wall_volume = to_float(qto["NetVolume"] or qto["GrossVolume"] or volume_val)
            mats = _material_rows(ctx, wall_area, wall_volume, prefer_volume_for_layers=False)
            if not mats:
                mats = [
                    {
                        "Material:Name": "",
                        "Material:Description": "",
                        "Material:Area": s(wall_area) if wall_area else "",
                        "Material:Volume": s(wall_volume) if wall_volume else "",
                    }
                ]
            for mat in mats:
                mat_name = s(mat.get("Material:Name", ""))
                mat_desc = s(mat.get("Material:Description", ""))
                final_desc = mat_desc
                if element_desc and (is_flooring_text(" ".join([family, type_name, mat_name, mat_desc])) or not mat_desc):
                    final_desc = element_desc
                wall_rows.append(
                    {
                        "ExpressId": s(ctx["id"]),
                        "GlobalId": s(ctx["global_id"]),
                        "Family": family,
                        "Type": type_name,
                        "Base Constraint": level,
                        "Length": length_val,
                        "Width": width_val,
                        "Material:Name": mat_name,
                        "Material:Description": final_desc,
                        "Material:Area": mat.get("Material:Area", ""),
                        "Material:Volume": mat.get("Material:Volume", ""),
                    }
                )

        # RCC extraction
        if ifc_class in (
            "IfcColumn",
            "IfcSlab",
            "IfcBeam",
            "IfcFooting",
            "IfcWall",
            "IfcWallStandardCase",
            "IfcMember",
            "IfcStair",
            "IfcStairFlight",
            "IfcRamp",
        ):
            element_desc = _pick_element_description(ctx, mode="rcc")
            extra_type_hints = _all(psets, "Original Type") + _all(psets, "Family and Type")
            if _is_excluded_rcc_component(name, family, type_name, element_desc, " ".join(extra_type_hints)):
                pass
            else:
                lift_hints = [name, family, type_name] + _all(psets, "Type") + _all(psets, "Original Type") + _all(psets, "Family and Type") + _all(psets, "Reference")
                is_lift_wall = "lift wall" in " ".join(s(x) for x in lift_hints).lower()
                level_l = level.lower()

                if is_lift_wall and (("parapet" in level_l) or ("roof" in level_l)):
                    pass
                else:
                    if is_lift_wall:
                        element_volume = to_float(qto["Volume"])
                        if element_volume <= 0:
                            pass
                        else:
                            gid = s(ctx["global_id"]).strip()
                            if gid and gid in seen_lift_global_ids:
                                pass
                            else:
                                if gid:
                                    seen_lift_global_ids.add(gid)
                                element_area = _pick_area_for_rcc(qto, ifc_class)
                                mats = _material_rows(ctx, element_area, element_volume, prefer_volume_for_layers=True)
                                if not mats:
                                    if is_rcc_text(" ".join([name, family, type_name, element_desc, structural_material])):
                                        inferred_name = structural_material or _infer_rcc_name(structural_material, name, family, type_name, element_desc)
                                        mats = [
                                            {
                                                "Material:Name": inferred_name,
                                                "Material:Description": element_desc,
                                                "Material:Volume": s(element_volume),
                                            }
                                        ]
                                stair_candidate = _is_stair_rcc_candidate(name, family, type_name, element_desc)
                                stair_rcc_name = _infer_rcc_name(structural_material, name, family, type_name, element_desc)
                                candidates = []
                                for mat in mats:
                                    mat_name = s(mat.get("Material:Name", "")).strip()
                                    mat_desc = s(mat.get("Material:Description", "")).strip()
                                    mat_vol = s(mat.get("Material:Volume", "")).strip()
                                    if stair_candidate:
                                        lower_name = mat_name.lower()
                                        if any(k in lower_name for k in ("tile", "marble", "granite", "ceramic", "vitrified", "vitified", "skirting")):
                                            continue
                                        if (not mat_name) or ("rcc" not in lower_name):
                                            mat_name = stair_rcc_name
                                    if structural_material and (not mat_name or mat_name.lower() in ("<unnamed>", "unnamed", "rcc")):
                                        mat_name = structural_material
                                    indexed_desc = material_desc_index.get(mat_name, "")
                                    final_desc = max([element_desc, mat_desc, indexed_desc], key=_rcc_desc_score)
                                    if not (
                                        is_rcc_text(mat_name)
                                        or is_rcc_text(final_desc)
                                        or is_rcc_text(family)
                                        or is_rcc_text(type_name)
                                        or is_rcc_text(name)
                                        or stair_candidate
                                    ):
                                        continue
                                    candidates.append(
                                        {
                                            "Material:Name": mat_name,
                                            "Material:Description": final_desc,
                                            "Material:Volume": mat_vol,
                                        }
                                    )
                                if not candidates and stair_candidate:
                                    candidates = [
                                        {
                                            "Material:Name": stair_rcc_name,
                                            "Material:Description": max(
                                                [
                                                    element_desc,
                                                    material_desc_index.get(stair_rcc_name, ""),
                                                ],
                                                key=_rcc_desc_score,
                                            ),
                                            "Material:Volume": s(element_volume),
                                        }
                                    ]
                                if candidates:
                                    best = max(
                                        candidates,
                                        key=lambda c: (
                                            int(bool(structural_material) and s(c.get("Material:Name", "")).lower() == structural_material.lower()),
                                            int(bool(re.search(r"\bm\s*[0-9]{2}\b", s(c.get("Material:Name", "")).lower()))),
                                            int("rcc" in s(c.get("Material:Name", "")).lower()),
                                            int(to_float(s(c.get("Material:Volume", ""))) > 0),
                                            len(s(c.get("Material:Description", ""))),
                                        ),
                                    )
                                    best_mat_vol = s(best.get("Material:Volume", "")).strip() or s(element_volume)
                                    rcc_rows.append(
                                        {
                                            "ExpressId": s(ctx["id"]),
                                            "GlobalId": s(ctx["global_id"]),
                                            "Family": family,
                                            "Type": type_name,
                                            "Level": level,
                                            "Material:Name": s(best.get("Material:Name", "")),
                                            "Material:Description": s(best.get("Material:Description", "")),
                                            "Material:Volume": best_mat_vol,
                                        }
                                    )
                    else:
                        element_volume = to_float(qto["NetVolume"] or qto["Volume"] or qto["GrossVolume"])
                        element_area = _pick_area_for_rcc(qto, ifc_class)
                        mats = _material_rows(ctx, element_area, element_volume, prefer_volume_for_layers=(ifc_class in ("IfcWall", "IfcWallStandardCase")))
                        if not mats:
                            if is_rcc_text(" ".join([name, family, type_name, element_desc, structural_material])):
                                inferred_name = structural_material or _infer_rcc_name(structural_material, name, family, type_name, element_desc)
                                mats = [
                                    {
                                        "Material:Name": inferred_name,
                                        "Material:Description": element_desc,
                                        "Material:Volume": s(element_volume) if element_volume else "",
                                    }
                                ]
                        stair_candidate = _is_stair_rcc_candidate(name, family, type_name, element_desc)
                        stair_rcc_name = _infer_rcc_name(structural_material, name, family, type_name, element_desc)
                        candidates = []
                        for mat in mats:
                            mat_name = s(mat.get("Material:Name", "")).strip()
                            mat_desc = s(mat.get("Material:Description", "")).strip()
                            mat_vol = s(mat.get("Material:Volume", "")).strip()
                            if stair_candidate:
                                lower_name = mat_name.lower()
                                if any(k in lower_name for k in ("tile", "marble", "granite", "ceramic", "vitrified", "vitified", "skirting")):
                                    continue
                                if (not mat_name) or ("rcc" not in lower_name):
                                    mat_name = stair_rcc_name
                            if structural_material and (not mat_name or mat_name.lower() in ("<unnamed>", "unnamed", "rcc")):
                                mat_name = structural_material
                            indexed_desc = material_desc_index.get(mat_name, "")
                            final_desc = max([element_desc, mat_desc, indexed_desc], key=_rcc_desc_score)
                            if not (
                                is_rcc_text(mat_name)
                                or is_rcc_text(final_desc)
                                or is_rcc_text(family)
                                or is_rcc_text(type_name)
                                or is_rcc_text(name)
                                or stair_candidate
                            ):
                                continue
                            candidates.append(
                                {
                                    "Material:Name": mat_name,
                                    "Material:Description": final_desc,
                                    "Material:Volume": mat_vol,
                                }
                            )
                        if not candidates and stair_candidate:
                            candidates = [
                                {
                                    "Material:Name": stair_rcc_name,
                                    "Material:Description": max(
                                        [
                                            element_desc,
                                            material_desc_index.get(stair_rcc_name, ""),
                                        ],
                                        key=_rcc_desc_score,
                                    ),
                                    "Material:Volume": s(element_volume) if element_volume else "",
                                }
                            ]
                        if candidates:
                            best = max(
                                candidates,
                                key=lambda c: (
                                    int(bool(structural_material) and s(c.get("Material:Name", "")).lower() == structural_material.lower()),
                                    int(bool(re.search(r"\bm\s*[0-9]{2}\b", s(c.get("Material:Name", "")).lower()))),
                                    int("rcc" in s(c.get("Material:Name", "")).lower()),
                                    int(to_float(s(c.get("Material:Volume", ""))) > 0),
                                    len(s(c.get("Material:Description", ""))),
                                ),
                            )
                            best_mat_vol = s(best.get("Material:Volume", "")).strip()
                            if not best_mat_vol and element_volume > 0:
                                best_mat_vol = s(element_volume)
                            rcc_rows.append(
                                {
                                    "ExpressId": s(ctx["id"]),
                                    "GlobalId": s(ctx["global_id"]),
                                    "Family": family,
                                    "Type": type_name,
                                    "Level": level,
                                    "Material:Name": s(best.get("Material:Name", "")),
                                    "Material:Description": s(best.get("Material:Description", "")),
                                    "Material:Volume": best_mat_vol,
                                }
                            )

        # Floor extraction
        if ifc_class in (
            "IfcSlab",
            "IfcCovering",
            "IfcWall",
            "IfcWallStandardCase",
            "IfcStair",
            "IfcStairFlight",
            "IfcRamp",
            "IfcMember",
            "IfcBeam",
            "IfcColumn",
        ):
            skip_signal = " ".join([name, family, type_name]).lower()
            if ("monolithic landing" in skip_signal) or ("monolithic run" in skip_signal):
                continue
            element_desc = _pick_element_description(ctx, mode="floor")
            area = _pick_area_for_floor(qto)
            volume = _pick_volume_for_floor(qto)
            mats = _material_rows(ctx, area, volume, prefer_volume_for_layers=False)
            if not mats:
                mats = [
                    {
                        "Material:Name": "",
                        "Material:Description": "",
                        "Material:Area": s(area) if area else "",
                        "Material:Volume": s(volume) if volume else "",
                    }
                ]
            for mat in mats:
                mat_name = s(mat.get("Material:Name", ""))
                mat_desc = s(mat.get("Material:Description", ""))
                signal = " ".join([name, family, type_name, element_desc, mat_name, mat_desc])
                if not is_flooring_text(signal):
                    continue
                if is_rcc_text(signal):
                    continue
                if element_desc and any(k in element_desc.lower() for k in ("flooring finished", "ceramic tiles", "vitrified", "marble", "granite")):
                    final_desc = element_desc
                else:
                    final_desc = mat_desc or element_desc
                floor_rows.append(
                    {
                        "ExpressId": s(ctx["id"]),
                        "GlobalId": s(ctx["global_id"]),
                        "IfcClass": ifc_class,
                        "Family": family,
                        "Type": type_name,
                        "Level": level,
                        "Material:Name": mat_name,
                        "Material:Description": final_desc,
                        "Material:Area": mat.get("Material:Area", ""),
                        "Material:Volume": mat.get("Material:Volume", ""),
                    }
                )

    return wall_rows, rcc_rows, floor_rows
