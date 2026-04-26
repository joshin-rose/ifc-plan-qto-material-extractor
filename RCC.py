import csv
import os
import re
from typing import Dict, List, Tuple

import ifcopenshell


def s(value) -> str:
    return "" if value is None else str(value)


def unwrap(value):
    return getattr(value, "wrappedValue", value)


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def pick_material_area_with_source(qto: Dict[str, str], ifc_class: str) -> Tuple[float, str]:
    # Class-aware preference: columns usually provide CrossSectionArea/OuterSurfaceArea,
    # while slabs/walls usually provide footprint/side/gross-net areas.
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

    candidates = [(k, qto.get(k, "")) for k in order]
    for source, value in candidates:
        if s(value).strip() != "":
            return to_float(s(value)), source
    return 0.0, ""


def get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_ifc_file() -> str:
    path = os.path.join(get_script_dir(), "finally.ifc")
    if not os.path.exists(path):
        raise SystemExit("finally.ifc not found in script directory.")
    return path


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


def get_pset_value(element, property_name: str) -> str:
    vals = get_pset_values(element, property_name)
    return vals[0] if vals else ""


def get_pset_values(element, property_name: str) -> List[str]:
    out: List[str] = []
    seen = set()

    def _push(v) -> None:
        vv = s(unwrap(v)).strip()
        if not vv:
            return
        key = vv.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(vv)

    for rel in getattr(element, "IsDefinedBy", []) or []:
        # Element-level property sets
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef and pdef.is_a("IfcPropertySet"):
                for prop in pdef.HasProperties or []:
                    if (
                        prop.is_a("IfcPropertySingleValue")
                        and s(prop.Name).strip().lower() == property_name.strip().lower()
                    ):
                        _push(prop.NominalValue)

        # Type-level property sets (common in Revit exports)
        if rel.is_a("IfcRelDefinesByType"):
            rtype = getattr(rel, "RelatingType", None)
            for pset in getattr(rtype, "HasPropertySets", []) or []:
                if not pset or not pset.is_a("IfcPropertySet"):
                    continue
                for prop in pset.HasProperties or []:
                    if (
                        prop.is_a("IfcPropertySingleValue")
                        and s(prop.Name).strip().lower() == property_name.strip().lower()
                    ):
                        _push(prop.NominalValue)
    return out


def get_level(element) -> str:
    for rel in getattr(element, "ContainedInStructure", []) or []:
        st = getattr(rel, "RelatingStructure", None)
        if st and st.is_a("IfcBuildingStorey"):
            return s(getattr(st, "Name", ""))
    return get_pset_value(element, "Base Constraint")


def get_family_type(element, element_name: str) -> Tuple[str, str]:
    family_from_name, type_from_name = split_family_type(element_name)

    family = s(get_pset_value(element, "Family")).strip()
    type_name = s(get_pset_value(element, "Type")).strip()

    # Some elements (including certain footings) carry a combined
    # "Family and Type" value like:
    # "RCC RECTANGULAR FOOTING: 1800 x 1200 x 600mm"
    family_and_type = s(get_pset_value(element, "Family and Type")).strip()
    if family_and_type:
        f2, t2 = parse_family_and_type_label(family_and_type)
        if not family and f2:
            family = f2
        if not type_name and t2:
            type_name = t2

    if not family:
        family = family_from_name
    if not type_name:
        type_name = type_from_name
    return family, type_name


def get_element_description(element) -> str:
    candidates: List[str] = []
    for prop_name in ("Description", "Type Comments", "Assembly Description", "Comments", "Original Type"):
        candidates.extend(get_pset_values(element, prop_name))
    native_desc = s(getattr(element, "Description", "")).strip()
    if native_desc:
        candidates.append(native_desc)

    if not candidates:
        return ""

    def _score(text: str) -> Tuple[int, int, int]:
        t = s(text).strip().lower()
        has_rcc_sentence = int(
            any(
                k in t
                for k in (
                    "laying reinforced cement concrete",
                    "reinforced cement concrete",
                    "rcc of",
                    "m30",
                    "m25",
                    "m20",
                )
            )
        )
        is_generic = int(any(k in t for k in ("basic structural asset", "structural asset")))
        return (has_rcc_sentence, -is_generic, len(t))

    return max(candidates, key=_score)


