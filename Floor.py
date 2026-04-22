import csv
import os
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


def get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_ifc_file() -> str:
    path = os.path.join(get_script_dir(), "finally.ifc")
    if not os.path.exists(path):
        raise SystemExit("finally.ifc not found in script directory.")
    return path


def get_pset_values(element, property_name: str) -> List[str]:
    out: List[str] = []
    seen = set()

    def _push(v: str) -> None:
        vv = s(v).strip()
        if not vv:
            return
        key = vv.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(vv)

    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef and pdef.is_a("IfcPropertySet"):
                for prop in pdef.HasProperties or []:
                    if (
                        prop.is_a("IfcPropertySingleValue")
                        and s(prop.Name).strip().lower() == property_name.strip().lower()
                    ):
                        _push(s(unwrap(prop.NominalValue)))

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
                        _push(s(unwrap(prop.NominalValue)))
    return out


def get_pset_value(element, property_name: str) -> str:
    vals = get_pset_values(element, property_name)
    return vals[0] if vals else ""


def get_level(element) -> str:
    for rel in getattr(element, "ContainedInStructure", []) or []:
        st = getattr(rel, "RelatingStructure", None)
        if st and st.is_a("IfcBuildingStorey"):
            return s(getattr(st, "Name", ""))
    return get_pset_value(element, "Base Constraint")


def split_family_type(name: str) -> Tuple[str, str]:
    if ":" in name:
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    return name.strip(), ""


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


def get_element_description(element) -> str:
    # Prefer explicit flooring spec text from IFC Psets over generic descriptions.
    candidates: List[Tuple[str, str]] = []
    for prop_name in ("Description", "Type Comments", "Assembly Description", "Comments", "Original Type"):
        for val in get_pset_values(element, prop_name):
            candidates.append((prop_name, val))

    native_desc = s(getattr(element, "Description", "")).strip()
    if native_desc:
        candidates.append(("NativeDescription", native_desc))

    if not candidates:
        return ""

    def _score(item: Tuple[str, str]) -> Tuple[int, int, int]:
        src, text = item
        t = s(text).strip().lower()
        # High-priority explicit flooring sentences.
        has_flooring_sentence = int(
            any(k in t for k in ("flooring finished", "ceramic tiles", "vitrified tiles", "marble flooring", "granite flooring"))
        )
        has_flooring_keyword = int(is_flooring_text(t))
        # De-prioritize generic strings.
        is_generic = int(any(k in t for k in ("basic structural asset", "structural asset")))
        src_priority = 1 if src == "Description" else 0
        return (has_flooring_sentence, src_priority + has_flooring_keyword, -is_generic, len(t))

    return max(candidates, key=_score)[1]


def get_quantities(element) -> Dict[str, str]:
    out = {
        "NetArea": "",
        "GrossArea": "",
        "Area": "",
        "GrossFootprintArea": "",
        "NetSideArea": "",
        "GrossSideArea": "",
        "CrossSectionArea": "",
        "OuterSurfaceArea": "",
        "NetVolume": "",
        "GrossVolume": "",
        "Volume": "",
        "_AnyArea": "",
        "_AnyVolume": "",
        "_AnyLength": "",
        "_AnyWidth": "",
    }
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcElementQuantity"):
            continue
        for q in pdef.Quantities or []:
            name = s(getattr(q, "Name", ""))
            if q.is_a("IfcQuantityArea"):
                val = s(getattr(q, "AreaValue", ""))
                if name in out:
                    out[name] = val
                if not out["_AnyArea"] and s(val).strip():
                    out["_AnyArea"] = val
            elif q.is_a("IfcQuantityVolume"):
                val = s(getattr(q, "VolumeValue", ""))
                if name in out:
                    out[name] = val
                if not out["_AnyVolume"] and s(val).strip():
                    out["_AnyVolume"] = val
            elif q.is_a("IfcQuantityLength"):
                val = s(getattr(q, "LengthValue", ""))
                lname = name.strip().lower()
                if (not out["_AnyLength"]) and (
                    "length" in lname or lname in ("l", "len")
                ) and s(val).strip():
                    out["_AnyLength"] = val
                if (not out["_AnyWidth"]) and (
                    "width" in lname
                    or "breadth" in lname
                    or lname in ("w", "b")
                ) and s(val).strip():
                    out["_AnyWidth"] = val

    if not out["Area"]:
        out["Area"] = (
            get_pset_value(element, "Area")
            or get_pset_value(element, "Net Area")
            or get_pset_value(element, "Gross Area")
            or get_pset_value(element, "Projected Area")
            or get_pset_value(element, "Host Area Computed")
            or get_pset_value(element, "Net Side Area")
            or get_pset_value(element, "Gross Side Area")
            or get_pset_value(element, "Top Area")
            or get_pset_value(element, "Bottom Area")
            or out["_AnyArea"]
        )
    if not out["Volume"]:
        out["Volume"] = (
            get_pset_value(element, "Volume")
            or get_pset_value(element, "Net Volume")
            or get_pset_value(element, "Gross Volume")
            or out["_AnyVolume"]
        )
    return out


def pick_area(qto: Dict[str, str]) -> float:
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
    # Fallback for elements that expose only length/width quantities.
    l = to_float(s(qto.get("_AnyLength", "")))
    w = to_float(s(qto.get("_AnyWidth", "")))
    if l > 0.0 and w > 0.0:
        return l * w
    return 0.0


def pick_volume(qto: Dict[str, str]) -> float:
    for key in ("NetVolume", "GrossVolume", "Volume", "_AnyVolume"):
        if s(qto.get(key, "")).strip():
            return to_float(qto[key])
    return 0.0


