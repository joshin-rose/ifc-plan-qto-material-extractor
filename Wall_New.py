import os
import pandas as pd
import numpy as np
import ifcopenshell
import ifcopenshell.geom


def s(x):
    return "" if x is None else str(x)


def script_folder():
    return os.path.dirname(os.path.abspath(__file__))


def find_ifc(folder):
    path = os.path.join(folder, "abc.ifc")
    if not os.path.exists(path):
        raise SystemExit("❌ abc.ifc not found")
    return path


def split_family_type(name):
    if ":" in name:
        parts = name.split(":")
        return parts[0], parts[1]
    return name, ""


# -----------------------------------------------------------
# PROPERTY EXTRACTION
# -----------------------------------------------------------

def get_pset_value(el, propname):

    for rel in getattr(el, "IsDefinedBy", []) or []:

        if rel.is_a("IfcRelDefinesByProperties"):

            pset = rel.RelatingPropertyDefinition

            if pset and pset.is_a("IfcPropertySet"):

                for p in pset.HasProperties:

                    if p.is_a("IfcPropertySingleValue") and p.Name == propname:
                        return s(p.NominalValue.wrappedValue)

    return ""


def get_pset_value_any(el, propname):

    val = get_pset_value(el, propname)

    if val:
        return val

    for pset in getattr(el, "HasPropertySets", []) or []:

        if pset and pset.is_a("IfcPropertySet"):

            for p in pset.HasProperties:

                if p.is_a("IfcPropertySingleValue") and p.Name == propname:
                    return s(p.NominalValue.wrappedValue)

    return ""


# -----------------------------------------------------------
# WALL DESCRIPTION (ROBUST)
# -----------------------------------------------------------

def get_wall_description(wall):

    # 1 direct wall property
    desc = get_pset_value(wall, "Description")

    if desc:
        return desc

    # 2 wall type property
    for rel in getattr(wall, "IsTypedBy", []) or []:

        if rel.is_a("IfcRelDefinesByType"):

            wall_type = rel.RelatingType

            desc = get_pset_value_any(wall_type, "Description")

            if desc:
                return desc

    # 3 fallback
    for rel in getattr(wall, "IsDefinedBy", []) or []:

        if rel.is_a("IfcRelDefinesByType"):

            wall_type = rel.RelatingType

            desc = get_pset_value_any(wall_type, "Description")

            if desc:
                return desc

    return ""


# -----------------------------------------------------------
# QUANTITIES
# -----------------------------------------------------------

def get_qto(el):

    length = width = height = area = volume = None

    for rel in getattr(el, "IsDefinedBy", []) or []:

        if rel.is_a("IfcRelDefinesByProperties"):

            pdef = rel.RelatingPropertyDefinition

            if pdef and pdef.is_a("IfcElementQuantity"):

                for q in pdef.Quantities:

                    if q.is_a("IfcQuantityLength"):

                        if q.Name == "Length":
                            length = getattr(q, "LengthValue", length)

                        elif q.Name == "Width":
                            width = getattr(q, "LengthValue", width)

                        elif q.Name == "Height":
                            height = getattr(q, "LengthValue", height)

                    elif q.is_a("IfcQuantityArea") and q.Name == "NetSideArea":
                        area = getattr(q, "AreaValue", area)

                    elif q.is_a("IfcQuantityVolume") and q.Name == "NetVolume":
                        volume = getattr(q, "VolumeValue", volume)

    return length, width, height, area, volume


# -----------------------------------------------------------
# GEOMETRY DIMENSIONS
# -----------------------------------------------------------

def get_geometry_dims(settings, wall):

    try:

        shape = ifcopenshell.geom.create_shape(settings, wall)

        v = np.array(shape.geometry.verts).reshape(-1, 3)

        mn, mx = v.min(axis=0), v.max(axis=0)

        dx, dy, dz = mx - mn

        return max(dx, dy), min(dx, dy), dz, dx * dy * dz

    except:

        return "", "", "", ""


# -----------------------------------------------------------
# MATERIALS
# -----------------------------------------------------------

