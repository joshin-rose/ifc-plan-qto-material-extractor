import os
import re
import uuid
import tempfile
import io
import csv
from datetime import date
from pathlib import Path
import html

import ifcopenshell
import mysql.connector
import streamlit as st
import Wall
import RCC
import Floor
import Earthwork
import Final_Report
import shared_extraction


# -----------------------------
# DB CONFIG (env override ready)
# -----------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "architect")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ap@2101")
DB_NAME = os.getenv("DB_NAME", "arch_db")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def get_sor_options():
    query = """
        SELECT sor_code, CONCAT(sor_code, ' - ', state_name, ' (', year, ')') AS label
        FROM sor_data
        ORDER BY sor_code
    """
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()


def safe_filename(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)
    return name.strip("_")


def save_project(payload):
    sql = """
        INSERT INTO project_master
        (
            project_code,
            project_name,
            project_location,
            client_name,
            site_area,
            total_builtup_area,
            building_height,
            date_of_issue,
            estimator_name,
            ifc_file_name,
            sor_database
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            sql,
            (
                payload["project_code"],
                payload["project_name"],
                payload["project_location"],
                payload["client_name"],
                payload["site_area"],
                payload["total_builtup_area"],
                payload["building_height"],
                payload["date_of_issue"],
                payload["estimator_name"],
                payload["ifc_file_name"],
                payload["sor_database"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_work_item_charges():
    query = """
        SELECT id, charge_name, percentage
        FROM work_item_charges
        ORDER BY id
    """
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query)
        return cur.fetchall()
    finally:
        conn.close()


def update_work_item_charges(charges):
    sql = """
        UPDATE work_item_charges
        SET percentage = %s
        WHERE id = %s
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.executemany(sql, [(row["percentage"], row["id"]) for row in charges])
        conn.commit()
    finally:
        conn.close()


def get_project_sor_code(project_code, ifc_file_name):
    query = """
        SELECT sor_database
        FROM project_master
        WHERE project_code = %s AND ifc_file_name = %s
        LIMIT 1
    """
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, (project_code, ifc_file_name))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_or_init_wastage_defaults(sor_code, work_item_codes):
    codes = [str(c or "").strip() for c in (work_item_codes or []) if str(c or "").strip()]
    if not sor_code or not codes:
        return {}

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT INTO work_item_wastage_defaults (sor_code, subpackage_code)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE subpackage_code = VALUES(subpackage_code)
            """,
            [(sor_code, code) for code in codes],
        )

        placeholders = ", ".join(["%s"] * len(codes))
        cur.execute(
            f"""
            SELECT subpackage_code, wastage_percent
            FROM work_item_wastage_defaults
            WHERE sor_code = %s
              AND subpackage_code IN ({placeholders})
            """,
            (sor_code, *codes),
        )
        rows = cur.fetchall()
        conn.commit()
        return {str(code): float(pct if pct is not None else 0.0) for code, pct in rows}
    finally:
        conn.close()


def save_wastage_defaults(sor_code, wastage_map):
    if not sor_code or not wastage_map:
        return

    rows = []
    for code, pct in (wastage_map or {}).items():
        code_s = str(code or "").strip()
        if not code_s:
            continue
        try:
            pct_val = float(pct if pct not in ("", None) else 0.0)
        except Exception:
            pct_val = 0.0
        rows.append((sor_code, code_s, pct_val))

    if not rows:
        return

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT INTO work_item_wastage_defaults (sor_code, subpackage_code, wastage_percent)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wastage_percent = VALUES(wastage_percent),
                updated_at = CURRENT_TIMESTAMP
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def get_subpackage_name_map(sor_code, work_item_codes):
    codes = [str(c or "").strip() for c in (work_item_codes or []) if str(c or "").strip()]
    if not sor_code or not codes:
        return {}

    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(codes))
        cur.execute(
            f"""
            SELECT subpackage_code, subpackage_name
            FROM work_item_subpackage
            WHERE sor_code = %s
              AND subpackage_code IN ({placeholders})
            """,
            (sor_code, *codes),
        )
        rows = cur.fetchall()
        return {
            str(r.get("subpackage_code") or "").strip(): str(r.get("subpackage_name") or "").strip()
            for r in rows
        }
    finally:
        conn.close()


def get_subpackage_description_map(sor_code, work_item_codes):
    codes = [str(c or "").strip() for c in (work_item_codes or []) if str(c or "").strip()]
    if not sor_code or not codes:
        return {}

    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(codes))
        cur.execute(
            f"""
            SELECT subpackage_code, description
            FROM work_item_subpackage
            WHERE sor_code = %s
              AND subpackage_code IN ({placeholders})
            """,
            (sor_code, *codes),
        )
        rows = cur.fetchall()
        return {
            str(r.get("subpackage_code") or "").strip(): str(r.get("description") or "").strip()
            for r in rows
        }
    finally:
        conn.close()


def submit_all(project_payload, file_bytes, original_file_name, charges):
    original_name = safe_filename(original_file_name)
    unique_prefix = uuid.uuid4().hex[:8]
    stored_name = f"{unique_prefix}_{original_name}"
    file_path = UPLOAD_DIR / stored_name

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    payload = dict(project_payload)
    payload["ifc_file_name"] = stored_name

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO project_master
            (
                project_code,
                project_name,
                project_location,
                client_name,
                site_area,
                total_builtup_area,
                building_height,
                date_of_issue,
                estimator_name,
                ifc_file_name,
                sor_database
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload["project_code"],
                payload["project_name"],
                payload["project_location"],
                payload["client_name"],
                payload["site_area"],
                payload["total_builtup_area"],
                payload["building_height"],
                payload["date_of_issue"],
                payload["estimator_name"],
                payload["ifc_file_name"],
                payload["sor_database"],
            ),
        )
        cur.executemany(
            """
            UPDATE work_item_charges
            SET percentage = %s
            WHERE id = %s
            """,
            [(row["percentage"], row["id"]) for row in charges],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    finally:
        conn.close()

    return payload["project_code"], stored_name


def get_material_package_mapping(sor_code):
    query = """
        SELECT s.subpackage_name, p.package_name
        FROM work_item_subpackage s
        JOIN work_item_package p
          ON p.sor_code = s.sor_code
         AND p.package_code = s.package_code
        WHERE s.sor_code = %s
    """
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, (sor_code,))
        return cur.fetchall()
    finally:
        conn.close()


def resolve_package_name(material_name, mappings):
    mat_raw = (material_name or "").strip().lower()
    if not mat_raw:
        return None

    def variants(text):
        t = (text or "").strip().lower()
        if not t:
            return []
        vals = [t, t.replace(",", ":"), t.replace(":", ","), t.replace(", ", ":"), t.replace(": ", ",")]
        out = []
        seen = set()
        for v in vals:
            if v and v not in seen:
                out.append(v)
                seen.add(v)
        return out

    mat_variants = variants(mat_raw)

    # exact first
    for row in mappings:
        sub_variants = variants(row.get("subpackage_name") or "")
        if any(mv == sv for mv in mat_variants for sv in sub_variants):
            return row.get("package_name")

    # then contains either direction
    for row in mappings:
        sub_variants = variants(row.get("subpackage_name") or "")
        if any((sv in mv or mv in sv) for mv in mat_variants for sv in sub_variants):
            return row.get("package_name")

    return None


def persist_project_and_qto(project_payload, file_bytes, original_file_name, charges, existing_ifc_file_name=None):
    if existing_ifc_file_name:
        stored_name = existing_ifc_file_name
    else:
        original_name = safe_filename(original_file_name)
        unique_prefix = uuid.uuid4().hex[:8]
        stored_name = f"{unique_prefix}_{original_name}"
    file_path = UPLOAD_DIR / stored_name

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    payload = dict(project_payload)
    payload["ifc_file_name"] = stored_name
    sor_code = payload["sor_database"]

    try:
        model = ifcopenshell.open(str(file_path))
        wall_rows, rcc_rows, floor_rows = shared_extraction.build_rows(model)
    except Exception:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    mappings = get_material_package_mapping(sor_code)

    masonry_rows = []
    plaster_rows = []
    rcc_takeoff_rows = []

    for row in wall_rows:
        mat_name = row.get("Material:Name", "")
        pkg = resolve_package_name(mat_name, mappings)
        if pkg == "Masonry Work":
            masonry_rows.append(row)
        elif pkg in ("PCC Work", "Plastering Work"):
            plaster_rows.append(row)

    # Add explicit flooring extraction rows so flooring family/type variants
    # extracted by Floor.py are persisted for QTO/export.
    for row in floor_rows:
        plaster_rows.append(
            {
                "ExpressId": row.get("ExpressId", ""),
                "GlobalId": row.get("GlobalId", ""),
                "Family": row.get("Family", ""),
                "Type": row.get("Type", ""),
                "Base Constraint": row.get("Level", ""),
                "Length": "",
                "Width": "",
                "Material:Name": row.get("Material:Name", ""),
                "Material:Description": row.get("Material:Description", ""),
                "Material:Area": row.get("Material:Area", ""),
                "Material:Volume": row.get("Material:Volume", ""),
            }
        )

    # RCC source of truth must come from RCC.py extraction strategy.
    # Do not mix wall-derived RCC rows, otherwise lift-wall volume/description
    # can be overwritten during de-duplication.
    for row in rcc_rows:
        if _is_excluded_rcc_row(
            row.get("Family", ""),
            row.get("Type", ""),
            row.get("Material:Name", ""),
            row.get("Material:Description", ""),
        ):
            continue
        rcc_takeoff_rows.append(row)

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT subpackage_code, subpackage_name, package_code, description
            FROM work_item_subpackage
            WHERE sor_code = %s
            """,
            (sor_code,),
        )
        catalog_rows = [
            {
                "subpackage_code": r[0],
                "subpackage_name": r[1],
                "package_code": r[2],
                "description": r[3],
            }
            for r in (cur.fetchall() or [])
        ]
        # project + charges
        cur.execute(
            """
            INSERT INTO project_master
            (
                project_code,
                project_name,
                project_location,
                client_name,
                site_area,
                total_builtup_area,
                building_height,
                date_of_issue,
                estimator_name,
                ifc_file_name,
                sor_database
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                project_name = VALUES(project_name),
                project_location = VALUES(project_location),
                client_name = VALUES(client_name),
                site_area = VALUES(site_area),
                total_builtup_area = VALUES(total_builtup_area),
                building_height = VALUES(building_height),
                date_of_issue = VALUES(date_of_issue),
                estimator_name = VALUES(estimator_name),
                sor_database = VALUES(sor_database)
            """,
            (
                payload["project_code"],
                payload["project_name"],
                payload["project_location"],
                payload["client_name"],
                payload["site_area"],
                payload["total_builtup_area"],
                payload["building_height"],
                payload["date_of_issue"],
                payload["estimator_name"],
                payload["ifc_file_name"],
                payload["sor_database"],
            ),
        )
        cur.executemany(
            """
            UPDATE work_item_charges
            SET percentage = %s
            WHERE id = %s
            """,
            [(row["percentage"], row["id"]) for row in charges],
        )

        # clear existing entries for this project+ifc
        clear_params = (payload["project_code"], payload["ifc_file_name"])
        cur.execute("DELETE FROM masonry_summary WHERE project_code=%s AND ifc_file_name=%s", clear_params)
        cur.execute("DELETE FROM plastering_summary WHERE project_code=%s AND ifc_file_name=%s", clear_params)
        cur.execute("DELETE FROM rcc_summary WHERE project_code=%s AND ifc_file_name=%s", clear_params)
        cur.execute("DELETE FROM masonry_material_takeoff WHERE project_code=%s AND ifc_file_name=%s", clear_params)
        cur.execute("DELETE FROM plastering_material_takeoff WHERE project_code=%s AND ifc_file_name=%s", clear_params)
        cur.execute("DELETE FROM rcc_material_takeoff WHERE project_code=%s AND ifc_file_name=%s", clear_params)

        if masonry_rows:
            cur.executemany(
                """
                INSERT INTO masonry_material_takeoff
                (project_code, ifc_file_name, express_id, global_id, family, type_name, base_constraint,
                 length_val, width_val, material_name, material_description, material_area, material_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        payload["project_code"],
                        payload["ifc_file_name"],
                        int(float(row.get("ExpressId") or 0)),
                        row.get("GlobalId") or None,
                        row.get("Family") or None,
                        row.get("Type") or None,
                        row.get("Base Constraint") or None,
                        float(row.get("Length") or 0) if row.get("Length") not in ("", None) else None,
                        float(row.get("Width") or 0) if row.get("Width") not in ("", None) else None,
                        row.get("Material:Name") or "",
                        row.get("Material:Description") or None,
                        float(row.get("Material:Area") or 0) if row.get("Material:Area") not in ("", None) else None,
                        float(row.get("Material:Volume") or 0) if row.get("Material:Volume") not in ("", None) else None,
                    )
                    for row in masonry_rows
                ],
            )

        if plaster_rows:
            # Guard against duplicate key collisions on
            # (project_code, ifc_file_name, express_id, material_name)
            # caused by the same element being collected from multiple paths.
            deduped_plaster_rows = []
            seen_plaster_keys = set()
            for row in plaster_rows:
                key = (
                    int(float(row.get("ExpressId") or 0)),
                    str(row.get("Material:Name") or "").strip(),
                )
                if key in seen_plaster_keys:
                    continue
                seen_plaster_keys.add(key)
                deduped_plaster_rows.append(row)

            cur.executemany(
                """
                INSERT INTO plastering_material_takeoff
                (project_code, ifc_file_name, express_id, global_id, family, type_name, base_constraint,
                 length_val, width_val, material_name, material_description, material_area, material_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        payload["project_code"],
                        payload["ifc_file_name"],
                        int(float(row.get("ExpressId") or 0)),
                        row.get("GlobalId") or None,
                        row.get("Family") or None,
                        row.get("Type") or None,
                        row.get("Base Constraint") or None,
                        float(row.get("Length") or 0) if row.get("Length") not in ("", None) else None,
                        float(row.get("Width") or 0) if row.get("Width") not in ("", None) else None,
                        row.get("Material:Name") or "",
                        row.get("Material:Description") or None,
                        float(row.get("Material:Area") or 0) if row.get("Material:Area") not in ("", None) else None,
                        float(row.get("Material:Volume") or 0) if row.get("Material:Volume") not in ("", None) else None,
                    )
                    for row in deduped_plaster_rows
                ],
            )

        if rcc_takeoff_rows:
            # Guard against duplicate key collisions on
            # (project_code, ifc_file_name, express_id, material_name)
            # when the same RCC element is collected from more than one source.
            deduped_rcc_rows = []
            seen_rcc_keys = set()
            for row in rcc_takeoff_rows:
                key = (
                    int(float(row.get("ExpressId") or 0)),
                    str(row.get("Material:Name") or "").strip(),
                )
                if key in seen_rcc_keys:
                    continue
                seen_rcc_keys.add(key)
                deduped_rcc_rows.append(row)

            cur.executemany(
                """
                INSERT INTO rcc_material_takeoff
                (project_code, ifc_file_name, express_id, global_id, family, type_name, level_name,
                 material_name, material_description, material_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        payload["project_code"],
                        payload["ifc_file_name"],
                        int(float(row.get("ExpressId") or 0)),
                        row.get("GlobalId") or None,
                        row.get("Family") or None,
                        row.get("Type") or None,
                        row.get("Level") or None,
                        row.get("Material:Name") or "",
                        row.get("Material:Description") or None,
                        float(row.get("Material:Volume") or 0) if row.get("Material:Volume") not in ("", None) else None,
                    )
                    for row in deduped_rcc_rows
                ],
            )

        # summaries
        cur.execute(
            """
            INSERT INTO masonry_summary
            (project_code, ifc_file_name, material_name, material_description, total_material_area, total_material_volume)
            SELECT project_code, ifc_file_name, material_name, MAX(material_description),
                   SUM(COALESCE(material_area,0)), SUM(COALESCE(material_volume,0))
            FROM masonry_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY project_code, ifc_file_name, material_name
            """,
            clear_params,
        )
        cur.execute(
            """
            INSERT INTO plastering_summary
            (project_code, ifc_file_name, material_name, material_description, total_material_area, total_material_volume)
            SELECT project_code, ifc_file_name, material_name, MAX(material_description),
                   SUM(COALESCE(material_area,0)), SUM(COALESCE(material_volume,0))
            FROM plastering_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY project_code, ifc_file_name, material_name
            """,
            clear_params,
        )
        cur.execute(
            """
            INSERT INTO rcc_summary
            (project_code, ifc_file_name, material_name, material_description, total_material_volume)
            SELECT project_code, ifc_file_name, material_name, MAX(material_description),
                   SUM(COALESCE(material_volume,0))
            FROM rcc_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY project_code, ifc_file_name, material_name
            """,
            clear_params,
        )

        recalculate_work_item_rate(cur, sor_code)

        conn.commit()
    except Exception:
        conn.rollback()
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    finally:
        conn.close()

    return payload["project_code"], payload["ifc_file_name"]


def fetch_qto_report(project_code, ifc_file_name):
    def _build_earthwork_qto_rows(_ifc_file_name):
        cached = _get_cached_earthwork_data(_ifc_file_name)
        return cached.get("qto_rows", []) if cached else []

    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT sor_database
            FROM project_master
            WHERE project_code=%s AND ifc_file_name=%s
            LIMIT 1
            """,
            (project_code, ifc_file_name),
        )
        project = cur.fetchone() or {}
        sor_code = (project.get("sor_database") or "").strip()

        catalog = []
        if sor_code:
            cur.execute(
                """
                SELECT s.subpackage_code, s.subpackage_name, s.package_code, s.analysis_unit, p.package_name
                FROM work_item_subpackage s
                LEFT JOIN work_item_package p
                  ON p.sor_code = s.sor_code
                 AND p.package_code = s.package_code
                WHERE s.sor_code = %s
                """,
                (sor_code,),
            )
            catalog = cur.fetchall()
        def _build_section_rows(rows, include_area):
            normalized = []
            for row in rows:
                material_name = row.get("material_name") or ""
                material_description = row.get("material_description") or ""
                family = (row.get("family") or "").strip()
                type_name = (row.get("type_name") or "").strip()
                total_area = float(row.get("total_area") or 0.0)
                total_volume = float(row.get("total_volume") or 0.0)

                matched = resolve_subpackage_row(material_name, material_description, catalog) if catalog else None
                work_item_code = ""
                if matched:
                    work_item_code = (matched.get("subpackage_code") or "").strip() or (matched.get("package_code") or "").strip()
                elif _is_rcc_candidate(
                    family, type_name, material_name, material_description
                ):
                    work_item_code = "C3"

                normalized.append(
                    {
                        "work_item_code": work_item_code,
                        "family": family,
                        "type_name": type_name,
                        "material_name": material_name,
                        "material_description": material_description,
                        "total_area": total_area,
                        "total_volume": total_volume,
                    }
                )

            normalized.sort(
                key=lambda r: (
                    r["work_item_code"],
                    r["family"],
                    r["type_name"],
                    r["material_name"],
                )
            )

            out = []

            for r in normalized:
                row_out = {
                    "Work Item Code": r["work_item_code"],
                    "Family": r["family"],
                    "Type": r["type_name"],
                    "Wastage (%)": "0.00",
                    "Material:Name": r["material_name"],
                    "Material:Description": r["material_description"],
                    "Total Volume (m\u00B3)": _format_indian_number(r["total_volume"], 3),
                }
                if include_area:
                    row_out["Total Area (m\u00B2)"] = _format_indian_number(r["total_area"], 3)
                out.append(row_out)

            return out

        cur.execute(
            """
            SELECT
                family,
                type_name,
                material_name,
                material_description,
                SUM(material_area) AS total_area,
                SUM(material_volume) AS total_volume
            FROM masonry_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY family, type_name, material_name, material_description
            ORDER BY family, type_name, material_name
            """,
            (project_code, ifc_file_name),
        )
        masonry = _build_section_rows(cur.fetchall(), include_area=True)

        cur.execute(
            """
            SELECT
                family,
                type_name,
                material_name,
                material_description,
                SUM(material_area) AS total_area,
                SUM(material_volume) AS total_volume
            FROM plastering_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY family, type_name, material_name, material_description
            ORDER BY family, type_name, material_name
            """,
            (project_code, ifc_file_name),
        )
        plastering = _build_section_rows(cur.fetchall(), include_area=True)

        cur.execute(
            """
            SELECT
                family,
                type_name,
                material_name,
                material_description,
                SUM(material_volume) AS total_volume
            FROM rcc_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY family, type_name, material_name, material_description
            ORDER BY family, type_name, material_name
            """,
            (project_code, ifc_file_name),
        )
        rcc = _build_section_rows(cur.fetchall(), include_area=False)
        rcc = [row for row in rcc if str(row.get("Work Item Code", "")).strip().upper().startswith("C")]

        earthwork = _build_earthwork_qto_rows(ifc_file_name)

        return earthwork, masonry, plastering, rcc
    finally:
        conn.close()


