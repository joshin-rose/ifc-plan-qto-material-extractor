import os
from typing import Dict, List, Tuple

import ifcopenshell

import Final_Report


def s(value) -> str:
    return "" if value is None else str(value)


def unwrap(value):
    return getattr(value, "wrappedValue", value)


def to_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def ifc_path() -> str:
    path = os.path.join(script_dir(), "finally.ifc")
    if not os.path.exists(path):
        raise SystemExit("finally.ifc not found in script directory.")
    return path


def _push_unique(out: List[str], seen: set, v) -> None:
    vv = s(unwrap(v)).strip()
    if not vv:
        return
    key = vv.lower()
    if key in seen:
        return
    seen.add(key)
    out.append(vv)


def get_pset_values(element, property_name: str) -> List[str]:
    out: List[str] = []
    seen = set()
    target = property_name.strip().lower()

    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef and pdef.is_a("IfcPropertySet"):
                for prop in pdef.HasProperties or []:
                    if (
                        prop.is_a("IfcPropertySingleValue")
                        and s(prop.Name).strip().lower() == target
                    ):
                        _push_unique(out, seen, prop.NominalValue)

        if rel.is_a("IfcRelDefinesByType"):
            rtype = getattr(rel, "RelatingType", None)
            for pset in getattr(rtype, "HasPropertySets", []) or []:
                if not pset or not pset.is_a("IfcPropertySet"):
                    continue
                for prop in pset.HasProperties or []:
                    if (
                        prop.is_a("IfcPropertySingleValue")
                        and s(prop.Name).strip().lower() == target
                    ):
                        _push_unique(out, seen, prop.NominalValue)

    return out


def get_pset_value(element, property_name: str) -> str:
    vals = get_pset_values(element, property_name)
    return vals[0] if vals else ""


def get_qto_length_values(element) -> Dict[str, float]:
    out = {"Length": 0.0, "Width": 0.0, "Depth": 0.0}

    for rel in getattr(element, "IsDefinedBy", []) or []:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue
        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcElementQuantity"):
            continue
        for q in pdef.Quantities or []:
            if not q.is_a("IfcQuantityLength"):
                continue
            name = s(getattr(q, "Name", "")).strip().lower()
            val = to_float(getattr(q, "LengthValue", 0.0))
            if name == "length":
                out["Length"] = val
            elif name == "width":
                out["Width"] = val
            elif name in ("depth", "foundation thickness", "thickness"):
                out["Depth"] = val

    # Property fallback
    if out["Length"] <= 0:
        out["Length"] = to_float(get_pset_value(element, "Length"))
    if out["Width"] <= 0:
        out["Width"] = to_float(get_pset_value(element, "Width"))
    if out["Depth"] <= 0:
        out["Depth"] = to_float(get_pset_value(element, "Depth"))
    if out["Depth"] <= 0:
        out["Depth"] = to_float(get_pset_value(element, "Foundation Thickness"))

    return out


def get_level(element) -> str:
    for rel in getattr(element, "ContainedInStructure", []) or []:
        st = getattr(rel, "RelatingStructure", None)
        if st and st.is_a("IfcBuildingStorey"):
            return s(getattr(st, "Name", ""))
    return get_pset_value(element, "Level") or get_pset_value(element, "Base Constraint")


def get_family_type(element) -> Tuple[str, str]:
    name = s(getattr(element, "Name", "")).strip()
    fam, typ = "", ""
    if ":" in name:
        p = name.split(":", 1)
        fam, typ = p[0].strip(), p[1].strip()

    family_val = get_pset_value(element, "Family")
    type_val = get_pset_value(element, "Type")
    fat = get_pset_value(element, "Family and Type")

    if fat and ":" in fat:
        ff, tt = fat.split(":", 1)
        fam = family_val or fam or ff.strip()
        typ = type_val or typ or tt.strip()
    else:
        fam = family_val or fam
        typ = type_val or typ

    return fam, typ


def is_rcc_rectangular_footing(element) -> bool:
    family, typ = get_family_type(element)
    fat = get_pset_value(element, "Family and Type")
    signal = " ".join(
        [
            s(getattr(element, "Name", "")),
            family,
            typ,
            fat,
            get_pset_value(element, "Original Type"),
        ]
    ).lower()
    return "rcc rectangular footing" in signal