def get_materials(model, wall):

    mats = []

    for rel in getattr(wall, "HasAssociations", []) or []:

        if rel.is_a("IfcRelAssociatesMaterial"):

            mat = rel.RelatingMaterial

            if mat.is_a("IfcMaterialLayerSetUsage"):

                ls = mat.ForLayerSet

                for layer in ls.MaterialLayers:

                    name = s(layer.Material.Name)

                    thickness = layer.LayerThickness / 1000 if layer.LayerThickness else 0

                    mats.append((name, thickness))

    return mats


# -----------------------------------------------------------
# STOREY
# -----------------------------------------------------------

def get_storey(el):

    try:

        rels = getattr(el, "ContainedInStructure", None) or []

        for r in rels:

            st = getattr(r, "RelatingStructure", None)

            if st and st.is_a("IfcBuildingStorey"):
                return s(st.Name)

    except:
        pass

    return ""


# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------

def main():

    folder = script_folder()

    model = ifcopenshell.open(find_ifc(folder))

    settings = ifcopenshell.geom.settings()

    settings.set(settings.USE_WORLD_COORDS, True)

    len_to_m = 0.001
    vol_to_m3 = len_to_m ** 3

    walls = model.by_type("IfcWallStandardCase")

    schedule_rows = []
    material_rows = []

    for wall in walls:

        guid = s(getattr(wall, "GlobalId", ""))

        name = s(wall.Name)

        family, typ = split_family_type(name)

        desc = get_wall_description(wall)

        base = get_storey(wall)

        q_len, q_wid, q_ht, q_area, q_vol = get_qto(wall)

        g_len, g_wid, g_ht, g_vol = get_geometry_dims(settings, wall)

        if g_len != "":
            g_len *= len_to_m
        if g_wid != "":
            g_wid *= len_to_m
        if g_ht != "":
            g_ht *= len_to_m
        if g_vol != "":
            g_vol *= vol_to_m3

        length = (q_len * len_to_m) if q_len else g_len
        width = (q_wid * len_to_m) if q_wid else g_wid
        height = (q_ht * len_to_m) if q_ht else g_ht

        area = q_area or (length * width if length and width else "")

        volume = q_vol or g_vol

        schedule_rows.append(
            [guid, family, typ, desc, base, length, width, height, volume, area]
        )

        mats = get_materials(model, wall)

        for mname, thick in mats:

            mat_area = area

            mat_vol = (area * thick) if area and thick else ""

            material_rows.append(
                [guid, family, typ, mname, desc, base, length, height, thick, mat_area, mat_vol]
            )

    df_schedule = pd.DataFrame(
        schedule_rows,
        columns=[
            "GlobalId",
            "Family",
            "Type",
            "Description",
            "Base Constraint",
            "Length",
            "Width",
            "Height",
            "Volume",
            "Area",
        ],
    )

    df_material = pd.DataFrame(
        material_rows,
        columns=[
            "GlobalId",
            "Family",
            "Type",
            "Material: Name",
            "Material: Description",
            "Base Constraint",
            "Length",
            "Height",
            "Thickness",
            "Material: Area",
            "Material: Volume",
        ],
    )

    df_schedule = df_schedule.sort_values(by="Type")

    df_material = df_material.sort_values(by="Material: Name")

    schedule_summary = df_schedule.groupby(["Family", "Type"], as_index=False).agg(
        Description=("Description", "first"),
        Total_Count=("GlobalId", "count"),
        Total_Area=("Area", "sum"),
        Total_Volume=("Volume", "sum"),
    )

    material_summary = df_material.groupby("Material: Name", as_index=False).agg(
        {
            "Material: Description": "first",
            "Material: Area": "sum",
            "Material: Volume": "sum",
        }
    )

    output_file = os.path.join(folder, "Wall_Reports_new.xlsx")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

        df_schedule.to_excel(writer, sheet_name="Wall Schedule", index=False)

        schedule_summary.to_excel(
            writer, sheet_name="Wall Schedule Summary", index=False
        )

        df_material.to_excel(writer, sheet_name="Material Takeoff", index=False)

        material_summary.to_excel(
            writer, sheet_name="Material Summary", index=False
        )

    print("✅ Excel report created → Wall_Reports_new.xlsx")


if __name__ == "__main__":
    main()