def recalculate_work_item_rate(cur, sor_code):
    cur.execute(
        """
        INSERT INTO work_item_rate (sor_code, subpackage_code, amount)
        SELECT
            s.sor_code,
            s.subpackage_code,
            CEILING((t.total_a * (1 + cf.pct)) / s.analysis_quantity) AS rate_per_unit
        FROM work_item_subpackage s
        JOIN (
            SELECT
                a.sor_code,
                a.subpackage_code,
                SUM(
                    CASE a.resource_type
                        WHEN 'MATERIAL' THEN (a.quantity / COALESCE(m.unit_multiplier, 1)) * m.base_rate
                        WHEN 'LABOUR'   THEN (a.quantity / COALESCE(l.unit_multiplier, 1)) * l.base_rate
                        WHEN 'EQUIPMENT' THEN a.quantity * e.base_rate
                        WHEN 'LEAD & LIFT' THEN (a.quantity / COALESCE(ll.unit_multiplier, 1)) * ll.total_charge_per_unit
                        ELSE 0
                    END
                ) AS total_a
            FROM work_item_analysis a
            LEFT JOIN sor_material_data  m
                ON a.resource_type = 'MATERIAL'
               AND a.material_code = m.unique_code
            LEFT JOIN sor_labour_data l
                ON a.resource_type = 'LABOUR'
               AND a.labour_code = l.unique_code
            LEFT JOIN sor_equipment_data e
                ON a.resource_type = 'EQUIPMENT'
               AND a.equipment_code = e.unique_code
            LEFT JOIN (
                SELECT
                    i.sor_code,
                    i.ll_code,
                    CASE
                        WHEN MAX(d.unit) LIKE '1000%%' THEN 1000
                        WHEN MAX(d.unit) LIKE '100 Nos%%' THEN 100
                        ELSE 1
                    END AS unit_multiplier,
                    ROUND(
                        SUM(
                            GREATEST(
                                LEAST(i.distance_km, COALESCE(d.slab_to_km, i.distance_km)) - d.slab_from_km,
                                0
                            ) * d.rate_per_km
                        )
                        + MAX(d.incidental_charges)
                        + MAX(d.loading_charges + d.unloading_charges),
                        2
                    ) AS total_charge_per_unit
                FROM lead_lift_item_master i
                JOIN lead_lift_rate_detail d
                  ON d.sor_code = i.sor_code
                 AND d.profile_code = i.profile_code
                WHERE i.sor_code = %s
                GROUP BY i.sor_code, i.ll_code
            ) ll
                ON a.resource_type = 'LEAD & LIFT'
               AND a.sor_code = ll.sor_code
               AND a.lead_lift_code = ll.ll_code
            WHERE a.sor_code = %s
              AND a.subpackage_code IN ('C3','D1','E3','E5')
            GROUP BY a.sor_code, a.subpackage_code
        ) t
            ON t.sor_code = s.sor_code
           AND t.subpackage_code = s.subpackage_code
        CROSS JOIN (
            SELECT COALESCE(SUM(percentage), 0) / 100.0 AS pct
            FROM work_item_charges
        ) cf
        WHERE s.sor_code = %s
          AND s.subpackage_code IN ('C3','D1','E3','E5')
          AND s.analysis_quantity IS NOT NULL
          AND s.analysis_quantity > 0
        ON DUPLICATE KEY UPDATE amount = VALUES(amount)
        """,
        (sor_code, sor_code, sor_code),
    )


