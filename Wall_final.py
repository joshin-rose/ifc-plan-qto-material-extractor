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
    path = os.path.join(folder, "final.ifc")
    if not os.path.exists(path):
        raise SystemExit("❌ final.ifc not found")
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
# WALL DESCRIPTION
# -----------------------------------------------------------

def get_wall_description(wall):

    desc = get_pset_value(wall, "Description")

    if desc:
        return desc

    for rel in getattr(wall, "IsTypedBy", []) or []:

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

    length = width = height = None
    net_area = gross_area = volume = None

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

                    elif q.is_a("IfcQuantityArea"):

                        if q.Name == "NetSideArea":
                            net_area = getattr(q, "AreaValue", net_area)

                        elif q.Name in ["GrossSideArea", "GrossArea"]:
                            gross_area = getattr(q, "AreaValue", gross_area)

                    elif q.is_a("IfcQuantityVolume") and q.Name == "NetVolume":
                        volume = getattr(q, "VolumeValue", volume)

    return length, width, height, net_area, gross_area, volume


# -----------------------------------------------------------
# GEOMETRY
# -----------------------------------------------------------

def get_geometry_dims(settings, wall):

    try:

        shape = ifcopenshell.geom.create_shape(settings, wall)

        v = np.array(shape.geometry.verts).reshape(-1, 3)

        mn, mx = v.min(axis=0), v.max(axis=0)

        dx, dy, dz = mx - mn

        return max(dx, dy), min(dx, dy), dz, dx * dy * dz

    except:

        return None, None, None, None


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
    area_to_m2 = len_to_m ** 2
    vol_to_m3 = len_to_m ** 3

    walls = list(set(model.by_type("IfcWall")))

    print("Wall count:", len(walls))

    schedule_rows = []
    material_rows = []

    for wall in walls:

        guid = s(getattr(wall, "GlobalId", ""))

        name = s(wall.Name)

        family, typ = split_family_type(name)

        desc = get_wall_description(wall)

        base = get_storey(wall)

        q_len, q_wid, q_ht, q_net_area, q_gross_area, q_vol = get_qto(wall)

        g_len, g_wid, g_ht, g_vol = get_geometry_dims(settings, wall)

        length = q_len * len_to_m if q_len is not None else (g_len * len_to_m if g_len else None)
        width = q_wid * len_to_m if q_wid is not None else (g_wid * len_to_m if g_wid else None)
        height = q_ht * len_to_m if q_ht is not None else (g_ht * len_to_m if g_ht else None)

        # NetSideArea
        if q_net_area is not None:
            net_area = q_net_area * area_to_m2
        else:
            net_area = length * height if length and height else None

        # GrossSideArea
        if q_gross_area is not None:
            gross_area = q_gross_area * area_to_m2
        else:
            gross_area = None

        volume = q_vol * vol_to_m3 if q_vol is not None else g_vol

        schedule_rows.append([
            guid, family, typ, desc, base,
            length, width, height,
            volume, net_area, gross_area
        ])

        mats = get_materials(model, wall)

        for mname, thick in mats:

            mat_area = net_area
            mat_vol = net_area * thick if net_area and thick else None

            material_rows.append([
                guid, family, typ, mname, desc, base,
                length, height, thick,
                mat_area, mat_vol
            ])

    df_schedule = pd.DataFrame(schedule_rows, columns=[
        "GlobalId", "Family", "Type", "Description",
        "Base Constraint", "Length", "Width",
        "Height", "Volume", "NetSideArea", "GrossSideArea"
    ])

    df_material = pd.DataFrame(material_rows, columns=[
        "GlobalId", "Family", "Type",
        "Material: Name", "Material: Description",
        "Base Constraint", "Length", "Height",
        "Thickness", "Material: Area", "Material: Volume"
    ])

    # ---------------- SUMMARY ----------------

    schedule_summary = df_schedule.groupby(["Family", "Type"], as_index=False).agg(
        Description=("Description", "first"),
        Total_Count=("GlobalId", "count"),
        Total_NetSideArea=("NetSideArea", "sum"),
        Total_GrossSideArea=("GrossSideArea", "sum"),
        Total_Volume=("Volume", "sum"),
    )

    material_summary = df_material.groupby("Material: Name", as_index=False).agg({
        "Material: Description": "first",
        "Material: Area": "sum",
        "Material: Volume": "sum",
    })

    output_file = os.path.join(folder, "Wall_Reports_final.xlsx")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

        df_schedule.to_excel(writer, sheet_name="Wall Schedule", index=False)

        schedule_summary.to_excel(
            writer, sheet_name="Wall Schedule Summary", index=False
        )

        df_material.to_excel(writer, sheet_name="Material Takeoff", index=False)

        material_summary.to_excel(
            writer, sheet_name="Material Summary", index=False
        )

    print("✅ Excel report created → Wall_Reports_final.xlsx")


if __name__ == "__main__":
    main()