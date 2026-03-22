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
import Final_Report


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
        wall_rows = Wall.build_rows(model)
        rcc_rows = RCC.build_rows(model)
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
        pkg = resolve_package_name(row.get("Material:Name", ""), mappings)
        if pkg == "Masonry Work":
            masonry_rows.append(row)
        elif pkg in ("PCC Work", "Plastering Work"):
            plaster_rows.append(row)

    for row in rcc_rows:
        pkg = resolve_package_name(row.get("Material:Name", ""), mappings)
        if pkg == "RCC Work":
            rcc_takeoff_rows.append(row)

    conn = get_conn()
    try:
        cur = conn.cursor()

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
                    for row in plaster_rows
                ],
            )

        if rcc_takeoff_rows:
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
                    for row in rcc_takeoff_rows
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
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT material_name AS `Material:Name`,
                   material_description AS `Material:Description`,
                   ROUND(total_material_area,2) AS `Total Area`,
                   ROUND(total_material_volume,2) AS `Total Volume`
            FROM masonry_summary
            WHERE project_code=%s AND ifc_file_name=%s
            ORDER BY material_name
            """,
            (project_code, ifc_file_name),
        )
        masonry = cur.fetchall()

        cur.execute(
            """
            SELECT material_name AS `Material:Name`,
                   material_description AS `Material:Description`,
                   ROUND(total_material_area,2) AS `Total Area`,
                   ROUND(total_material_volume,2) AS `Total Volume`
            FROM plastering_summary
            WHERE project_code=%s AND ifc_file_name=%s
            ORDER BY material_name
            """,
            (project_code, ifc_file_name),
        )
        plastering = cur.fetchall()

        cur.execute(
            """
            SELECT material_name AS `Material:Name`,
                   material_description AS `Material:Description`,
                   ROUND(total_material_volume,2) AS `Total Volume`
            FROM rcc_summary
            WHERE project_code=%s AND ifc_file_name=%s
            ORDER BY material_name
            """,
            (project_code, ifc_file_name),
        )
        rcc = cur.fetchall()

        return masonry, plastering, rcc
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


def build_tender_estimate(project_code, ifc_file_name):
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

            amount = qty * price
            key = (code, item, unit, price)
            if key not in grouped:
                grouped[key] = {"qty": 0.0, "amount": 0.0}
            grouped[key]["qty"] += qty
            grouped[key]["amount"] += amount

        rows = []
        grand_total = 0.0
        for (code, item, unit, price), vals in grouped.items():
            qty = vals["qty"]
            amount = vals["amount"]
            grand_total += amount
            rows.append(
                {
                    "Work Item Code": code,
                    "Item": item,
                    "Area / Volume": f"{qty:,.3f}",
                    "Unit": unit,
                    "Price": f"{price:,.2f}",
                    "Amount": f"{amount:,.2f}",
                }
            )

        return project, rows, grand_total
    finally:
        conn.close()


def build_tender_estimate_csv_bytes(rows, grand_total):
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["Work Item Code", "Item", "Area / Volume", "Unit", "Price", "Amount"]
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    writer.writerow([])
    writer.writerow(["", "", "", "", "Grand Total", f"{grand_total:,.2f}"])
    return output.getvalue().encode("utf-8")


def render_simple_table(rows):
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
    table_html = f"""
    <style>
      .formal-table-wrap {{
        overflow-x: auto;
        margin-bottom: 1rem;
      }}
      .formal-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid #c9c9c9;
        border-radius: 10px;
        overflow: hidden;
        background: #ffffff;
        color: #111111;
        font-size: 15px;
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
        padding: 10px 12px;
        white-space: nowrap;
      }}
      .formal-table td {{
        color: #111111 !important;
        padding: 10px 12px;
        border-bottom: 1px solid #ececec;
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


def build_final_report_bytes(project_code, ifc_file_name):
    sheets = [
        (
            "Masonry_Takeoff",
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
                    "length_val",
                    "width_val",
                    "material_name",
                    "material_description",
                    "material_area",
                    "material_volume",
                ],
            ),
        ),
        (
            "Masonry_Summary",
            fetch_table_rows(
                project_code,
                ifc_file_name,
                "masonry_summary",
                [
                    "material_name",
                    "material_description",
                    "total_material_area",
                    "total_material_volume",
                ],
            ),
        ),
        (
            "Plastering_Takeoff",
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
                    "length_val",
                    "width_val",
                    "material_name",
                    "material_description",
                    "material_area",
                    "material_volume",
                ],
            ),
        ),
        (
            "Plastering_Summary",
            fetch_table_rows(
                project_code,
                ifc_file_name,
                "plastering_summary",
                [
                    "material_name",
                    "material_description",
                    "total_material_area",
                    "total_material_volume",
                ],
            ),
        ),
        (
            "RCC_Takeoff",
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
        ),
        (
            "RCC_Summary",
            fetch_table_rows(
                project_code,
                ifc_file_name,
                "rcc_summary",
                [
                    "material_name",
                    "material_description",
                    "total_material_volume",
                ],
            ),
        ),
    ]

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
st.set_page_config(page_title="Tender Estimation Model", layout="centered")