def get_structural_material_label(element) -> str:
    # Revit exports commonly store RCC grade here even when explicit
    # element->material associations are sparse for some footing/slab objects.
    for prop_name in ("Structural Material", "Monolithic Material", "Material"):
        vals = get_pset_values(element, prop_name)
        if vals:
            return s(vals[0]).strip()
    return ""


def get_quantities(element) -> Dict[str, str]:
    out = {
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
    }
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcElementQuantity"):
            continue
        for q in pdef.Quantities or []:
            name = s(getattr(q, "Name", ""))
            if q.is_a("IfcQuantityLength") and name in ("Length", "Width", "Height"):
                out[name] = s(getattr(q, "LengthValue", ""))
            elif q.is_a("IfcQuantityArea") and name in (
                "GrossFootprintArea",
                "NetArea",
                "GrossArea",
                "NetSideArea",
                "GrossSideArea",
                "CrossSectionArea",
                "OuterSurfaceArea",
                "Area",
            ):
                out[name] = s(getattr(q, "AreaValue", ""))
            elif q.is_a("IfcQuantityVolume") and name in ("NetVolume", "GrossVolume", "Volume"):
                out[name] = s(getattr(q, "VolumeValue", ""))

    # Pset fallback for common Revit-exported fields
    if not out["Length"]:
        out["Length"] = get_pset_value(element, "Length")
    if not out["Width"]:
        out["Width"] = get_pset_value(element, "Width")
    if not out["Area"]:
        out["Area"] = get_pset_value(element, "Area")
    if not out["Volume"]:
        out["Volume"] = get_pset_value(element, "Volume")
    if not out["NetArea"]:
        out["NetArea"] = out["NetSideArea"] or out["OuterSurfaceArea"] or out["CrossSectionArea"]
    if not out["GrossArea"]:
        out["GrossArea"] = out["GrossSideArea"] or out["OuterSurfaceArea"] or out["CrossSectionArea"]
    return out


def get_material_description(material) -> str:
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
            if not text:
                continue
            candidates.append((pset_name, text))

    if not candidates:
        return ""

    def _score(item: Tuple[str, str]) -> Tuple[int, int, int]:
        src, text = item
        t = text.lower()
        has_rcc_phrase = int(
            any(
                k in t
                for k in (
                    "laying reinforced cement concrete",
                    "reinforced cement concrete",
                    "rcc",
                    "m30",
                    "m25",
                    "m20",
                )
            )
        )
        src_priority = int("identity" in src)
        generic_penalty = -int(any(k in t for k in ("basic structural asset", "structural asset")))
        return (has_rcc_phrase, src_priority, generic_penalty)

    return max(candidates, key=_score)[1]


def build_material_description_index(model) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for mat in model.by_type("IfcMaterial") or []:
        name = s(getattr(mat, "Name", "")).strip()
        if not name:
            continue
        desc = s(get_material_description(mat)).strip()
        if not desc:
            continue
        # Keep richer text if multiple descriptions exist for same material name.
        old = s(out.get(name, "")).strip()
        if not old or len(desc) > len(old):
            out[name] = desc
    return out


def is_rcc_text(text: str) -> bool:
    t = s(text).strip().lower()
    if not t:
        return False
    keys = ["rcc", "reinforced concrete", "concrete", "m30", "m25", "m20"]
    return any(k in t for k in keys)


def infer_rcc_material_name(*texts) -> str:
    blob = " ".join(s(t).lower() for t in texts)
    m = re.search(r"\bm\s*([0-9]{2})\b", blob)
    if m:
        return f"RCC - M{m.group(1)}"
    return "RCC"