def resolve_subpackage_row(material_name, material_description, catalog_rows):
    mat_raw = (material_name or "").strip().lower()
    desc_raw = (material_description or "").strip().lower()
    if not mat_raw and not desc_raw:
        return None

    def variants(text):
        v = []
        t = (text or "").strip().lower()
        if not t:
            return v
        v.append(t)
        v.append(t.replace(",", ":"))
        v.append(t.replace(":", ","))
        v.append(t.replace(", ", ":"))
        v.append(t.replace(": ", ","))
        # de-duplicate while preserving order
        seen = set()
        out = []
        for x in v:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    candidate_variants = variants(mat_raw) + [v for v in variants(desc_raw) if v not in variants(mat_raw)]

    def extract_mix_ratio(text):
        # Matches 1:4, 1,4, 1 : 4 etc.
        m = re.search(r"1\s*[:.,]\s*(\d+)", text or "")
        return m.group(1) if m else None

    # exact match first
    for row in catalog_rows:
        sub_variants = variants(row.get("subpackage_name") or "")
        if any(mv == sv for mv in candidate_variants for sv in sub_variants):
            return row

    # plastering ratio-aware fallback (e.g., "1,4" in description -> "1:4" subpackage)
    ratio = extract_mix_ratio(mat_raw) or extract_mix_ratio(desc_raw)
    if ratio:
        for row in catalog_rows:
            sub_name = (row.get("subpackage_name") or "").lower()
            if "plaster" in sub_name and f"1:{ratio}" in sub_name.replace(" ", ""):
                return row
            if "plaster" in sub_name and f"1,{ratio}" in sub_name.replace(" ", ""):
                return row

    # contains match fallback
    for row in catalog_rows:
        sub_variants = variants(row.get("subpackage_name") or "")
        if any((sv in mv or mv in sv) for mv in candidate_variants for sv in sub_variants):
            return row

    return None


def _wastage_map_key(work_item_code, material_name, material_description=None):
    return str(work_item_code or "").strip()


def _get_wastage_pct(wastage_map, work_item_code, default_pct=0.0):
    code = str(work_item_code or "").strip()
    if not code:
        return 0.0
    try:
        raw = wastage_map.get(code, default_pct)
        return float(raw if raw not in ("", None) else default_pct)
    except Exception:
        return float(default_pct)


def extract_unique_work_item_codes(*sections):
    seen = set()
    out = []
    for rows in sections:
        for r in rows or []:
            code = str(r.get("Work Item Code", "")).strip()
            if code and code not in seen:
                seen.add(code)
                out.append(code)
    out.sort()
    return out


def _rows_for_work_item_prefix_from_sections(prefix, *sections):
    out = []
    p = (prefix or "").strip().upper()
    for rows in sections:
        for r in rows or []:
            code = str(r.get("Work Item Code", "")).strip().upper()
            if code.startswith(p):
                out.append(r)
    return out


def _format_indian_number(value, decimals=2):
    try:
        num = float(value)
    except Exception:
        return ""

    sign = "-" if num < 0 else ""
    num = abs(num)
    int_part = str(int(num))
    frac_part = f"{num:.{decimals}f}".split(".")[1] if decimals > 0 else ""

    if len(int_part) <= 3:
        grouped = int_part
    else:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        grouped = ",".join(groups + [last3])

    if decimals > 0:
        return f"{sign}{grouped}.{frac_part}"
    return f"{sign}{grouped}"


def _format_inr(value):
    return f"\u20B9 {_format_indian_number(value, 2)}"


def _work_item_code_sort_key(code):
    text = str(code or "").strip().upper()
    if not text:
        return ("ZZZ", 10**9, "")
    m = re.match(r"^([A-Z]+)\s*([0-9]+)$", text)
    if m:
        return (m.group(1), int(m.group(2)), "")
    return (text, 10**9, text)


def _detect_flooring_code_and_name(*texts):
    blob = " ".join(str(t or "").strip().lower() for t in texts)
    if "granite" in blob:
        return "F1", "Granite"
    if "marble" in blob:
        return "F2", "Marble"
    if any(k in blob for k in ("vitrified", "vitified", "tile", "tiles")):
        return "F3", "Tile"
    return "", ""


def _is_rcc_candidate(*texts):
    blob = " ".join(str(t or "").strip().lower() for t in texts)
    return any(
        k in blob
        for k in (
            "rcc",
            "reinforced concrete",
            "reinforced cement concrete",
            "m30",
            "m25",
            "m20",
        )
    )


def _is_excluded_rcc_row(*texts):
    blob = " ".join(str(t or "").strip().lower() for t in texts)
    return ("monolithic run" in blob) or ("m_monolithic run" in blob)


def _get_subpackage_catalog_rows(sor_code):
    if not sor_code:
        return []
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT subpackage_code, subpackage_name, package_code, description
            FROM work_item_subpackage
            WHERE sor_code = %s
            """,
            (sor_code,),
        )
        return cur.fetchall() or []
    finally:
        conn.close()


def remap_qto_rows_by_name(rows, sor_code):
    catalog_rows = _get_subpackage_catalog_rows(sor_code)
    catalog_by_code = {
        str(r.get("subpackage_code") or "").strip().upper(): r for r in catalog_rows
    }
    out = []
    for r in rows or []:
        rr = dict(r)
        mat_name = str(rr.get("Material:Name", "")).strip()
        mat_desc = str(rr.get("Material:Description", "")).strip()
        family = str(rr.get("Family", "")).strip()
        type_name = str(rr.get("Type", "")).strip()

        matched = resolve_subpackage_row(mat_name, mat_desc, catalog_rows) if catalog_rows else None
        if matched:
            code = str(matched.get("subpackage_code") or "").strip().upper()
            if code:
                rr["Work Item Code"] = code
            mapped_name = str(matched.get("subpackage_name") or "").strip()
            if mapped_name:
                rr["Material:Name"] = mapped_name
        else:
            # RCC fallback
            if _is_rcc_candidate(family, type_name, mat_name, mat_desc):
                rr["Work Item Code"] = "C3"
                c3 = catalog_by_code.get("C3")
                if c3:
                    rr["Material:Name"] = str(c3.get("subpackage_name") or rr.get("Material:Name", ""))
            else:
                # Flooring fallback
                floor_code, _ = _detect_flooring_code_and_name(family, type_name, mat_name, mat_desc)
                if floor_code:
                    rr["Work Item Code"] = floor_code
                    frow = catalog_by_code.get(floor_code)
                    if frow:
                        rr["Material:Name"] = str(frow.get("subpackage_name") or rr.get("Material:Name", ""))
        out.append(rr)
    return out


def derive_flooring_rows_from_sections(rows, flooring_desc_map=None):
    flooring_desc_map = flooring_desc_map or {}
    derived = []
    def _to_float(v):
        try:
            return float(str(v).replace(",", "").strip())
        except Exception:
            return 0.0
    for r in rows or []:
        family = str(r.get("Family", "")).strip()
        type_name = str(r.get("Type", "")).strip()
        mat_name = str(r.get("Material:Name", "")).strip()
        mat_desc = str(r.get("Material:Description", "")).strip()
        if _is_rcc_candidate(family, type_name, mat_name, mat_desc):
            continue
        code, item_name = _detect_flooring_code_and_name(family, type_name, mat_name, mat_desc)
        if not code:
            continue
        area = _to_float(r.get("Total Area (m²)", r.get("Total Area (mÂ²)", 0)))
        volume = _to_float(r.get("Total Volume (m³)", r.get("Total Volume (mÂ³)", 0)))
        if area <= 0 and volume <= 0:
            continue
        rr = dict(r)
        rr["Work Item Code"] = code
        rr["Material:Name"] = item_name
        # For flooring, keep description from IFC extraction as source of truth.
        rr["Material:Description"] = mat_desc or item_name
        derived.append(rr)
    return derived


def build_tender_estimate(project_code, ifc_file_name, wastage_map=None):
    wastage_map = wastage_map or {}
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT project_code, project_name, project_location, client_name, site_area,
                   total_builtup_area, building_height, date_of_issue, estimator_name,
                   sor_database
            FROM project_master
            WHERE project_code=%s AND ifc_file_name=%s
            LIMIT 1
            """,
            (project_code, ifc_file_name),
        )
        project = cur.fetchone()
        if not project:
            return None, [], 0.0

        sor_code = project["sor_database"]

        cur.execute(
            """
            SELECT material_name, material_description, total_material_volume AS qty
            FROM masonry_summary
            WHERE project_code=%s AND ifc_file_name=%s
            UNION ALL
            SELECT material_name, material_description, total_material_volume AS qty
            FROM plastering_summary
            WHERE project_code=%s AND ifc_file_name=%s
            UNION ALL
            SELECT material_name, material_description, total_material_volume AS qty
            FROM rcc_summary
            WHERE project_code=%s AND ifc_file_name=%s
            """,
            (project_code, ifc_file_name, project_code, ifc_file_name, project_code, ifc_file_name),
        )
        summary_rows = cur.fetchall()

        # Earthwork (A1) is IFC-derived and not persisted in *_summary tables.
        # Include it in tender estimate from Earthwork takeoff.
        earthwork_takeoff_rows = build_earthwork_takeoff_rows(ifc_file_name)
        if earthwork_takeoff_rows and len(earthwork_takeoff_rows) > 1:
            hdr = earthwork_takeoff_rows[0]
            try:
                vol_idx = hdr.index("Computed Volume (m³)")
            except Exception:
                vol_idx = -1
            earth_qty = 0.0
            if vol_idx >= 0:
                for rr in earthwork_takeoff_rows[1:]:
                    try:
                        earth_qty += float(str(rr[vol_idx]).replace(",", "").strip())
                    except Exception:
                        continue
            if earth_qty > 0:
                summary_rows.append(
                    {
                        "material_name": "Earthwork",
                        "material_description": "",
                        "qty": earth_qty,
                    }
                )

        # Painting quantities are area-driven and are derived from plastering takeoff types.
        cur.execute(
            """
            SELECT type_name, SUM(COALESCE(material_area, 0)) AS total_area
            FROM plastering_material_takeoff
            WHERE project_code=%s AND ifc_file_name=%s
            GROUP BY type_name
            """,
            (project_code, ifc_file_name),
        )
        painting_qty_by_code = {"G1": 0.0, "G2": 0.0}
        for rr in cur.fetchall() or []:
            t = str(rr.get("type_name") or "").strip().lower()
            area = float(rr.get("total_area") or 0.0)
            if area <= 0:
                continue
            if "external wall" in t:
                painting_qty_by_code["G2"] += area
            elif "internal wall" in t:
                painting_qty_by_code["G1"] += area

        cur.execute(
            """
            SELECT s.subpackage_code, s.subpackage_name, s.package_code, s.analysis_unit, p.package_name
            FROM work_item_subpackage s
            LEFT JOIN work_item_package p
              ON p.sor_code = s.sor_code
             AND p.package_code = s.package_code
            WHERE s.sor_code = %s
            """,
            (sor_code,),
        )
        catalog = cur.fetchall()
        catalog_by_code = {
            str(r.get("subpackage_code") or "").strip(): r for r in (catalog or [])
        }

        cur.execute(
            """
            SELECT subpackage_code, amount
            FROM work_item_rate
            WHERE sor_code = %s
            """,
            (sor_code,),
        )
        rate_map = {r["subpackage_code"]: float(r["amount"] or 0) for r in cur.fetchall()}

        grouped = {}
        for r in summary_rows:
            material_name = r.get("material_name") or ""
            material_description = r.get("material_description") or ""
            qty = float(r.get("qty") or 0)
            if qty <= 0:
                continue

            matched = resolve_subpackage_row(material_name, material_description, catalog)
            if matched:
                code = (matched.get("subpackage_code") or "").strip() or (matched.get("package_code") or "").strip()
                item = (matched.get("subpackage_name") or "").strip() or material_name
                unit = (matched.get("analysis_unit") or "").strip()
                price = float(rate_map.get(matched.get("subpackage_code"), 0))
            else:
                code = ""
                item = material_name
                unit = ""
                price = 0.0

            wastage_pct = _get_wastage_pct(wastage_map, code, default_pct=0.0)
            total_volume = qty * (1 + (wastage_pct / 100.0))
            total_amt = total_volume * price
            key = (code, item, unit, price)
            if key not in grouped:
                grouped[key] = {
                    "qty": 0.0,
                    "total_volume": 0.0,
                    "total_amt": 0.0,
                }
            grouped[key]["qty"] += qty
            grouped[key]["total_volume"] += total_volume
            grouped[key]["total_amt"] += total_amt

        # Ensure painting codes are always present in final tender estimate.
        for forced_code in ("G1", "G2"):
            info = catalog_by_code.get(forced_code, {})
            item = (info.get("subpackage_name") or "").strip() or (
                "Internal Wall Painting" if forced_code == "G1" else "External Wall Painting"
            )
            unit = (info.get("analysis_unit") or "").strip()
            price = float(rate_map.get(forced_code, 0))
            key = (forced_code, item, unit, price)
            base_qty = float(painting_qty_by_code.get(forced_code, 0.0))
            wastage_pct = _get_wastage_pct(wastage_map, forced_code, default_pct=0.0)
            total_qty = base_qty * (1 + (wastage_pct / 100.0))
            total_amt = total_qty * price
            grouped[key] = {
                "qty": base_qty,
                "total_volume": total_qty,
                "total_amt": total_amt,
            }

        rows = []
        grand_total = 0.0
        for (code, item, unit, price), vals in grouped.items():
            total_volume = vals["total_volume"]
            total_amt = vals["total_amt"]
            grand_total += total_amt
            rows.append(
                {
                    "Work Item Code": code,
                    "Item": item,
                    "Area / Volume": _format_indian_number(total_volume, 3),
                    "Unit": unit,
                    "Price (\u20B9)": _format_indian_number(price, 2),
                    "Total Amount (\u20B9)": _format_indian_number(total_amt, 2),
                }
            )

        rows.sort(
            key=lambda r: (
                _work_item_code_sort_key(r.get("Work Item Code", "")),
                str(r.get("Item", "")),
            )
        )

        return project, rows, grand_total
    finally:
        conn.close()


