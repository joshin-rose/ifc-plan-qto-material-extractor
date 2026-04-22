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
    path = os.path.join(get_script_dir(), "final.ifc")
    if not os.path.exists(path):
        raise SystemExit("final.ifc not found in script directory.")
    return path


def split_family_type(name: str) -> Tuple[str, str]:
    if ":" in name:
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    return name.strip(), ""


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


def is_rcc_text(text: str) -> bool:
    t = s(text).strip().lower()
    if not t:
        return False
    keys = ["rcc", "reinforced concrete", "concrete", "m30", "m25", "m20"]
    return any(k in t for k in keys)


def get_material_rows(element, element_area: float, element_volume: float) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
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
                mat_vol = element_area * thickness_m if element_area and thickness_m else 0.0
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(element_area) if element_area else "",
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
                        "Material:Area": s(element_area) if element_area else "",
                        "Material:Volume": "",
                    }
                )

    return rows


def get_rcc_elements(model) -> List:
    classes = [
        "IfcColumn",
        "IfcSlab",
        "IfcBeam",
        "IfcFooting",
        "IfcMember",
        "IfcStair",
        "IfcRamp",
    ]
    out = []
    for cls in classes:
        out.extend(model.by_type(cls))
    return list({e.id(): e for e in out}.values())


def build_rows(model) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for element in get_rcc_elements(model):
        name = s(getattr(element, "Name", ""))
        family_from_name, type_from_name = split_family_type(name)

        family = get_pset_value(element, "Family") or family_from_name
        type_name = get_pset_value(element, "Type") or type_from_name
        level = get_level(element)
        element_desc = get_element_description(element)

        qto = get_quantities(element)
        element_area, element_area_source = pick_material_area_with_source(qto, s(element.is_a()))
        element_volume = to_float(qto["NetVolume"] or qto["GrossVolume"] or qto["Volume"])

        material_rows = get_material_rows(element, element_area, element_volume)
        if not material_rows:
            continue

        for mat in material_rows:
            mat_name = s(mat["Material:Name"])
            mat_desc = s(mat["Material:Description"])
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

            final_desc = max([element_desc, mat_desc], key=_desc_score)

            if not (
                is_rcc_text(mat_name)
                or is_rcc_text(final_desc)
                or is_rcc_text(family)
                or is_rcc_text(type_name)
                or is_rcc_text(name)
            ):
                continue

            rows.append(
                {
                    "ExpressId": s(element.id()),
                    "GlobalId": s(getattr(element, "GlobalId", "")),
                    "Family": family,
                    "Type": type_name,
                    "Level": level,
                    "Material:Name": mat_name,
                    "Material:Description": final_desc,
                    "Material:Volume": mat["Material:Volume"],
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
        "Material:Volume",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[str, float] = {}
    desc_by_name: Dict[str, str] = {}

    for row in rows:
        mat_name = s(row.get("Material:Name", "")).strip()
        if not mat_name:
            continue
        mat_desc = s(row.get("Material:Description", "")).strip()
        if mat_name not in desc_by_name or (not desc_by_name[mat_name] and mat_desc):
            desc_by_name[mat_name] = mat_desc
        if mat_name not in grouped:
            grouped[mat_name] = 0.0
        grouped[mat_name] += to_float(s(row.get("Material:Volume", "")))

    summary = []
    for mat_name in sorted(grouped.keys()):
        summary.append(
            {
                "Material:Name": mat_name,
                "Material:Description": desc_by_name.get(mat_name, ""),
                "Total Material:Volume": s(grouped[mat_name]),
            }
        )
    return summary


def build_family_type_description_catalog(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str, str], Dict[str, float]] = {}
    for row in rows:
        family = s(row.get("Family", "")).strip()
        type_name = s(row.get("Type", "")).strip()
        mat_name = s(row.get("Material:Name", "")).strip()
        mat_desc = s(row.get("Material:Description", "")).strip()
        key = (family, type_name, mat_name, mat_desc)
        if key not in grouped:
            grouped[key] = {"count": 0.0, "volume": 0.0}
        grouped[key]["count"] += 1.0
        grouped[key]["volume"] += to_float(s(row.get("Material:Volume", "")))

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
                "Total Material:Volume": s(vals["volume"]),
            }
        )
    return out


def write_summary_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Material:Name",
        "Material:Description",
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
        print("No RCC elements found using current filters.")

    detail_path = os.path.join(get_script_dir(), "RCC_sheet.csv")
    summary_path = os.path.join(get_script_dir(), "RCC_Summary.csv")
    catalog_path = os.path.join(get_script_dir(), "RCC_Family_Type_Descriptions.csv")

    write_csv(detail_rows, detail_path)
    summary_rows = build_summary(detail_rows)
    write_summary_csv(summary_rows, summary_path)
    catalog_rows = build_family_type_description_catalog(detail_rows)
    write_family_type_catalog_csv(catalog_rows, catalog_path)

    print(f"Created {detail_path} with {len(detail_rows)} rows.")
    print(f"Created {summary_path} with {len(summary_rows)} rows.")
    print(f"Created {catalog_path} with {len(catalog_rows)} rows.")


if __name__ == "__main__":
    main()