def is_excluded_rcc_component(*texts) -> bool:
    blob = " ".join(s(t).strip().lower() for t in texts)
    if not blob:
        return False
    # Staircase extraction is intentionally disabled for RCC for now.
    return (
        ("stair" in blob)
        or ("staircase" in blob)
        or ("monolithic run" in blob)
        or ("m_monolithic run" in blob)
        or ("monolithic landing" in blob)
        or ("m_monolithic landing" in blob)
    )


def get_material_rows(element, element_area: float, element_volume: float) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    is_wall_like = bool(element.is_a("IfcWall") or element.is_a("IfcWallStandardCase"))
    for rel in getattr(element, "HasAssociations", []) or []:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        rel_mat = rel.RelatingMaterial
        if not rel_mat:
            continue

        if rel_mat.is_a("IfcMaterial"):
            m_name = s(rel_mat.Name)
            m_desc = get_material_description(rel_mat)
            rows.append(
                {
                    "Material:Name": m_name,
                    "Material:Description": m_desc,
                    "Material:Area": s(element_area) if element_area else "",
                    "Material:Volume": s(element_volume) if element_volume else "",
                }
            )

        elif rel_mat.is_a("IfcMaterialLayerSetUsage"):
            layer_set = rel_mat.ForLayerSet
            for layer in getattr(layer_set, "MaterialLayers", []) or []:
                mat = layer.Material
                if not mat:
                    continue
                thickness_model = float(layer.LayerThickness or 0.0)
                thickness_m = thickness_model / 1000.0
                # For wall-like RCC elements, prefer element quantity volume
                # to avoid drift from side-area*thickness approximations.
                if is_wall_like and element_volume:
                    mat_vol = element_volume
                else:
                    mat_vol = element_area * thickness_m if element_area and thickness_m else 0.0
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(element_area) if element_area else "",
                        "Material:Volume": s(mat_vol) if mat_vol else "",
                    }
                )

        elif rel_mat.is_a("IfcMaterialLayerSet"):
            # Common in some footing exports where Usage wrapper is absent.
            for layer in getattr(rel_mat, "MaterialLayers", []) or []:
                mat = layer.Material
                if not mat:
                    continue
                thickness_model = float(layer.LayerThickness or 0.0)
                thickness_m = thickness_model / 1000.0
                if is_wall_like and element_volume:
                    mat_vol = element_volume
                else:
                    mat_vol = element_area * thickness_m if element_area and thickness_m else 0.0
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(element_area) if element_area else "",
                        "Material:Volume": s(mat_vol) if mat_vol else "",
                    }
                )

        elif rel_mat.is_a("IfcMaterialList"):
            # Legacy/alternate representation.
            for mat in getattr(rel_mat, "Materials", []) or []:
                if not mat:
                    continue
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(element_area) if element_area else "",
                        "Material:Volume": s(element_volume) if element_volume else "",
                    }
                )

        elif rel_mat.is_a("IfcMaterialConstituentSet"):
            for constituent in getattr(rel_mat, "MaterialConstituents", []) or []:
                mat = constituent.Material
                if not mat:
                    continue
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(element_area) if element_area else "",
                        "Material:Volume": s(element_volume) if (is_wall_like and element_volume) else "",
                    }
                )

    return rows


def get_rcc_elements(model) -> List:
    classes = [
        "IfcColumn",
        "IfcSlab",
        "IfcBeam",
        "IfcFooting",
        "IfcWall",
        "IfcWallStandardCase",
        "IfcMember",
        "IfcRamp",
    ]
    out = []
    for cls in classes:
        out.extend(model.by_type(cls))
    return list({e.id(): e for e in out}.values())


