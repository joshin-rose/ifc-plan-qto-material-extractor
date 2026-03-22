import csv
import os
from typing import Dict, List, Tuple

import ifcopenshell


def s(value) -> str:
    return "" if value is None else str(value)


def unwrap(value):
    return getattr(value, "wrappedValue", value)


def get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_ifc_file() -> str:
    path = os.path.join(get_script_dir(), "final.ifc")
    if not os.path.exists(path):
        raise SystemExit("final.ifc not found in script directory.")
    return path


def get_wall_entities(model) -> List:
    walls = model.by_type("IfcWall") + model.by_type("IfcWallStandardCase")
    return list({w.id(): w for w in walls}.values())


def split_family_type(name: str) -> Tuple[str, str]:
    if ":" in name:
        parts = name.split(":")
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
    return name.strip(), ""


def get_pset_value(element, property_name: str) -> str:
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcPropertySet"):
            continue
        for prop in pdef.HasProperties or []:
            if prop.is_a("IfcPropertySingleValue") and prop.Name == property_name:
                return s(unwrap(prop.NominalValue))
    return ""


def get_wall_quantities(element) -> Dict[str, str]:
    out = {
        "Length": "",
        "Width": "",
        "Height": "",
        "GrossFootprintArea": "",
        "NetSideArea": "",
        "GrossSideArea": "",
        "NetVolume": "",
        "GrossVolume": "",
    }
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcElementQuantity"):
            continue
        for q in pdef.Quantities or []:
            if q.is_a("IfcQuantityLength") and q.Name in ("Length", "Width", "Height"):
                out[q.Name] = s(getattr(q, "LengthValue", ""))
            elif q.is_a("IfcQuantityArea") and q.Name in ("GrossFootprintArea", "NetSideArea", "GrossSideArea"):
                out[q.Name] = s(getattr(q, "AreaValue", ""))
            elif q.is_a("IfcQuantityVolume") and q.Name in ("NetVolume", "GrossVolume"):
                out[q.Name] = s(getattr(q, "VolumeValue", ""))
    return out


def get_material_description(material) -> str:
    direct = s(getattr(material, "Description", ""))
    if direct:
        return direct

    for prop_set in getattr(material, "HasProperties", []) or []:
        props = getattr(prop_set, "Properties", None) or getattr(prop_set, "ExtendedProperties", None)
        for prop in props or []:
            if prop.is_a("IfcPropertySingleValue") and prop.Name == "Description":
                return s(unwrap(prop.NominalValue))
    return ""


def get_material_rows(wall, wall_area: float, wall_volume: float) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    for rel in getattr(wall, "HasAssociations", []) or []:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue

        rel_mat = rel.RelatingMaterial
        if not rel_mat:
            continue

        if rel_mat.is_a("IfcMaterial"):
            mat_name = s(rel_mat.Name)
            mat_desc = get_material_description(rel_mat)
            rows.append(
                {
                    "Material:Name": mat_name,
                    "Material:Description": mat_desc,
                    "Material:Area": s(wall_area) if wall_area else "",
                    "Material:Volume": s(wall_volume) if wall_volume else "",
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
                mat_vol = wall_area * thickness_m if wall_area and thickness_m else 0.0
                rows.append(
                    {
                        "Material:Name": s(mat.Name),
                        "Material:Description": get_material_description(mat),
                        "Material:Area": s(wall_area) if wall_area else "",
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
                        "Material:Area": s(wall_area) if wall_area else "",
                        "Material:Volume": "",
                    }
                )

    if not rows:
        rows.append(
            {
                "Material:Name": "",
                "Material:Description": "",
                "Material:Area": s(wall_area) if wall_area else "",
                "Material:Volume": s(wall_volume) if wall_volume else "",
            }
        )

    return rows


def build_rows(model) -> List[Dict[str, str]]:
    out_rows: List[Dict[str, str]] = []

    for wall in get_wall_entities(model):
        wall_name = s(getattr(wall, "Name", ""))
        family, type_name_from_name = split_family_type(wall_name)

        family_val = get_pset_value(wall, "Family") or family
        type_val = get_pset_value(wall, "Type") or type_name_from_name
        base_constraint = get_pset_value(wall, "Base Constraint")

        qto = get_wall_quantities(wall)

        length_val = get_pset_value(wall, "Length") or qto["Length"]
        width_val = get_pset_value(wall, "Width") or qto["Width"]
        area_val = get_pset_value(wall, "Area")
        volume_val = get_pset_value(wall, "Volume")

        wall_area = to_float(qto["NetSideArea"] or qto["GrossSideArea"] or area_val)
        wall_volume = to_float(qto["NetVolume"] or qto["GrossVolume"] or volume_val)
        mat_rows = get_material_rows(wall, wall_area, wall_volume)

        for mat in mat_rows:
            out_rows.append(
                {
                    "ExpressId": s(wall.id()),
                    "GlobalId": s(getattr(wall, "GlobalId", "")),
                    "Family": family_val,
                    "Type": type_val,
                    "Base Constraint": base_constraint,
                    "Length": length_val,
                    "Width": width_val,
                    "Material:Name": mat["Material:Name"],
                    "Material:Description": mat["Material:Description"],
                    "Material:Area": mat["Material:Area"],
                    "Material:Volume": mat["Material:Volume"],
                }
            )

    return out_rows


def write_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    if not rows:
        raise SystemExit("No wall data found in final.ifc.")

    headers = [
        "ExpressId",
        "GlobalId",
        "Family",
        "Type",
        "Base Constraint",
        "Length",
        "Width",
        "Material:Name",
        "Material:Description",
        "Material:Area",
        "Material:Volume",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def build_material_summary(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[str, Dict[str, float]] = {}
    desc_by_name: Dict[str, str] = {}

    for row in rows:
        mat_name = s(row.get("Material:Name", "")).strip()
        if not mat_name:
            continue

        mat_desc = s(row.get("Material:Description", "")).strip()
        if mat_name not in desc_by_name or (not desc_by_name[mat_name] and mat_desc):
            desc_by_name[mat_name] = mat_desc

        if mat_name not in grouped:
            grouped[mat_name] = {"material_area": 0.0, "material_volume": 0.0}

        grouped[mat_name]["material_area"] += to_float(s(row.get("Material:Area", "")))
        grouped[mat_name]["material_volume"] += to_float(s(row.get("Material:Volume", "")))

    summary_rows: List[Dict[str, str]] = []
    for mat_name in sorted(grouped.keys()):
        summary_rows.append(
            {
                "Material:Name": mat_name,
                "Material:Description": desc_by_name.get(mat_name, ""),
                "Total Material:Area": s(grouped[mat_name]["material_area"]),
                "Total Material:Volume": s(grouped[mat_name]["material_volume"]),
            }
        )

    return summary_rows


def write_summary_csv(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
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
    rows = build_rows(model)
    details_path = os.path.join(get_script_dir(), "Wall_Sheet.csv")
    write_csv(rows, details_path)

    summary_rows = build_material_summary(rows)
    summary_path = os.path.join(get_script_dir(), "Wall_Sheet_Summary.csv")
    write_summary_csv(summary_rows, summary_path)

    print(f"Created {details_path} with {len(rows)} rows.")
    print(f"Created {summary_path} with {len(summary_rows)} rows.")


if __name__ == "__main__":
    main()