def build_takeoff_rows(model) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    elements = model.by_type("IfcProduct") or []

    for e in elements:
        if not is_rcc_rectangular_footing(e):
            continue

        lv = get_qto_length_values(e)
        length = lv["Length"]
        width = lv["Width"]
        depth = lv["Depth"]

        elevation_raw = to_float(get_pset_value(e, "Elevation at Top Survey"))
        elevation = abs(elevation_raw)

        family, typ = get_family_type(e)
        level = get_level(e)

        # IFC length values here are in millimetres, so this formula yields mm^3.
        # Convert to m^3 by dividing by 1e9.
        computed_volume_m3 = (length * width * (depth + elevation)) / 1_000_000_000.0

        rows.append(
            {
                "ExpressId": s(e.id()),
                "GlobalId": s(getattr(e, "GlobalId", "")),
                "Family": family,
                "Type": typ,
                "Level": level,
                "Length (mm)": f"{length:.3f}",
                "Width (mm)": f"{width:.3f}",
                "Depth (mm)": f"{depth:.3f}",
                "Elevation (mm)": f"{elevation:.3f}",
                "Material:Name": "Earthwork",
                "Material:Description": "",
                "Computed Volume (m³)": f"{computed_volume_m3:.6f}",
            }
        )

    return rows


def build_summary_rows(takeoff_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    grouped: Dict[Tuple[str, str, str], Dict[str, float]] = {}
    for r in takeoff_rows:
        key = (r.get("Family", ""), r.get("Type", ""), r.get("Level", ""))
        if key not in grouped:
            grouped[key] = {"count": 0.0, "volume": 0.0}
        grouped[key]["count"] += 1.0
        grouped[key]["volume"] += to_float(r.get("Computed Volume (m³)", 0.0))

    out: List[Dict[str, str]] = []
    grand_count = 0.0
    grand_volume = 0.0
    for (family, typ, level), vals in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        grand_count += vals["count"]
        grand_volume += vals["volume"]
        out.append(
            {
                "Family": family,
                "Type": typ,
                "Level": level,
                "Count": str(int(vals["count"])),
                "Material:Name": "Earthwork",
                "Material:Description": "",
                "Total Computed Volume (m³)": f"{vals['volume']:.6f}",
            }
        )

    out.append(
        {
            "Family": "GRAND TOTAL",
            "Type": "",
            "Level": "",
            "Count": str(int(grand_count)),
            "Material:Name": "Earthwork",
            "Material:Description": "",
            "Total Computed Volume (m³)": f"{grand_volume:.6f}",
        }
    )
    return out


def write_takeoff_xlsx(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "ExpressId",
        "GlobalId",
        "Family",
        "Type",
        "Level",
        "Length (mm)",
        "Width (mm)",
        "Depth (mm)",
        "Elevation (mm)",
        "Material:Name",
        "Material:Description",
        "Computed Volume (m³)",
    ]
    sheet_rows = [headers] + [[r.get(h, "") for h in headers] for r in rows]
    Final_Report.build_workbook([("Earthwork_Takeoff", sheet_rows)], out_path)


def write_summary_xlsx(rows: List[Dict[str, str]], out_path: str) -> None:
    headers = [
        "Family",
        "Type",
        "Level",
        "Count",
        "Material:Name",
        "Material:Description",
        "Total Computed Volume (m³)",
    ]
    sheet_rows = [headers] + [[r.get(h, "") for h in headers] for r in rows]
    Final_Report.build_workbook([("Earthwork_Summary", sheet_rows)], out_path)


def main() -> None:
    model = ifcopenshell.open(ifc_path())
    takeoff_rows = build_takeoff_rows(model)
    summary_rows = build_summary_rows(takeoff_rows)

    takeoff_path = os.path.join(script_dir(), "Earthwork_Takeoff.xlsx")
    summary_path = os.path.join(script_dir(), "Earthwork_Summary.xlsx")

    write_takeoff_xlsx(takeoff_rows, takeoff_path)
    write_summary_xlsx(summary_rows, summary_path)

    print(f"Created {takeoff_path} with {len(takeoff_rows)} rows.")
    print(f"Created {summary_path} with {len(summary_rows)} rows.")


if __name__ == "__main__":
    main()