def build_rows(model) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    material_desc_index = build_material_description_index(model)
    seen_lift_global_ids = set()
    for element in get_rcc_elements(model):
        name = s(getattr(element, "Name", ""))
        global_id = s(getattr(element, "GlobalId", "")).strip()
        family, type_name = get_family_type(element, name)
        level = get_level(element)
        element_desc = get_element_description(element)
        structural_material = get_structural_material_label(element)
        extra_type_hints = []
        extra_type_hints.extend(get_pset_values(element, "Original Type"))
        extra_type_hints.extend(get_pset_values(element, "Family and Type"))
        if is_excluded_rcc_component(name, family, type_name, element_desc, " ".join(extra_type_hints)):
            continue

        qto = get_quantities(element)
        element_area, element_area_source = pick_material_area_with_source(qto, s(element.is_a()))
        # Volume rule:
        # - Lift wall: use ONLY explicit Volume; ignore rows without Volume
        #   to avoid GrossVolume-based repetition.
        # - Others: NetVolume -> Volume -> GrossVolume fallback.
        lift_hints = []
        lift_hints.extend([name, family, type_name])
        lift_hints.extend(get_pset_values(element, "Type"))
        lift_hints.extend(get_pset_values(element, "Original Type"))
        lift_hints.extend(get_pset_values(element, "Family and Type"))
        lift_hints.extend(get_pset_values(element, "Reference"))
        is_lift_wall = "lift wall" in " ".join(s(x) for x in lift_hints).lower()
        level_l = level.lower()

        if is_lift_wall:
            # Exclude lift-wall quantities from parapet/roof levels.
            if ("parapet" in level_l) or ("roof" in level_l):
                continue
            element_volume = to_float(qto["Volume"])
            if element_volume <= 0:
                continue
            # Some IFC exports duplicate the same Lift Wall element with the
            # same GlobalId but slightly different quantity payloads.
            # For Lift Wall, keep only one row per GlobalId.
            if global_id:
                if global_id in seen_lift_global_ids:
                    continue
                seen_lift_global_ids.add(global_id)
        else:
            element_volume = to_float(qto["NetVolume"] or qto["Volume"] or qto["GrossVolume"])

        material_rows = get_material_rows(element, element_area, element_volume)
        if not material_rows:
            # Keep RCC elements even when explicit material association is absent
            # (common in some footing exports).
            if not (
                is_rcc_text(name)
                or is_rcc_text(family)
                or is_rcc_text(type_name)
                or is_rcc_text(element_desc)
                or is_rcc_text(structural_material)
            ):
                continue
            inferred_name = structural_material or infer_rcc_material_name(name, family, type_name, element_desc)
            inferred_desc = (
                material_desc_index.get(inferred_name, "")
                or element_desc
            )
            material_rows = [
                {
                    "Material:Name": inferred_name,
                    "Material:Description": inferred_desc,
                    "Material:Area": s(element_area) if element_area else "",
                    "Material:Volume": s(element_volume) if element_volume else "",
                }
            ]

        # Prefer richer RCC-oriented text between element and material descriptions.
        def _desc_score(text: str) -> Tuple[int, int, int]:
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

        candidates: List[Dict[str, str]] = []
        for mat in material_rows:
            mat_name = s(mat.get("Material:Name", "")).strip()
            mat_desc = s(mat.get("Material:Description", "")).strip()
            mat_vol = s(mat.get("Material:Volume", "")).strip()

            if structural_material and (not mat_name or mat_name.lower() in ("<unnamed>", "unnamed", "rcc")):
                mat_name = structural_material

            indexed_desc = material_desc_index.get(mat_name, "")
            final_desc = max([element_desc, mat_desc, indexed_desc], key=_desc_score)

            if not (
                is_rcc_text(mat_name)
                or is_rcc_text(final_desc)
                or is_rcc_text(family)
                or is_rcc_text(type_name)
                or is_rcc_text(name)
            ):
                continue

            candidates.append(
                {
                    "Material:Name": mat_name,
                    "Material:Description": final_desc,
                    "Material:Volume": mat_vol,
                }
            )

        if not candidates:
            continue

        def _candidate_score(c: Dict[str, str]) -> Tuple[int, int, int, int, int]:
            mat_name = s(c.get("Material:Name", "")).strip()
            mat_desc = s(c.get("Material:Description", "")).strip()
            mat_vol = to_float(s(c.get("Material:Volume", "")))
            name_l = mat_name.lower()
            structural_match = int(bool(structural_material) and name_l == structural_material.lower())
            has_grade = int(bool(re.search(r"\bm\s*[0-9]{2}\b", name_l)))
            has_rcc_name = int("rcc" in name_l)
            has_vol = int(mat_vol > 0)
            desc_rank = _desc_score(mat_desc)[0]
            return (structural_match, has_grade, has_rcc_name, desc_rank, has_vol)

        best = max(candidates, key=_candidate_score)
        best_mat_vol = s(best.get("Material:Volume", "")).strip()
        if not best_mat_vol and element_volume > 0:
            best_mat_vol = s(element_volume)

        rows.append(
            {
                "ExpressId": s(element.id()),
                "GlobalId": global_id,
                "Family": family,
                "Type": type_name,
                "Level": level,
                "Material:Name": s(best.get("Material:Name", "")),
                "Material:Description": s(best.get("Material:Description", "")),
                "Volume": s(element_volume) if element_volume else "",
                "Material:Volume": best_mat_vol,
            }
        )

    return rows