def build_tender_estimate_csv_bytes(rows, grand_total):
    output = io.StringIO()
    writer = csv.writer(output)
    headers = [
        "Work Item Code",
        "Item",
        "Area / Volume",
        "Unit",
        "Price (\u20B9)",
        "Total Amount (\u20B9)",
    ]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    writer.writerow([])
    writer.writerow(["", "", "", "", "Grand Total", _format_inr(grand_total)])
    # Keep ASCII labels for maximum compatibility across Excel/encodings.
    return output.getvalue().encode("utf-8-sig")


def build_tender_estimate_excel_bytes(rows, grand_total):
    headers = [
        "Work Item Code",
        "Item",
        "Area / Volume",
        "Unit",
        "Price (\u20B9)",
        "Total Amount (\u20B9)",
    ]
    sheet_rows = [headers]
    for row in rows:
        sheet_rows.append([row.get(h, "") for h in headers])
    sheet_rows.append(["", "", "", "", "Grand Total", _format_inr(grand_total)])

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        Final_Report.build_workbook([("Tender_Estimate", sheet_rows)], tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def render_simple_table(rows, wide=False):
    if not rows:
        return
    headers = list(rows[0].keys())
    head_html = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body_parts = []
    for row in rows:
        tds = "".join(
            f"<td>{html.escape('' if row.get(h) is None else str(row.get(h)))}</td>"
            for h in headers
        )
        body_parts.append(f"<tr>{tds}</tr>")
    table_layout = "auto"
    wrap_overflow = "auto"
    table_font = "12px" if wide else "13px"
    td_whitespace = "nowrap"

    table_html = f"""
    <style>
      .formal-table-wrap {{
        overflow-x: {wrap_overflow};
        margin-bottom: 0.5rem;
        border: 1px solid #dcdcdc;
        border-radius: 8px;
      }}
      .formal-table {{
        width: 100%;
        table-layout: {table_layout};
        min-width: 980px;
        border-collapse: separate;
        border-spacing: 0;
        border: 0;
        border-radius: 0;
        overflow: visible;
        background: #ffffff;
        color: #111111;
        font-size: {table_font};
      }}
      .formal-table thead tr {{
        background: #ffffff;
      }}
      .formal-table th {{
        color: #111111 !important;
        background: #ffffff !important;
        border-bottom: 2px solid #d6d6d6;
        font-weight: 700;
        text-align: left;
        padding: 6px 8px;
        white-space: nowrap;
      }}
      .formal-table td {{
        color: #111111 !important;
        padding: 6px 8px;
        border-bottom: 1px solid #ececec;
        white-space: {td_whitespace};
        word-break: normal;
      }}
      .formal-table tbody tr:nth-child(even) {{
        background: #fafafa;
      }}
      .formal-table tbody tr:hover {{
        background: #f1f5f9;
      }}
    </style>
    <div class="formal-table-wrap">
      <table class="formal-table">
        <thead>
          <tr>{head_html}</tr>
        </thead>
        <tbody>
          {''.join(body_parts)}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def render_tender_estimate_table(rows):
    if not rows:
        return
    headers = list(rows[0].keys())
    numeric_headers = {
        "Area / Volume",
        "Price (₹)",
        "Total Amount (₹)",
    }

    head_html = "".join(
        f"<th class=\"{'num' if h in numeric_headers else ''}\">{html.escape(str(h))}</th>"
        for h in headers
    )
    body_parts = []
    for idx, row in enumerate(rows, start=1):
        cells = []
        for h in headers:
            val = "" if row.get(h) is None else str(row.get(h))
            cls = "num" if h in numeric_headers else ""
            cells.append(f"<td class=\"{cls}\">{html.escape(val)}</td>")
        cells.insert(0, f"<td class=\"rowno\">{idx}</td>")
        body_parts.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f"""
    <style>
      .tender-table-wrap {{
        overflow-x: auto;
        margin: 0.2rem 0 0.6rem 0;
        border: 1px solid #d7dbe0;
        border-radius: 8px;
        background: #fff;
      }}
      .tender-table {{
        width: 100%;
        min-width: 980px;
        border-collapse: collapse;
        font-size: 12px;
      }}
      .tender-table thead th {{
        position: sticky;
        top: 0;
        z-index: 1;
        background: #f5f7fa;
        color: #111827;
        padding: 6px 8px;
        border-bottom: 1px solid #d7dbe0;
        text-align: left;
        white-space: nowrap;
        font-weight: 700;
      }}
      .tender-table td {{
        padding: 6px 8px;
        border-bottom: 1px solid #eef1f4;
        color: #111827;
        white-space: nowrap;
      }}
      .tender-table tbody tr:nth-child(even) {{
        background: #fafbfc;
      }}
      .tender-table .num {{
        text-align: right;
      }}
      .tender-table .rowno {{
        width: 40px;
        text-align: center;
        color: #6b7280;
      }}
    </style>
    <div class="tender-table-wrap">
      <table class="tender-table">
        <thead>
          <tr><th>#</th>{head_html}</tr>
        </thead>
        <tbody>
          {''.join(body_parts)}
        </tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def split_qto_tables(rows, wastage_map=None):
    wastage_map = wastage_map or {}
    first_rows = []
    second_acc = {}
    for r in rows or []:
        area_val = r.get("Total Area (m²)", r.get("Total Area (mÂ²)", ""))
        vol_val = r.get("Total Volume (m³)", r.get("Total Volume (mÂ³)", ""))
        work_item_code = r.get("Work Item Code", "")
        material_name = r.get("Material:Name", "")
        material_description = r.get("Material:Description", "")
        wastage_val = _get_wastage_pct(wastage_map, work_item_code, default_pct=0.0)

        first_rows.append(
            {
                "Work Item Code": work_item_code,
                "Family": r.get("Family", ""),
                "Type": r.get("Type", ""),
                "Material:Name": material_name,
                "Total Volume (m³)": vol_val,
                "Total Area (m²)": area_val,
            }
        )

        # Table 2 should be work-item wise, not split by family/type lines.
        if str(material_name).strip().lower().startswith("total for "):
            continue
        key = (work_item_code, material_name)
        if key not in second_acc:
            second_acc[key] = {
                "Work Item Code": work_item_code,
                "Material:Name": material_name,
                "_descriptions": set(),
                "Wastage (%)": wastage_val,
                "_vol": 0.0,
                "_area": 0.0,
            }
        if material_description:
            second_acc[key]["_descriptions"].add(str(material_description).strip())

        def _to_float(v):
            try:
                return float(str(v).replace(",", "").strip())
            except Exception:
                return 0.0

        second_acc[key]["_vol"] += _to_float(vol_val)
        second_acc[key]["_area"] += _to_float(area_val)

    second_rows = []
    for _, row in second_acc.items():
        wastage_pct = float(row.get("Wastage (%)") or 0.0)
        base_vol = float(row["_vol"])
        wastage_vol = base_vol * (wastage_pct / 100.0)
        total_vol = base_vol + wastage_vol
        second_rows.append(
            {
                "Work Item Code": row["Work Item Code"],
                "Material:Name": row["Material:Name"],
                "Material:Description": "; ".join(sorted(row["_descriptions"])),
                "Wastage (%)": _format_indian_number(wastage_pct, 2),
                "Base Volume (m³)": _format_indian_number(base_vol, 3),
                "Wastage Volume (m³)": _format_indian_number(wastage_vol, 3),
                "Total Volume (m³)": _format_indian_number(total_vol, 3),
                "Total Area (m²)": _format_indian_number(row["_area"], 3),
            }
        )
    return first_rows, second_rows


def render_qto_table1_inputs(rows, key_prefix):
    if not rows:
        return []

    sample = rows[0]
    vol_key = (
        "Base Volume (m³)"
        if "Base Volume (m³)" in sample
        else ("Total Volume (m³)" if "Total Volume (m³)" in sample else "Total Volume (mÂ³)")
    )
    area_key = "Total Area (m²)" if "Total Area (m²)" in sample else "Total Area (mÂ²)"

    h = st.columns([1.2, 1.0, 1.1, 1.6, 1.1, 1.1])
    h[0].markdown("**Work Item Code**")
    h[1].markdown("**Family**")
    h[2].markdown("**Type**")
    h[3].markdown("**Material:Name**")
    h[4].markdown("**Total Volume (m³)**")
    h[5].markdown("**Total Area (m²)**")
    st.divider()

    for _, row in enumerate(rows):
        c = st.columns([1.2, 1.0, 1.1, 1.6, 1.1, 1.1])
        c[0].write(row.get("Work Item Code", ""))
        c[1].write(row.get("Family", ""))
        c[2].write(row.get("Type", ""))
        c[3].write(row.get("Material:Name", ""))
        c[4].write(row.get(vol_key, ""))
        c[5].write(row.get(area_key, ""))
        st.divider()

    return rows


def render_qto_table2_inputs(rows, key_prefix):
    if not rows:
        return []

    sample = rows[0]
    base_vol_key = (
        "Base Volume (m³)"
        if "Base Volume (m³)" in sample
        else ("Total Volume (m³)" if "Total Volume (m³)" in sample else "Total Volume (mÂ³)")
    )
    area_key = "Total Area (m²)" if "Total Area (m²)" in sample else "Total Area (mÂ²)"

    h = st.columns([1.0, 1.4, 2.0, 0.9, 1.0, 1.1, 1.4, 1.0])
    h[0].markdown("**Work Item Code**")
    h[1].markdown("**Material:Name**")
    h[2].markdown("**Material:Description**")
    h[3].markdown("**Wastage (%)**")
    h[4].markdown("**Base Volume (m³)**")
    h[5].markdown("**Wastage Volume (m³)**")
    h[6].markdown("**Total Volume (m³)**")
    h[7].markdown("**Total Area (m²)**")
    st.divider()

    for row in rows:
        c = st.columns([1.0, 1.4, 2.0, 0.9, 1.0, 1.1, 1.4, 1.0])
        c[0].write(row.get("Work Item Code", ""))
        c[1].write(row.get("Material:Name", ""))
        c[2].write(row.get("Material:Description", ""))
        c[3].write(row.get("Wastage (%)", ""))
        c[4].write(row.get(base_vol_key, ""))
        c[5].write(row.get("Wastage Volume (m³)", row.get("Wastage Qty (m³)", "")))
        c[6].write(row.get("Total Volume (m³)", row.get("Total Volume + Wastage (m³)", "")))
        c[7].write(row.get(area_key, ""))
        st.divider()
    return rows


def build_qto_merged_rows(rows, wastage_map=None, include_area=True, area_only=False, flooring_mode=False):
    wastage_map = wastage_map or {}
    grouped = {}

    def _to_float(v):
        try:
            return float(str(v).replace(",", "").strip())
        except Exception:
            return 0.0

    normalized = []
    for r in rows or []:
        code = str(r.get("Work Item Code", "")).strip()
        family = str(r.get("Family", "")).strip()
        type_name = str(r.get("Type", "")).strip()
        material_name = str(r.get("Material:Name", "")).strip()
        material_desc = str(r.get("Material:Description", "")).strip()
        base_vol = _to_float(r.get("Total Volume (m³)", r.get("Total Volume (mÂ³)", 0)))
        area = _to_float(r.get("Total Area (m²)", r.get("Total Area (mÂ²)", 0))) if include_area else 0.0
        wastage_pct = _get_wastage_pct(wastage_map, code, default_pct=0.0)
        row_obj = {
            "Work Item Code": code,
            "Family": family,
            "Type": type_name,
            "Material:Name": material_name,
            "Material:Description": material_desc,
            "Wastage (%)": _format_indian_number(wastage_pct, 2),
            "_area": area,
            "_total_volume_only": base_vol,
        }
        if flooring_mode:
            wastage_area = area * (wastage_pct / 100.0)
            total_area = area + wastage_area
            row_obj["Total Volume (m³)"] = _format_indian_number(base_vol, 3)
            row_obj["Base Area (m²)"] = _format_indian_number(area, 3)
            row_obj["Wastage Area (m²)"] = _format_indian_number(wastage_area, 3)
            row_obj["Total Area (m²)"] = _format_indian_number(total_area, 3)
            row_obj["_base_vol"] = area
            row_obj["_wastage_vol"] = wastage_area
            row_obj["_total_vol"] = total_area
        else:
            base_qty = area if area_only else base_vol
            wastage_qty = base_qty * (wastage_pct / 100.0)
            total_qty = base_qty + wastage_qty
            row_obj["Base Volume (m³)"] = _format_indian_number(base_qty, 3)
            row_obj["Wastage Volume (m³)"] = _format_indian_number(wastage_qty, 3)
            row_obj["Total Volume (m³)"] = _format_indian_number(total_qty, 3)
            row_obj["_base_vol"] = base_qty
            row_obj["_wastage_vol"] = wastage_qty
            row_obj["_total_vol"] = total_qty
            if include_area and not area_only:
                row_obj["Total Area (m²)"] = _format_indian_number(area, 3)
            if area_only:
                row_obj["Base Area (m²)"] = _format_indian_number(base_qty, 3)
                row_obj["Wastage Area (m²)"] = _format_indian_number(wastage_qty, 3)
                row_obj["Total Area (m²)"] = _format_indian_number(total_qty, 3)
        normalized.append(row_obj)

    normalized.sort(
        key=lambda x: (
            x["Work Item Code"],
            x["Family"],
            x["Type"],
            x["Material:Name"],
            x["Material:Description"],
        )
    )

    merged = []
    for row in normalized:
        code = row["Work Item Code"]
        if code not in grouped:
            grouped[code] = {"base": 0.0, "wastage": 0.0, "total": 0.0, "area": 0.0, "vol": 0.0}
        grouped[code]["base"] += row["_base_vol"]
        grouped[code]["wastage"] += row["_wastage_vol"]
        grouped[code]["total"] += row["_total_vol"]
        grouped[code]["area"] += row["_area"]
        grouped[code]["vol"] += row["_total_volume_only"]
        merged.append({k: v for k, v in row.items() if not k.startswith("_")})

    final_rows = []
    current_code = None
    for row in merged:
        code = row["Work Item Code"]
        if current_code is None:
            current_code = code
        elif code != current_code:
            sums = grouped.get(current_code, {"base": 0.0, "wastage": 0.0, "total": 0.0, "area": 0.0, "vol": 0.0})
            total_row = {
                "Work Item Code": current_code,
                "Family": "",
                "Type": "",
                "Material:Name": f"Total for {current_code}",
                "Material:Description": "",
                "Wastage (%)": "",
            }
            if flooring_mode:
                total_row["Total Volume (m³)"] = _format_indian_number(sums["vol"], 3)
                total_row["Base Area (m²)"] = _format_indian_number(sums["base"], 3)
                total_row["Wastage Area (m²)"] = _format_indian_number(sums["wastage"], 3)
                total_row["Total Area (m²)"] = _format_indian_number(sums["total"], 3)
            else:
                total_row["Base Volume (m³)"] = _format_indian_number(sums["base"], 3)
                total_row["Wastage Volume (m³)"] = _format_indian_number(sums["wastage"], 3)
                total_row["Total Volume (m³)"] = _format_indian_number(sums["total"], 3)
            if include_area and not area_only and not flooring_mode:
                total_row["Total Area (m²)"] = _format_indian_number(sums["area"], 3)
            if area_only:
                total_row["Base Area (m²)"] = _format_indian_number(sums["base"], 3)
                total_row["Wastage Area (m²)"] = _format_indian_number(sums["wastage"], 3)
                total_row["Total Area (m²)"] = _format_indian_number(sums["total"], 3)
            final_rows.append(total_row)
            current_code = code
        final_rows.append(row)

    if current_code is not None:
        sums = grouped.get(current_code, {"base": 0.0, "wastage": 0.0, "total": 0.0, "area": 0.0, "vol": 0.0})
        total_row = {
            "Work Item Code": current_code,
            "Family": "",
            "Type": "",
            "Material:Name": f"Total for {current_code}",
            "Material:Description": "",
            "Wastage (%)": "",
        }
        if flooring_mode:
            total_row["Total Volume (m³)"] = _format_indian_number(sums["vol"], 3)
            total_row["Base Area (m²)"] = _format_indian_number(sums["base"], 3)
            total_row["Wastage Area (m²)"] = _format_indian_number(sums["wastage"], 3)
            total_row["Total Area (m²)"] = _format_indian_number(sums["total"], 3)
        else:
            total_row["Base Volume (m³)"] = _format_indian_number(sums["base"], 3)
            total_row["Wastage Volume (m³)"] = _format_indian_number(sums["wastage"], 3)
            total_row["Total Volume (m³)"] = _format_indian_number(sums["total"], 3)
        if include_area and not area_only and not flooring_mode:
            total_row["Total Area (m²)"] = _format_indian_number(sums["area"], 3)
        if area_only:
            total_row["Base Area (m²)"] = _format_indian_number(sums["base"], 3)
            total_row["Wastage Area (m²)"] = _format_indian_number(sums["wastage"], 3)
            total_row["Total Area (m²)"] = _format_indian_number(sums["total"], 3)
        final_rows.append(total_row)

    return final_rows


def render_qto_merged_table(rows, key_prefix, include_area=True, area_only=False, flooring_mode=False):
    if not rows:
        return []
    if flooring_mode:
        headers = [
            "Work Item Code",
            "Family",
            "Type",
            "Material:Name",
            "Material:Description",
            "Wastage (%)",
            "Total Volume (m³)",
            "Base Area (m²)",
            "Wastage Area (m²)",
            "Total Area (m²)",
        ]
    elif area_only:
        headers = [
            "Work Item Code",
            "Family",
            "Type",
            "Material:Name",
            "Material:Description",
            "Wastage (%)",
            "Base Area (m²)",
            "Wastage Area (m²)",
            "Total Area (m²)",
        ]
    else:
        headers = [
            "Work Item Code",
            "Family",
            "Type",
            "Material:Name",
            "Material:Description",
            "Wastage (%)",
            "Base Volume (m³)",
            "Wastage Volume (m³)",
            "Total Volume (m³)",
        ]
        if include_area:
            headers.append("Total Area (m²)")

    head_html = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body_parts = []
    for row in rows:
        is_total = str(row.get("Material:Name", "")).strip().lower().startswith("total for ")
        cls = "qto-total-row" if is_total else ""
        tds = "".join(
            f"<td>{html.escape('' if row.get(h) is None else str(row.get(h)))}</td>"
            for h in headers
        )
        body_parts.append(f"<tr class=\"{cls}\">{tds}</tr>")

    table_html = f"""
    <style>
      .qto-merged-wrap {{
        overflow-x: auto;
        margin-bottom: 0.75rem;
        border: 1px solid #3b4252;
        border-radius: 8px;
      }}
      .qto-merged-table {{
        width: 100%;
        min-width: 1400px;
        border-collapse: collapse;
        table-layout: auto;
      }}
      .qto-merged-table th,
      .qto-merged-table td {{
        border: 1px solid #3b4252;
        padding: 8px 10px;
        vertical-align: top;
      }}
      .qto-merged-table th {{
        font-weight: 700;
        white-space: nowrap;
      }}
      .qto-total-row td {{
        font-weight: 700;
      }}
    </style>
    <div class="qto-merged-wrap">
      <table class="qto-merged-table">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{''.join(body_parts)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    return rows


def render_earthwork_summary_table(rows, key_prefix):
    if not rows:
        return []
    headers = [
        "Family",
        "Type",
        "Level",
        "Count",
        "Material:Name",
        "Material:Description",
        "Total Computed Volume (m³)",
    ]
    head_html = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body_parts = []
    for row in rows:
        is_total = str(row.get("Family", "")).strip().upper() == "GRAND TOTAL"
        cls = "qto-total-row" if is_total else ""
        tds = "".join(
            f"<td>{html.escape('' if row.get(h) is None else str(row.get(h)))}</td>"
            for h in headers
        )
        body_parts.append(f"<tr class=\"{cls}\">{tds}</tr>")

    table_html = f"""
    <style>
      .qto-merged-wrap {{
        overflow-x: auto;
        margin-bottom: 0.75rem;
        border: 1px solid #3b4252;
        border-radius: 8px;
      }}
      .qto-merged-table {{
        width: 100%;
        min-width: 1200px;
        border-collapse: collapse;
        table-layout: auto;
      }}
      .qto-merged-table th,
      .qto-merged-table td {{
        border: 1px solid #3b4252;
        padding: 8px 10px;
        vertical-align: top;
      }}
      .qto-merged-table th {{
        font-weight: 700;
        white-space: nowrap;
      }}
      .qto-total-row td {{
        font-weight: 700;
      }}
    </style>
    <div class="qto-merged-wrap" id="{html.escape(key_prefix)}">
      <table class="qto-merged-table">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{''.join(body_parts)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    return rows


def render_tender_table_qto_style(rows, key_prefix):
    if not rows:
        return []
    headers = [
        "Work Item Code",
        "Item",
        "Area / Volume",
        "Unit",
        "Price (\u20B9)",
        "Total Amount (\u20B9)",
    ]
    numeric_headers = {"Area / Volume", "Price (\u20B9)", "Total Amount (\u20B9)"}
    head_html = "".join(
        f"<th class=\"{'num' if h in numeric_headers else ''}\">{html.escape(h)}</th>"
        for h in headers
    )
    body_parts = []
    for row in rows:
        tds = "".join(
            f"<td class=\"{'num' if h in numeric_headers else ''}\">{html.escape('' if row.get(h) is None else str(row.get(h)))}</td>"
            for h in headers
        )
        body_parts.append(f"<tr>{tds}</tr>")

    table_html = f"""
    <style>
      .tender-qto-wrap {{
        overflow-x: auto;
        margin-bottom: 0.75rem;
        border: 1px solid #3b4252;
        border-radius: 8px;
      }}
      .tender-qto-table {{
        width: 100%;
        min-width: 1050px;
        border-collapse: collapse;
      }}
      .tender-qto-table th,
      .tender-qto-table td {{
        border: 1px solid #3b4252;
        padding: 8px 10px;
        vertical-align: top;
      }}
      .tender-qto-table th {{
        font-weight: 700;
        white-space: nowrap;
      }}
      .tender-qto-table .num {{
        text-align: right;
      }}
    </style>
    <div class="tender-qto-wrap">
      <table class="tender-qto-table">
        <thead><tr>{head_html}</tr></thead>
        <tbody>{''.join(body_parts)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    return rows


def fetch_table_rows(project_code, ifc_file_name, table_name, columns):
    conn = get_conn()
    try:
        cur = conn.cursor()
        query = f"""
            SELECT {", ".join(columns)}
            FROM {table_name}
            WHERE project_code=%s AND ifc_file_name=%s
        """
        cur.execute(query, (project_code, ifc_file_name))
        out = [list(columns)]
        for row in cur.fetchall():
            out.append(["" if v is None else str(v) for v in row])
        return out
    finally:
        conn.close()


def build_flooring_takeoff_rows(project_code, ifc_file_name, flooring_desc_map=None):
    flooring_desc_map = flooring_desc_map or {}
    headers = [
        "express_id",
        "global_id",
        "family",
        "type_name",
        "base_constraint_or_level",
        "material_name",
        "material_description",
        "material_area",
        "material_volume",
    ]
    out = [headers]

    def _append_from_rows(rows, base_field, area_field, volume_field):
        if not rows:
            return
        idx = {name: i for i, name in enumerate(rows[0])}
        for r in rows[1:]:
            family = r[idx["family"]] if "family" in idx else ""
            type_name = r[idx["type_name"]] if "type_name" in idx else ""
            mat_name = r[idx["material_name"]] if "material_name" in idx else ""
            mat_desc = r[idx["material_description"]] if "material_description" in idx else ""
            if _is_rcc_candidate(family, type_name, mat_name, mat_desc):
                continue
            code, item_name = _detect_flooring_code_and_name(family, type_name, mat_name, mat_desc)
            if not code:
                continue
            out.append(
                [
                    r[idx["express_id"]] if "express_id" in idx else "",
                    r[idx["global_id"]] if "global_id" in idx else "",
                    family,
                    type_name,
                    r[idx[base_field]] if base_field in idx else "",
                    item_name,
                    mat_desc or item_name,
                    r[idx[area_field]] if area_field in idx else "",
                    r[idx[volume_field]] if volume_field in idx else "",
                ]
            )

    _append_from_rows(
        fetch_table_rows(
            project_code,
            ifc_file_name,
            "masonry_material_takeoff",
            [
                "express_id",
                "global_id",
                "family",
                "type_name",
                "base_constraint",
                "material_name",
                "material_description",
                "material_area",
                "material_volume",
            ],
        ),
        "base_constraint",
        "material_area",
        "material_volume",
    )
    _append_from_rows(
        fetch_table_rows(
            project_code,
            ifc_file_name,
            "plastering_material_takeoff",
            [
                "express_id",
                "global_id",
                "family",
                "type_name",
                "base_constraint",
                "material_name",
                "material_description",
                "material_area",
                "material_volume",
            ],
        ),
        "base_constraint",
        "material_area",
        "material_volume",
    )
    _append_from_rows(
        fetch_table_rows(
            project_code,
            ifc_file_name,
            "rcc_material_takeoff",
            [
                "express_id",
                "global_id",
                "family",
                "type_name",
                "level_name",
                "material_name",
                "material_description",
                "material_volume",
            ],
        ),
        "level_name",
        "__missing__",
        "material_volume",
    )
    return out


def _earthwork_cache_tag(ifc_file_name):
    if not ifc_file_name:
        return None
    ifc_full_path = UPLOAD_DIR / ifc_file_name
    if not ifc_full_path.exists():
        return None
    try:
        stt = ifc_full_path.stat()
        return ifc_file_name, int(stt.st_size), int(stt.st_mtime_ns)
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def _build_cached_earthwork_data(ifc_file_name, file_size, file_mtime_ns):
    _ = (file_size, file_mtime_ns)
    ifc_full_path = UPLOAD_DIR / ifc_file_name
    if not ifc_full_path.exists():
        return {"takeoff_rows": [], "summary_rows": [], "qto_rows": []}

    try:
        model = ifcopenshell.open(str(ifc_full_path))
        takeoff_rows = Earthwork.build_takeoff_rows(model) or []
        summary_rows = Earthwork.build_summary_rows(takeoff_rows) or []
    except Exception:
        return {"takeoff_rows": [], "summary_rows": [], "qto_rows": []}

    grouped_qto = {}
    for r in takeoff_rows:
        family = str(r.get("Family", "")).strip()
        typ = str(r.get("Type", "")).strip()
        key = ("A1", family, typ, "Earthwork", "")
        vol = r.get("Computed Volume (m³)", r.get("Computed Volume (mÂ³)", "0"))
        try:
            vol_f = float(str(vol).replace(",", "").strip())
        except Exception:
            vol_f = 0.0
        grouped_qto[key] = grouped_qto.get(key, 0.0) + vol_f

    qto_rows = []
    for (code, family, typ, mat_name, mat_desc), vol_f in sorted(
        grouped_qto.items(),
        key=lambda x: (x[0][0], x[0][1], x[0][2], x[0][3], x[0][4]),
    ):
        qto_rows.append(
            {
                "Work Item Code": code,
                "Family": family,
                "Type": typ,
                "Wastage (%)": "0.00",
                "Material:Name": mat_name,
                "Material:Description": mat_desc,
                "Total Volume (m³)": _format_indian_number(vol_f, 3),
            }
        )

    return {
        "takeoff_rows": takeoff_rows,
        "summary_rows": summary_rows,
        "qto_rows": qto_rows,
    }


def _get_cached_earthwork_data(ifc_file_name):
    tag = _earthwork_cache_tag(ifc_file_name)
    if not tag:
        return {"takeoff_rows": [], "summary_rows": [], "qto_rows": []}
    file_name, file_size, file_mtime_ns = tag
    return _build_cached_earthwork_data(file_name, file_size, file_mtime_ns)


def build_earthwork_takeoff_rows(ifc_file_name):
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
    out = [headers]
    rows = _get_cached_earthwork_data(ifc_file_name).get("takeoff_rows", [])

    for r in rows or []:
        out.append([str(r.get(h, "")) for h in headers])
    return out


def build_earthwork_summary_rows(ifc_file_name):
    headers = [
        "Family",
        "Type",
        "Level",
        "Count",
        "Material:Name",
        "Material:Description",
        "Total Computed Volume (m³)",
    ]
    out = []
    rows = _get_cached_earthwork_data(ifc_file_name).get("summary_rows", [])

    for r in rows or []:
        vol = r.get("Total Computed Volume (m³)", r.get("Total Computed Volume (mÂ³)", "0"))
        try:
            vol_f = float(str(vol).replace(",", "").strip())
        except Exception:
            vol_f = 0.0
        out.append(
            {
                "Family": str(r.get("Family", "")),
                "Type": str(r.get("Type", "")),
                "Level": str(r.get("Level", "")),
                "Count": str(r.get("Count", "")),
                "Material:Name": str(r.get("Material:Name", "Earthwork")),
                "Material:Description": str(r.get("Material:Description", "")),
                "Total Computed Volume (m³)": _format_indian_number(vol_f, 6),
            }
        )
    return out


def _rows_to_sheet_rows(rows, headers):
    out = [headers]
    for r in rows or []:
        out.append(["" if r.get(h) is None else str(r.get(h)) for h in headers])
    return out


def _summary_only_rows(rows):
    out = []
    for r in rows or []:
        mat_name = str(r.get("Material:Name", "")).strip().lower()
        if mat_name.startswith("total for "):
            out.append(r)
    return out


def build_final_report_bytes(project_code, ifc_file_name, wastage_map=None):
    wastage_map = wastage_map or {}
    earthwork_rows, masonry_rows, plastering_rows, rcc_rows = fetch_qto_report(project_code, ifc_file_name)
    sor_code = get_project_sor_code(project_code, ifc_file_name)
    painting_desc_map = {}
    if sor_code:
        try:
            painting_desc_map = get_subpackage_description_map(sor_code, ["G1", "G2"])
        except Exception:
            painting_desc_map = {}
    all_rows = remap_qto_rows_by_name(
        (earthwork_rows or []) + (masonry_rows or []) + (plastering_rows or []) + (rcc_rows or []),
        sor_code,
    )
    earth_rows = _rows_for_work_item_prefix_from_sections("A", all_rows)
    pcc_rows = _rows_for_work_item_prefix_from_sections("B", all_rows)
    rcc_only_rows = [
        r for r in _rows_for_work_item_prefix_from_sections("C", all_rows)
        if not _is_excluded_rcc_row(
            r.get("Family", ""),
            r.get("Type", ""),
            r.get("Material:Name", ""),
            r.get("Material:Description", ""),
        )
    ]
    masonry_only_rows = _rows_for_work_item_prefix_from_sections("D", all_rows)
    plaster_only_rows = _rows_for_work_item_prefix_from_sections("E", all_rows)
    flooring_rows = _rows_for_work_item_prefix_from_sections("F", all_rows)

    masonry_merged = build_qto_merged_rows(masonry_only_rows, wastage_map=wastage_map, include_area=True)
    plaster_merged = build_qto_merged_rows(plaster_only_rows, wastage_map=wastage_map, include_area=True)
    rcc_merged = build_qto_merged_rows(rcc_only_rows, wastage_map=wastage_map, include_area=False)

    def _derive_painting_rows_from_plaster(rows):
        derived = []
        for r in rows or []:
            type_text = str(r.get("Type", "")).strip().lower()
            if not type_text:
                continue

            painting_code = ""
            painting_name = ""
            if "external wall" in type_text:
                painting_code = "G2"
                painting_name = "External Wall Painting"
            elif "internal wall" in type_text:
                painting_code = "G1"
                painting_name = "Internal Wall Painting"
            else:
                continue

            rr = dict(r)
            rr["Work Item Code"] = painting_code
            rr["Material:Name"] = painting_name
            rr["Material:Description"] = (
                painting_desc_map.get(painting_code)
                or rr.get("Material:Description")
                or painting_name
            )
            derived.append(rr)
        return derived

    painting_rows = _derive_painting_rows_from_plaster(plaster_only_rows)
    flooring_merged = build_qto_merged_rows(
        flooring_rows,
        wastage_map=wastage_map,
        include_area=True,
        flooring_mode=True,
    )
    painting_merged = build_qto_merged_rows(
        painting_rows,
        wastage_map=wastage_map,
        include_area=True,
        area_only=True,
    )
    earthwork_merged = build_qto_merged_rows(earth_rows, wastage_map=wastage_map, include_area=False)
    pcc_merged = build_qto_merged_rows(pcc_rows, wastage_map=wastage_map, include_area=True)

    qto_headers_with_area = [
        "Work Item Code",
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Wastage (%)",
        "Base Volume (m³)",
        "Wastage Volume (m³)",
        "Total Volume (m³)",
        "Total Area (m²)",
    ]
    qto_headers_no_area = [
        "Work Item Code",
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Wastage (%)",
        "Base Volume (m³)",
        "Wastage Volume (m³)",
        "Total Volume (m³)",
    ]
    painting_summary_headers = [
        "Work Item Code",
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Wastage (%)",
        "Base Area (m²)",
        "Wastage Area (m²)",
        "Total Area (m²)",
    ]
    flooring_summary_headers = [
        "Work Item Code",
        "Family",
        "Type",
        "Material:Name",
        "Material:Description",
        "Wastage (%)",
        "Total Volume (m³)",
        "Base Area (m²)",
        "Wastage Area (m²)",
        "Total Area (m²)",
    ]

    plastering_takeoff_rows_raw = fetch_table_rows(
        project_code,
        ifc_file_name,
        "plastering_material_takeoff",
        [
            "express_id",
            "global_id",
            "family",
            "type_name",
            "base_constraint",
            "length_val",
            "width_val",
            "material_name",
            "material_description",
            "material_area",
            "material_volume",
        ],
    )
    plastering_takeoff_rows = []
    if plastering_takeoff_rows_raw:
        plastering_takeoff_rows.append(plastering_takeoff_rows_raw[0])
        hdr = plastering_takeoff_rows_raw[0]
        idx = {name: i for i, name in enumerate(hdr)}
        for r in plastering_takeoff_rows_raw[1:]:
            family = r[idx["family"]] if "family" in idx else ""
            type_name = r[idx["type_name"]] if "type_name" in idx else ""
            mat_name = r[idx["material_name"]] if "material_name" in idx else ""
            mat_desc = r[idx["material_description"]] if "material_description" in idx else ""
            if _detect_flooring_code_and_name(family, type_name, mat_name, mat_desc)[0]:
                continue
            plastering_takeoff_rows.append(r)

    painting_takeoff_headers = [
        "express_id",
        "global_id",
        "family",
        "type_name",
        "base_constraint",
        "length_val",
        "width_val",
        "material_name",
        "material_description",
        "material_area",
    ]
    painting_takeoff_rows = [painting_takeoff_headers]
    if plastering_takeoff_rows:
        hdr = plastering_takeoff_rows[0]
        idx = {name: i for i, name in enumerate(hdr)}
        for r in plastering_takeoff_rows[1:]:
            type_text = str(r[idx["type_name"]]).strip().lower() if "type_name" in idx else ""
            if "external wall" in type_text:
                code = "G2"
                mat_name = "External Wall Painting"
            elif "internal wall" in type_text:
                code = "G1"
                mat_name = "Internal Wall Painting"
            else:
                continue

            out_row = [
                r[idx["express_id"]] if "express_id" in idx else "",
                r[idx["global_id"]] if "global_id" in idx else "",
                r[idx["family"]] if "family" in idx else "",
                r[idx["type_name"]] if "type_name" in idx else "",
                r[idx["base_constraint"]] if "base_constraint" in idx else "",
                r[idx["length_val"]] if "length_val" in idx else "",
                r[idx["width_val"]] if "width_val" in idx else "",
                mat_name,
                painting_desc_map.get(code, "")
                or (r[idx["material_description"]] if "material_description" in idx else "")
                or mat_name,
                r[idx["material_area"]] if "material_area" in idx else "",
            ]
            painting_takeoff_rows.append(out_row)

    flooring_takeoff_rows = build_flooring_takeoff_rows(
        project_code,
        ifc_file_name,
    )
    earthwork_takeoff_rows = build_earthwork_takeoff_rows(ifc_file_name)

    masonry_takeoff_rows = fetch_table_rows(
        project_code,
        ifc_file_name,
        "masonry_material_takeoff",
        [
            "express_id",
            "global_id",
            "family",
            "type_name",
            "base_constraint",
            "length_val",
            "width_val",
            "material_name",
            "material_description",
            "material_area",
            "material_volume",
        ],
    )
    rcc_takeoff_rows = fetch_table_rows(
        project_code,
        ifc_file_name,
        "rcc_material_takeoff",
        [
            "express_id",
            "global_id",
            "family",
            "type_name",
            "level_name",
            "material_name",
            "material_description",
            "material_volume",
        ],
    )

    def _has_takeoff_data(sheet_rows):
        return bool(sheet_rows and len(sheet_rows) > 1)

    sheets = []

    # Defined order: A, B, C, D, E, F, G (include only if data exists).
    if _has_takeoff_data(earthwork_takeoff_rows):
        sheets.append(("Earthwork_Takeoff", earthwork_takeoff_rows))
    if earthwork_merged:
        sheets.append(("Earthwork_Summary", _rows_to_sheet_rows(earthwork_merged, qto_headers_no_area)))

    if pcc_merged:
        sheets.append(("PCC_Summary", _rows_to_sheet_rows(pcc_merged, qto_headers_with_area)))

    if _has_takeoff_data(rcc_takeoff_rows):
        sheets.append(("RCC_Takeoff", rcc_takeoff_rows))
    if rcc_merged:
        sheets.append(("RCC_Summary", _rows_to_sheet_rows(rcc_merged, qto_headers_no_area)))

    if _has_takeoff_data(masonry_takeoff_rows):
        sheets.append(("Masonry_Takeoff", masonry_takeoff_rows))
    if masonry_merged:
        sheets.append(("Masonry_Summary", _rows_to_sheet_rows(masonry_merged, qto_headers_with_area)))

    if _has_takeoff_data(plastering_takeoff_rows):
        sheets.append(("Plastering_Takeoff", plastering_takeoff_rows))
    if plaster_merged:
        sheets.append(("Plastering_Summary", _rows_to_sheet_rows(plaster_merged, qto_headers_with_area)))

    if _has_takeoff_data(flooring_takeoff_rows):
        sheets.append(("Flooring_Takeoff", flooring_takeoff_rows))
    if flooring_merged:
        sheets.append(("Flooring_Summary", _rows_to_sheet_rows(flooring_merged, flooring_summary_headers)))

    if _has_takeoff_data(painting_takeoff_rows):
        sheets.append(("Painting_Takeoff", painting_takeoff_rows))
    if painting_merged:
        sheets.append(("Painting_Summary", _rows_to_sheet_rows(painting_merged, painting_summary_headers)))

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        Final_Report.build_workbook(sheets, tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Tender Estimation Model", layout="wide")

st.markdown(
    """
    <style>
    .stApp .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .main-title {
        font-size: 48px;
        font-weight: 800;
        text-align: center;
        margin: 0.5rem 0 1rem 0;
    }
    .section-title {
        font-size: 34px;
        font-weight: 700;
        text-align: center;
        margin: 1rem 0 0.75rem 0;
    }
    .hint {
        color: #555;
        margin-top: -0.3rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.4rem;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div {
        min-height: 2rem !important;
        font-size: 0.90rem !important;
    }
    div[data-baseweb="input"] {
        margin-bottom: 0.15rem;
    }
    hr {
        margin-top: 0.35rem !important;
        margin-bottom: 0.35rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">TENDER ESTIMATION MODEL</div>', unsafe_allow_html=True)

if "step" not in st.session_state:
    st.session_state.step = 1
if "draft_project" not in st.session_state:
    st.session_state.draft_project = None
if "draft_charges" not in st.session_state:
    st.session_state.draft_charges = None
if "draft_ifc_name" not in st.session_state:
    st.session_state.draft_ifc_name = None
if "draft_ifc_bytes" not in st.session_state:
    st.session_state.draft_ifc_bytes = None
if "result_project_code" not in st.session_state:
    st.session_state.result_project_code = None
if "result_ifc_file_name" not in st.session_state:
    st.session_state.result_ifc_file_name = None
if "qto_wastage_map" not in st.session_state:
    st.session_state.qto_wastage_map = {}

# Load SOR codes from sor_data
try:
    sor_rows = get_sor_options()
except Exception as e:
    sor_rows = []
    st.error(f"Could not load SOR list from sor_data: {e}")

sor_labels = [r["label"] for r in sor_rows]
sor_map = {r["label"]: r["sor_code"] for r in sor_rows}

if st.session_state.step == 1:
    draft = st.session_state.draft_project or {}
    default_sor_label = sor_labels[0] if sor_labels else "No SOR data found"
    if sor_labels and draft.get("sor_database"):
        for lbl, code in sor_map.items():
            if code == draft.get("sor_database"):
                default_sor_label = lbl
                break

    with st.form("project_entry_form", clear_on_submit=False):
        st.markdown('<div class="section-title">Project Data Entry</div>', unsafe_allow_html=True)

        project_name = st.text_input(
            "Project Name",
            value=draft.get("project_name", ""),
            placeholder="Type the Project Name",
        )
        project_location = st.text_input(
            "Project Location",
            value=draft.get("project_location", ""),
            placeholder="Type the Project Location Address",
        )
        client_name = st.text_input(
            "Client Name",
            value=draft.get("client_name", ""),
            placeholder="Type the Client Name",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            site_area = st.number_input(
                "Site Area (Sq.M)",
                min_value=0.0,
                step=1.0,
                format="%.3f",
                value=float(draft.get("site_area", 0.0)),
            )
        with c2:
            total_builtup_area = st.number_input(
                "Total Built-Up Area (Sq.M)",
                min_value=0.0,
                step=1.0,
                format="%.3f",
                value=float(draft.get("total_builtup_area", 0.0)),
            )
        with c3:
            building_height = st.number_input(
                "Building Height (M)",
                min_value=0.0,
                step=0.1,
                format="%.3f",
                value=float(draft.get("building_height", 0.0)),
            )

        date_of_issue = st.date_input("Date of Issue", value=draft.get("date_of_issue", date.today()))
        estimator_name = st.text_input(
            "Estimation Done By",
            value=draft.get("estimator_name", ""),
            placeholder="Type Your Name",
        )

        st.markdown('<div class="section-title">Project Model Entry</div>', unsafe_allow_html=True)

        ifc_file = st.file_uploader("Select IFC File", type=["ifc"])
        if st.session_state.draft_ifc_name:
            st.caption(f"Selected IFC (draft): {st.session_state.draft_ifc_name}")
        sor_label = st.selectbox(
            "Select SOR Database",
            sor_labels if sor_labels else ["No SOR data found"],
            index=(sor_labels.index(default_sor_label) if sor_labels else 0),
            disabled=(len(sor_labels) == 0),
        )

        c_spacer, c_next = st.columns([6.6, 1.4])
        with c_next:
            submitted = st.form_submit_button("Next", type="primary", use_container_width=True)

    if submitted:
        if not project_name.strip():
            st.warning("Project Name is required.")
            st.stop()
        if not project_location.strip():
            st.warning("Project Location is required.")
            st.stop()
        if not client_name.strip():
            st.warning("Client Name is required.")
            st.stop()
        if not estimator_name.strip():
            st.warning("Estimator Name is required.")
            st.stop()
        if not sor_labels:
            st.warning("SOR list is empty. Please insert rows in sor_data first.")
            st.stop()
        if not ifc_file and not st.session_state.draft_ifc_bytes:
            st.warning("Please upload an IFC file.")
            st.stop()

        if ifc_file:
            st.session_state.draft_ifc_name = ifc_file.name
            st.session_state.draft_ifc_bytes = ifc_file.getvalue()

        project_code = draft.get("project_code") or f"PRJ-{uuid.uuid4().hex[:8].upper()}"
        st.session_state.draft_project = {
            "project_code": project_code,
            "project_name": project_name.strip(),
            "project_location": project_location.strip(),
            "client_name": client_name.strip(),
            "site_area": site_area,
            "total_builtup_area": total_builtup_area,
            "building_height": building_height,
            "date_of_issue": date_of_issue,
            "estimator_name": estimator_name.strip(),
            "sor_database": sor_map[sor_label],
        }
        st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    st.markdown('<div class="section-title">Additional Charges</div>', unsafe_allow_html=True)

    if st.session_state.draft_charges is None:
        try:
            charge_rows = get_work_item_charges()
        except Exception as e:
            st.error(f"Could not load work_item_charges: {e}")
            st.stop()
        st.session_state.draft_charges = charge_rows

    charge_rows = st.session_state.draft_charges
    if not charge_rows:
        st.warning("No rows found in work_item_charges.")
        st.stop()

    with st.form("additional_charges_form", clear_on_submit=False):
        updated_rows = []
        for row in charge_rows:
            key = f"charge_{row['id']}"
            charge_label = row.get("charge_name") or f"Charge {row['id']}"
            val = st.number_input(
                f"{charge_label} @",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=float(row["percentage"]),
                key=key,
                help="Default value - can be changed",
            )
            updated_rows.append({"id": row["id"], "charge_name": charge_label, "percentage": val})

        c_prev, c_spacer, c_next = st.columns([1.4, 5.2, 1.4])
        with c_prev:
            prev_clicked = st.form_submit_button("Previous", use_container_width=True)
        with c_next:
            next_clicked = st.form_submit_button("Next", type="primary", use_container_width=True)

    if prev_clicked:
        st.session_state.draft_charges = updated_rows
        st.session_state.step = 1
        st.rerun()
    if next_clicked:
        st.session_state.draft_charges = updated_rows
        try:
            existing_ifc_name = None
            if (
                st.session_state.result_project_code
                and st.session_state.result_project_code == st.session_state.draft_project.get("project_code")
            ):
                existing_ifc_name = st.session_state.result_ifc_file_name

            project_code, ifc_file_name = persist_project_and_qto(
                st.session_state.draft_project,
                st.session_state.draft_ifc_bytes,
                st.session_state.draft_ifc_name,
                st.session_state.draft_charges,
                existing_ifc_file_name=existing_ifc_name,
            )
            st.session_state.result_project_code = project_code
            st.session_state.result_ifc_file_name = ifc_file_name
            st.session_state.qto_wastage_map = {}
            st.session_state.step = 3
            st.rerun()
        except Exception as e:
            st.error(f"Failed to process and save project/QTO data: {e}")

elif st.session_state.step == 3:
    st.markdown('<div class="section-title">Work Item Wastage</div>', unsafe_allow_html=True)
    project_code = st.session_state.result_project_code
    ifc_file_name = st.session_state.result_ifc_file_name
    if not project_code or not ifc_file_name:
        st.warning("No processed project result found. Please complete previous steps.")
        if st.button("Back to Step 1"):
            st.session_state.step = 1
            st.rerun()
        st.stop()

    st.caption("Set wastage % for each Work Item Code (defaults are loaded from database).")

    try:
        earthwork_rows, masonry_rows, plastering_rows, rcc_rows = fetch_qto_report(project_code, ifc_file_name)
    except Exception as e:
        st.error(f"Failed to load Work Item Codes: {e}")
        st.stop()

    sor_code = get_project_sor_code(project_code, ifc_file_name)
    remapped_for_wastage = remap_qto_rows_by_name(
        (earthwork_rows or []) + (masonry_rows or []) + (plastering_rows or []) + (rcc_rows or []),
        sor_code,
    )
    work_item_codes = extract_unique_work_item_codes(remapped_for_wastage)
    for _fixed_code in ("A1", "G1", "G2"):
        if _fixed_code not in work_item_codes:
            work_item_codes.append(_fixed_code)
    if not work_item_codes:
        st.warning("No Work Item Codes found in generated QTO data.")
        st.stop()
    if not sor_code:
        st.error("Could not resolve SOR code for this project.")
        st.stop()

    try:
        db_default_map = get_or_init_wastage_defaults(sor_code, work_item_codes)
    except Exception as e:
        st.error(f"Failed to load default wastage values: {e}")
        st.stop()
    try:
        subpackage_name_map = get_subpackage_name_map(sor_code, work_item_codes)
    except Exception as e:
        st.error(f"Failed to load subpackage names: {e}")
        st.stop()

    current_map = st.session_state.get("qto_wastage_map", {})
    initial_map = dict(db_default_map)
    initial_map.update(current_map)
    with st.form("work_item_wastage_form", clear_on_submit=False):
        updated_map = {}
        for code in work_item_codes:
            default_pct = _get_wastage_pct(initial_map, code, default_pct=float(db_default_map.get(code, 0.0)))
            subpackage_name = subpackage_name_map.get(code, "").strip()
            label = f"{code} - {subpackage_name} - Wastage (%)" if subpackage_name else f"{code} - Wastage (%)"
            pct = st.number_input(
                label,
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=float(default_pct),
                key=f"wastage_code_{code}",
            )
            updated_map[code] = float(pct)

        c_prev, c_spacer, c_next = st.columns([1.4, 5.2, 1.4])
        with c_prev:
            prev_clicked = st.form_submit_button("Previous", use_container_width=True)
        with c_next:
            next_clicked = st.form_submit_button("Next", type="primary", use_container_width=True)

    if prev_clicked:
        st.session_state.step = 2
        st.rerun()
    if next_clicked:
        try:
            save_wastage_defaults(sor_code, updated_map)
        except Exception as e:
            st.error(f"Failed to save wastage values: {e}")
            st.stop()
        st.session_state.qto_wastage_map = updated_map
        st.session_state.step = 4
        st.rerun()

elif st.session_state.step == 4:
    st.markdown('<div class="section-title">QTO Report</div>', unsafe_allow_html=True)
    project_code = st.session_state.result_project_code
    ifc_file_name = st.session_state.result_ifc_file_name
    if not project_code or not ifc_file_name:
        st.warning("No processed project result found. Please complete previous steps.")
        if st.button("Back to Step 1"):
            st.session_state.step = 1
            st.rerun()
        st.stop()

    st.caption(f"Project: {project_code} | IFC: {ifc_file_name}")

    try:
        earthwork_rows, masonry_rows, plastering_rows, rcc_rows = fetch_qto_report(project_code, ifc_file_name)
    except Exception as e:
        st.error(f"Failed to load QTO report: {e}")
        st.stop()

    wastage_map = st.session_state.get("qto_wastage_map", {})
    sor_code = get_project_sor_code(project_code, ifc_file_name)
    painting_desc_map = {}
    if sor_code:
        try:
            painting_desc_map = get_subpackage_description_map(sor_code, ["G1", "G2"])
        except Exception:
            painting_desc_map = {}
    def _derive_painting_rows_from_plaster(rows):
        derived = []
        for r in rows or []:
            type_text = str(r.get("Type", "")).strip().lower()
            if not type_text:
                continue

            painting_code = ""
            painting_name = ""
            if "external wall" in type_text:
                painting_code = "G2"
                painting_name = "External Wall Painting"
            elif "internal wall" in type_text:
                painting_code = "G1"
                painting_name = "Internal Wall Painting"
            else:
                continue

            rr = dict(r)
            rr["Work Item Code"] = painting_code
            rr["Material:Name"] = painting_name
            rr["Material:Description"] = (
                painting_desc_map.get(painting_code)
                or rr.get("Material:Description")
                or painting_name
            )
            derived.append(rr)
        return derived

    all_rows = remap_qto_rows_by_name(
        (earthwork_rows or []) + (masonry_rows or []) + (plastering_rows or []) + (rcc_rows or []),
        sor_code,
    )
    earth_rows = _rows_for_work_item_prefix_from_sections("A", all_rows)
    pcc_rows = _rows_for_work_item_prefix_from_sections("B", all_rows)
    rcc_only_rows = [
        r for r in _rows_for_work_item_prefix_from_sections("C", all_rows)
        if not _is_excluded_rcc_row(
            r.get("Family", ""),
            r.get("Type", ""),
            r.get("Material:Name", ""),
            r.get("Material:Description", ""),
        )
    ]
    masonry_only_rows = _rows_for_work_item_prefix_from_sections("D", all_rows)
    plaster_only_rows = _rows_for_work_item_prefix_from_sections("E", all_rows)
    flooring_rows = _rows_for_work_item_prefix_from_sections("F", all_rows)
    painting_rows = _derive_painting_rows_from_plaster(plaster_only_rows)

    section_definitions = [
        ("A - Earth Work", earth_rows, False, "qto_earth"),
        ("B - PCC Work", pcc_rows, True, "qto_pcc"),
        ("C - RCC Work", rcc_only_rows, False, "qto_rcc"),
        ("D - Masonry Work", masonry_only_rows, True, "qto_masonry"),
        ("E - Plastering Work", plaster_only_rows, True, "qto_plaster"),
        ("F - Flooring Work", flooring_rows, True, "qto_flooring"),
        ("G - Painting Work", painting_rows, True, "qto_painting"),
    ]
    rendered_any_section = False
    for title, rows, include_area, key_prefix in section_definitions:
        if not rows:
            continue
        area_only = key_prefix == "qto_painting"
        flooring_mode = key_prefix == "qto_flooring"
        merged_rows = build_qto_merged_rows(
            rows,
            wastage_map=wastage_map,
            include_area=include_area,
            area_only=area_only,
            flooring_mode=flooring_mode,
        )
        if not merged_rows:
            continue
        rendered_any_section = True
        st.subheader(title)
        render_qto_merged_table(
            merged_rows,
            f"{key_prefix}_merged",
            include_area=include_area,
            area_only=area_only,
            flooring_mode=flooring_mode,
        )

    if not rendered_any_section:
        st.info("No QTO records found for this project.")

    st.markdown("---")
    try:
        report_bytes = build_final_report_bytes(project_code, ifc_file_name, wastage_map=wastage_map)
        _exp_spacer, _exp_btn_col = st.columns([6.6, 1.4])
        with _exp_btn_col:
            st.download_button(
                "Export Final Report",
                data=report_bytes,
                file_name=f"{project_code}_{ifc_file_name}_final_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    except Exception as e:
        st.error(f"Failed to build export report: {e}")

    c_prev, c_spacer, c_next = st.columns([1.4, 5.2, 1.4])
    with c_prev:
        if st.button("Previous", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with c_next:
        if st.button("Next", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()

elif st.session_state.step == 5:
    project_code = st.session_state.result_project_code
    ifc_file_name = st.session_state.result_ifc_file_name
    if not project_code or not ifc_file_name:
        st.warning("No processed project result found.")
        if st.button("Back to Step 1"):
            st.session_state.step = 1
            st.rerun()
        st.stop()

    st.markdown('<div class="section-title">Tender Estimate</div>', unsafe_allow_html=True)
    try:
        project, estimate_rows, grand_total = build_tender_estimate(
            project_code,
            ifc_file_name,
            wastage_map=st.session_state.get("qto_wastage_map", {}),
        )
    except Exception as e:
        st.error(f"Failed to build tender estimate: {e}")
        st.stop()

    if not project:
        st.warning("Project details not found.")
        st.stop()

    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Project Name:** {project.get('project_name','')}")
        st.write(f"**Project Location:** {project.get('project_location','')}")
        _site_area = project.get("site_area", "")
        _total_builtup = project.get("total_builtup_area", "")
        _height = project.get("building_height", "")
        st.write(f"**Site Area:** {_format_indian_number(_site_area, 3) if _site_area not in ('', None) else ''}")
        st.write(f"**Total Built-Up Area:** {_format_indian_number(_total_builtup, 3) if _total_builtup not in ('', None) else ''}")
        st.write(f"**Building Height:** {_format_indian_number(_height, 3) if _height not in ('', None) else ''}")
    with c2:
        est = html.escape(str(project.get("estimator_name", "")))
        client = html.escape(str(project.get("client_name", "")))
        doi = html.escape(str(project.get("date_of_issue", "")))
        st.markdown(f"<div style='text-align:right;'><b>Estimator By:</b> {est}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;'><b>Client Name:</b> {client}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:right;'><b>Date of Issue:</b> {doi}</div>", unsafe_allow_html=True)

    if estimate_rows:
        render_tender_table_qto_style(estimate_rows, "tender_table")
        st.markdown(
            f"<div style='text-align:right; font-size:1.2rem; font-weight:700;'>Grand Total: {_format_inr(grand_total)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        excel_bytes = build_tender_estimate_excel_bytes(estimate_rows, grand_total)
        _exp_spacer, _exp_btn_col = st.columns([6.6, 1.4])
        with _exp_btn_col:
            st.download_button(
                "Export Rate Table",
                data=excel_bytes,
                file_name=f"{project_code}_{ifc_file_name}_tender_estimate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.info("No estimate rows could be generated from current summaries.")

    c_prev, c_spacer, c_reset = st.columns([1.4, 5.2, 1.4])
    with c_prev:
        if st.button("Previous", use_container_width=True):
            st.session_state.step = 4
            st.rerun()
    with c_reset:
        if st.button("Start New Project", use_container_width=True):
            st.session_state.step = 1
            st.session_state.draft_project = None
            st.session_state.draft_charges = None
            st.session_state.draft_ifc_name = None
            st.session_state.draft_ifc_bytes = None
            st.session_state.result_project_code = None
            st.session_state.result_ifc_file_name = None
            st.session_state.qto_wastage_map = {}
            st.rerun()
