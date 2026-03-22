import csv
import os
from typing import Dict, List, Optional, Tuple

import ifcopenshell


def s(value) -> str:
    return "" if value is None else str(value)


def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def ifc_path() -> str:
    path = os.path.join(script_dir(), "abcd.ifc")
    if not os.path.exists(path):
        raise SystemExit("abcd.ifc not found in script folder.")
    return path


def unwrap_ifc_value(value):
    if value is None:
        return None
    return getattr(value, "wrappedValue", value)


def get_first_pset_prop(element, prop_name: str) -> str:
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcPropertySet"):
            continue
        for prop in pdef.HasProperties or []:
            if prop.is_a("IfcPropertySingleValue") and prop.Name == prop_name:
                return s(unwrap_ifc_value(prop.NominalValue))
    return ""


def get_qto_values(element) -> Dict[str, str]:
    out = {
        "Length": "",
        "Width": "",
        "Height": "",
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
            q_name = s(getattr(q, "Name", ""))
            if q.is_a("IfcQuantityLength") and q_name in ("Length", "Width", "Height"):
                out[q_name] = s(getattr(q, "LengthValue", ""))
            elif q.is_a("IfcQuantityArea") and q_name in ("NetSideArea", "GrossSideArea"):
                out[q_name] = s(getattr(q, "AreaValue", ""))
            elif q.is_a("IfcQuantityVolume") and q_name in ("NetVolume", "GrossVolume"):
                out[q_name] = s(getattr(q, "VolumeValue", ""))
    return out


def get_storey_name(element) -> str:
    for rel in getattr(element, "ContainedInStructure", []) or []:
        structure = getattr(rel, "RelatingStructure", None)
        if structure and structure.is_a("IfcBuildingStorey"):
            return s(structure.Name)
    return ""


def get_type_info(element) -> Tuple[str, str]:
    for rel in getattr(element, "IsTypedBy", []) or []:
        if rel.is_a("IfcRelDefinesByType"):
            t = rel.RelatingType
            if t:
                return s(getattr(t, "Name", "")), s(getattr(t, "PredefinedType", ""))
    return "", ""


def get_materials(element) -> str:
    names: List[str] = []
    for rel in getattr(element, "HasAssociations", []) or []:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        mat = rel.RelatingMaterial
        if not mat:
            continue
        if mat.is_a("IfcMaterial"):
            names.append(s(mat.Name))
        elif mat.is_a("IfcMaterialLayerSetUsage"):
            layer_set = mat.ForLayerSet
            for layer in getattr(layer_set, "MaterialLayers", []) or []:
                if layer.Material:
                    names.append(s(layer.Material.Name))
        elif mat.is_a("IfcMaterialConstituentSet"):
            for c in getattr(mat, "MaterialConstituents", []) or []:
                if c.Material:
                    names.append(s(c.Material.Name))
        else:
            names.append(s(getattr(mat, "Name", mat.is_a())))
    deduped = [n for n in dict.fromkeys([n for n in names if n])]
    return " | ".join(deduped)


def wall_entities(model) -> List:
    walls = []
    walls.extend(model.by_type("IfcWall"))
    walls.extend(model.by_type("IfcWallStandardCase"))
    unique = {w.id(): w for w in walls}
    return list(unique.values())


def extract_wall_rows(model) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for wall in wall_entities(model):
        qto = get_qto_values(wall)
        type_name, type_predef = get_type_info(wall)
        rows.append(
            {
                "ExpressId": s(wall.id()),
                "GlobalId": s(getattr(wall, "GlobalId", "")),
                "IfcClass": s(wall.is_a()),
                "Name": s(getattr(wall, "Name", "")),
                "ObjectType": s(getattr(wall, "ObjectType", "")),
                "Tag": s(getattr(wall, "Tag", "")),
                "PredefinedType": s(getattr(wall, "PredefinedType", "")),
                "TypeName": type_name,
                "TypePredefinedType": type_predef,
                "Storey": get_storey_name(wall),
                "LoadBearing": get_first_pset_prop(wall, "LoadBearing"),
                "IsExternal": get_first_pset_prop(wall, "IsExternal"),
                "FireRating": get_first_pset_prop(wall, "FireRating"),
                "AcousticRating": get_first_pset_prop(wall, "AcousticRating"),
                "Reference": get_first_pset_prop(wall, "Reference"),
                "Length": qto["Length"],
                "Width": qto["Width"],
                "Height": qto["Height"],
                "NetSideArea": qto["NetSideArea"],
                "GrossSideArea": qto["GrossSideArea"],
                "NetVolume": qto["NetVolume"],
                "GrossVolume": qto["GrossVolume"],
                "Materials": get_materials(wall),
            }
        )
    return rows


def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        raise SystemExit("No wall entities found.")
    headers = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    model = ifcopenshell.open(ifc_path())
    rows = extract_wall_rows(model)
    out_file = os.path.join(script_dir(), "abcd_wall_parameters.csv")
    write_csv(rows, out_file)
    print(f"Extracted {len(rows)} walls to: {out_file}")


if __name__ == "__main__":
    main()