def write_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "ExpressId",
        "GlobalId",
        "Family",
        "Type",
        "Level",
        "Material:Name",
        "Material:Description",
        "Volume",
        "Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # Detailed summary with family + type + material + description,
    # then a final grand total row.
    grouped: Dict[Tuple[str, str, str, str], Dict[str, object]] = {}

    for row in rows:
        family = s(row.get("Family", "")).strip() or "(Blank)"
        type_name = s(row.get("Type", "")).strip() or "(Blank)"
        mat_name = s(row.get("Material:Name", "")).strip() or "(Blank)"
        mat_desc = s(row.get("Material:Description", "")).strip()
        eid = s(row.get("ExpressId", "")).strip()
        key = (family, type_name, mat_name, mat_desc)

        if key not in grouped:
            grouped[key] = {
                "mat": 0.0,
                "elements": {},  # eid -> volume
            }

        grouped[key]["mat"] = float(grouped[key]["mat"]) + to_float(s(row.get("Material:Volume", "")))
        elements = grouped[key]["elements"]
        if eid and eid not in elements:
            elements[eid] = to_float(s(row.get("Volume", "")))

    out: List[Dict[str, str]] = []
    total_count = total_volume = total_mat = 0.0

    for key in sorted(grouped.keys()):
        family, type_name, mat_name, mat_desc = key
        vals = grouped[key]
        elements = vals["elements"]
        cnt = float(len(elements))
        volume = float(sum(elements.values()))
        mat = float(vals["mat"])

        total_count += cnt
        total_volume += volume
        total_mat += mat

        out.append(
            {
                "Family": family,
                "Type": type_name,
                "Material:Name": mat_name,
                "Material:Description": mat_desc,
                "Occurrence Count": str(int(cnt)),
                "Total Volume": s(volume),
                "Total Material:Volume": s(mat),
            }
        )

    out.append(
        {
            "Family": "GRAND TOTAL",
            "Type": "",
            "Material:Name": "",
            "Material:Description": "",
            "Occurrence Count": str(int(total_count)),
            "Total Volume": s(total_volume),
            "Total Material:Volume": s(total_mat),
        }
    )
    return out


def build_family_type_description_catalog(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str, str], Dict[str, float]] = {}
    for row in rows:
        family = s(row.get("Family", "")).strip()
        type_name = s(row.get("Type", "")).strip()
        mat_name = s(row.get("Material:Name", "")).strip()
        mat_desc = s(row.get("Material:Description", "")).strip()
        key = (family, type_name, mat_name, mat_desc)
        if key not in grouped:
            grouped[key] = {"count": 0.0, "volume": 0.0, "net": 0.0, "gross": 0.0, "raw": 0.0}
        grouped[key]["count"] += 1.0
        grouped[key]["volume"] += to_float(s(row.get("Material:Volume", "")))
        grouped[key]["net"] += to_float(s(row.get("NetVolume", "")))
        grouped[key]["gross"] += to_float(s(row.get("GrossVolume", "")))
        grouped[key]["raw"] += to_float(s(row.get("Volume", "")))

    out: List[Dict[str, str]] = []
    for (family, type_name, mat_name, mat_desc), vals in sorted(
        grouped.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3])
    ):
        out.append(
            {
                "Family": family,
                "Type": type_name,
                "Material:Name": mat_name,
                "Material:Description": mat_desc,
                "Occurrence Count": str(int(vals["count"])),
                "Total NetVolume": s(vals["net"]),
                "Total GrossVolume": s(vals["gross"]),
                "Total Volume": s(vals["raw"]),
                "Total Material:Volume": s(vals["volume"]),
            }
        )
    return out