def get_material_description(material) -> str:
    candidates: List[Tuple[str, str]] = []

    direct = s(getattr(material, "Description", "")).strip()
    if direct:
        candidates.append(("material.description", direct))

    for prop_set in getattr(material, "HasProperties", []) or []:
        pset_name = s(getattr(prop_set, "Name", "")).strip().lower()
        props = getattr(prop_set, "Properties", None) or getattr(
            prop_set, "ExtendedProperties", None
        )
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

        # Prefer useful finish specs.
        has_flooring_phrase = int(
            any(
                k in t
                for k in (
                    "flooring finished",
                    "finished with",
                    "ceramic tile",
                    "ceramic tiles",
                    "vitrified",
                    "vitified",
                    "marble",
                    "granite",
                    "skirting",
                )
            )
        )
        # Prefer identity-data level description over structural note.
        src_priority = int("identity" in src or "type comments" in src)
        # Penalize generic filler.
        generic_penalty = -int(
            any(k in t for k in ("basic structural asset", "structural asset"))
        )
        return (has_flooring_phrase, src_priority, generic_penalty)

    return max(candidates, key=_score)[1]


def get_material_rows(element, area: float, volume: float) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for rel in getattr(element, "HasAssociations", []) or []:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        rel_mat = rel.RelatingMaterial
        if not rel_mat:
            continue

        if rel_mat.is_a("IfcMaterial"):
            rows.append(
                {
                    "Material:Name": s(rel_mat.Name),
                    "Material:Description": get_material_description(rel_mat),
                    "Material:Area": s(area) if area else "",
                    "Material:Volume": s(volume) if volume else "",
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
                mat_vol = area * thickness_m if area and thickness_m else 0.0
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(area) if area else "",
                        "Material:Volume": s(mat_vol) if mat_vol else "",
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
                        "Material:Area": s(area) if area else "",
                        "Material:Volume": s(volume) if volume else "",
                    }
                )

    return rows


def get_candidate_elements(model) -> List:
    classes = [
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
    ]
    out = []
    for cls in classes:
        out.extend(model.by_type(cls))
    return list({e.id(): e for e in out}.values())


def build_rows(model) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for e in get_candidate_elements(model):
        name = s(getattr(e, "Name", ""))
        family_name, type_from_name = split_family_type(name)
        family = get_pset_value(e, "Family") or family_name
        type_name = get_pset_value(e, "Type") or type_from_name
        level = get_level(e)
        element_desc = get_element_description(e)
        qto = get_quantities(e)
        area = pick_area(qto)
        volume = pick_volume(qto)

        mat_rows = get_material_rows(e, area, volume)
        if not mat_rows:
            mat_rows = [
                {
                    "Material:Name": "",
                    "Material:Description": "",
                    "Material:Area": s(area) if area else "",
                    "Material:Volume": s(volume) if volume else "",
                }
            ]

        for mat in mat_rows:
            mat_name = s(mat.get("Material:Name", ""))
            mat_desc = s(mat.get("Material:Description", ""))
            signal = " ".join([name, family, type_name, element_desc, mat_name, mat_desc])
            if not is_flooring_text(signal):
                continue
            if is_rcc_text(signal):
                continue

            # IFC element description is preferred when it clearly describes flooring finish.
            if element_desc and any(k in element_desc.lower() for k in ("flooring finished", "ceramic tiles", "vitrified", "marble", "granite")):
                final_desc = element_desc
            else:
                final_desc = mat_desc or element_desc
            rows.append(
                {
                    "ExpressId": s(e.id()),
                    "GlobalId": s(getattr(e, "GlobalId", "")),
                    "IfcClass": s(e.is_a()),
                    "Family": family,
                    "Type": type_name,
                    "Level": level,
                    "Material:Name": mat_name,
                    "Material:Description": final_desc,
                    "Material:Area": mat.get("Material:Area", ""),
                    "Material:Volume": mat.get("Material:Volume", ""),
                }
            )
    return rows


def write_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "ExpressId",
        "GlobalId",
        "IfcClass",
        "Family",
        "Type",
        "Level",
        "Material:Name",
        "Material:Description",
        "Material:Area",
        "Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str, str], Dict[str, float]] = {}
    for r in rows:
        family = s(r.get("Family", "")).strip()
        type_name = s(r.get("Type", "")).strip()
        mat_name = s(r.get("Material:Name", "")).strip()
        mat_desc = s(r.get("Material:Description", "")).strip()
        key = (family, type_name, mat_name, mat_desc)
        if key not in grouped:
            grouped[key] = {"area": 0.0, "volume": 0.0}
        grouped[key]["area"] += to_float(s(r.get("Material:Area", "")))
        grouped[key]["volume"] += to_float(s(r.get("Material:Volume", "")))

    out: List[Dict[str, str]] = []
    for (family, type_name, name, desc), vals in sorted(
        grouped.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3])
    ):
        out.append(
            {
                "Family": family,
                "Type": type_name,
                "Material:Name": name,
                "Material:Description": desc,
                "Total Material:Area": s(vals["area"]),
                "Total Material:Volume": s(vals["volume"]),
            }
        )
    return out


def write_summary_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Total Material:Area",
        "Total Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    model = ifcopenshell.open(get_ifc_file())
    detail_rows = build_rows(model)
    if not detail_rows:
        print("No flooring records found (tile/marble/granite keywords).")

    detail_path = os.path.join(get_script_dir(), "Floor_Sheet.csv")
    summary_path = os.path.join(get_script_dir(), "Floor_Summary.csv")

    write_csv(detail_rows, detail_path)
    summary_rows = build_summary(detail_rows)
    write_summary_csv(summary_rows, summary_path)

    print(f"Created {detail_path} with {len(detail_rows)} rows.")
    print(f"Created {summary_path} with {len(summary_rows)} rows.")


if __name__ == "__main__":
    main()