st.markdown(
    """
    <style>
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
                "Site Area",
                min_value=0.0,
                step=1.0,
                format="%.3f",
                value=float(draft.get("site_area", 0.0)),
            )
        with c2:
            total_builtup_area = st.number_input(
                "Total Built-Up Area",
                min_value=0.0,
                step=1.0,
                format="%.3f",
                value=float(draft.get("total_builtup_area", 0.0)),
            )
        with c3:
            building_height = st.number_input(
                "Building Height",
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

        submitted = st.form_submit_button("Next", type="primary")

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

        c_prev, c_next = st.columns(2)
        with c_prev:
            prev_clicked = st.form_submit_button("Previous")
        with c_next:
            next_clicked = st.form_submit_button("Next", type="primary")

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
            st.session_state.step = 3
            st.rerun()
        except Exception as e:
            st.error(f"Failed to process and save project/QTO data: {e}")

elif st.session_state.step == 3:
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
        masonry_rows, plastering_rows, rcc_rows = fetch_qto_report(project_code, ifc_file_name)
    except Exception as e:
        st.error(f"Failed to load QTO report: {e}")
        st.stop()

    st.subheader("D - Masonry Work")
    if masonry_rows:
        render_simple_table(masonry_rows)
    else:
        st.info("No masonry records found for this project.")

    st.subheader("F - Plastering Work")
    if plastering_rows:
        render_simple_table(plastering_rows)
    else:
        st.info("No plastering records found for this project.")

    st.subheader("C - RCC Work")
    if rcc_rows:
        render_simple_table(rcc_rows)
    else:
        st.info("No RCC records found for this project.")

    st.markdown("---")
    try:
        report_bytes = build_final_report_bytes(project_code, ifc_file_name)
        st.download_button(
            "Export Final Report",
            data=report_bytes,
            file_name=f"{project_code}_{ifc_file_name}_final_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Failed to build export report: {e}")

    c_prev, c_next = st.columns(2)
    with c_prev:
        if st.button("Previous"):
            st.session_state.step = 2
            st.rerun()
    with c_next:
        if st.button("Next", type="primary"):
            st.session_state.step = 4
            st.rerun()

elif st.session_state.step == 4:
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
        project, estimate_rows, grand_total = build_tender_estimate(project_code, ifc_file_name)
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
        st.write(f"**Site Area:** {project.get('site_area','')}")
        st.write(f"**Total Built-Up Area:** {project.get('total_builtup_area','')}")
        st.write(f"**Building Height:** {project.get('building_height','')}")
    with c2:
        st.write(f"**Estimator By:** {project.get('estimator_name','')}")
        st.write(f"**Client Name:** {project.get('client_name','')}")
        st.write(f"**Date of Issue:** {project.get('date_of_issue','')}")

    if estimate_rows:
        render_simple_table(estimate_rows)
        st.markdown(f"### Grand Total: {grand_total:,.2f}")
        csv_bytes = build_tender_estimate_csv_bytes(estimate_rows, grand_total)
        st.download_button(
            "Export Rate Table (CSV)",
            data=csv_bytes,
            file_name=f"{project_code}_{ifc_file_name}_tender_estimate.csv",
            mime="text/csv",
        )
    else:
        st.info("No estimate rows could be generated from current summaries.")

    c_prev, c_reset = st.columns(2)
    with c_prev:
        if st.button("Previous"):
            st.session_state.step = 3
            st.rerun()
    with c_reset:
        if st.button("Start New Project"):
            st.session_state.step = 1
            st.session_state.draft_project = None
            st.session_state.draft_charges = None
            st.session_state.draft_ifc_name = None
            st.session_state.draft_ifc_bytes = None
            st.session_state.result_project_code = None
            st.session_state.result_ifc_file_name = None
            st.rerun()