def build_family_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[str, Dict[str, float]] = {}
    for row in rows:
        family = s(row.get("Family", "")).strip()
        if not family:
            family = "(Blank)"
        if family not in grouped:
            grouped[family] = {
                "count": 0.0,
                "net": 0.0,
                "gross": 0.0,
                "raw": 0.0,
                "mat": 0.0,
            }
        grouped[family]["count"] += 1.0
        grouped[family]["net"] += to_float(s(row.get("NetVolume", "")))
        grouped[family]["gross"] += to_float(s(row.get("GrossVolume", "")))
        grouped[family]["raw"] += to_float(s(row.get("Volume", "")))
        grouped[family]["mat"] += to_float(s(row.get("Material:Volume", "")))

    out: List[Dict[str, str]] = []
    for family in sorted(grouped.keys()):
        vals = grouped[family]
        out.append(
            {
                "Family": family,
                "Occurrence Count": str(int(vals["count"])),
                "Total NetVolume": s(vals["net"]),
                "Total GrossVolume": s(vals["gross"]),
                "Total Volume": s(vals["raw"]),
                "Total Material:Volume": s(vals["mat"]),
            }
        )
    return out


def write_summary_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Occurrence Count",
        "Total Volume",
        "Total Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_family_summary_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Family",
        "Occurrence Count",
        "Total NetVolume",
        "Total GrossVolume",
        "Total Volume",
        "Total Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_family_type_catalog_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Occurrence Count",
        "Total NetVolume",
        "Total GrossVolume",
        "Total Volume",
        "Total Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_volume_check_totals(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    # Check totals once per element to avoid multiplying element volumes by material rows.
    by_element: Dict[str, Dict[str, float]] = {}
    for row in rows:
        eid = s(row.get("ExpressId", "")).strip()
        if not eid:
            continue
        if eid not in by_element:
            by_element[eid] = {
                "net": to_float(s(row.get("NetVolume", ""))),
                "gross": to_float(s(row.get("GrossVolume", ""))),
                "raw": to_float(s(row.get("Volume", ""))),
            }

    total_net = sum(v["net"] for v in by_element.values())
    total_gross = sum(v["gross"] for v in by_element.values())
    total_raw = sum(v["raw"] for v in by_element.values())
    total_mat = sum(to_float(s(r.get("Material:Volume", ""))) for r in rows)

    return [
        {
            "Distinct Element Count": str(len(by_element)),
            "Sum NetVolume": s(total_net),
            "Sum GrossVolume": s(total_gross),
            "Sum Volume": s(total_raw),
            "Sum Material:Volume": s(total_mat),
        }
    ]


def write_volume_check_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Distinct Element Count",
        "Sum NetVolume",
        "Sum GrossVolume",
        "Sum Volume",
        "Sum Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    model = ifcopenshell.open(get_ifc_file())
    detail_rows = build_rows(model)
    if not detail_rows:
        print("No RCC elements found using current filters.")

    detail_path = os.path.join(get_script_dir(), "RCC_sheet.csv")
    summary_path = os.path.join(get_script_dir(), "RCC_Summary.csv")

    write_csv(detail_rows, detail_path)
    summary_rows = build_summary(detail_rows)
    write_summary_csv(summary_rows, summary_path)

    print(f"Created {detail_path} with {len(detail_rows)} rows.")
    print(f"Created {summary_path} with {len(summary_rows)} rows.")


if __name__ == "__main__":
    main()
