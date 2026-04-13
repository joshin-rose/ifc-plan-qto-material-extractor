import os

import mysql.connector
import pandas as pd
import streamlit as st


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "architect")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ap@2101")
DB_NAME = os.getenv("DB_NAME", "arch_db")


def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )


def load_sor_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, state_name, year, name, created_at
            FROM sor_data
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def save_sor_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            if not sor_code:
                continue

            state_name = None if pd.isna(row.get("state_name")) else str(row.get("state_name")).strip()
            name = None if pd.isna(row.get("name")) else str(row.get("name")).strip()

            year_val = row.get("year")
            year = None
            if pd.notna(year_val) and str(year_val).strip() != "":
                year = int(float(year_val))

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            if has_id:
                cur.execute(
                    """
                    UPDATE sor_data
                    SET sor_code=%s, state_name=%s, year=%s, name=%s
                    WHERE id=%s
                    """,
                    (sor_code, state_name, year, name, int(float(id_val))),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sor_data (sor_code, state_name, year, name)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        state_name=VALUES(state_name),
                        year=VALUES(year),
                        name=VALUES(name)
                    """,
                    (sor_code, state_name, year, name),
                )

        conn.commit()
    finally:
        conn.close()


def load_labour_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, category_code, unique_code, description, unit, base_rate
            FROM sor_labour_data
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def load_labour_categories():
    conn = get_conn()
    try:
        query = """
            SELECT sor_code, category_code, category_name
            FROM sor_labour_category
            ORDER BY sor_code, category_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=120)
def load_material_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, category_code, subcategory_name, unique_code, description, unit, unit_multiplier, base_rate
            FROM sor_material_data
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_material_categories():
    conn = get_conn()
    try:
        query = """
            SELECT sor_code, category_code, category_name
            FROM sor_material_category
            ORDER BY sor_code, category_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_material_subcategories_by_category(category_code):
    conn = get_conn()
    try:
        query = """
            SELECT subcategory_name
            FROM sor_material_subcategory
            WHERE category_code = %s
            ORDER BY subcategory_name
        """
        return pd.read_sql(query, conn, params=(category_code,))
    finally:
        conn.close()


def load_equipment_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, unique_code, description, unit, base_rate
            FROM sor_equipment_data
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def load_work_item_package_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, package_code, package_name
            FROM work_item_package
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def load_work_item_subpackage_data():
    conn = get_conn()
    try:
        query = """
            SELECT id, sor_code, package_code, subpackage_code, subpackage_name, description, analysis_quantity, analysis_unit
            FROM work_item_subpackage
            ORDER BY id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def load_lead_lift_item_master_data():
    conn = get_conn()
    try:
        query = """
            SELECT sor_code, ll_code, item_name, profile_code, distance_km
            FROM lead_lift_item_master
            ORDER BY sor_code, ll_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def get_work_item_analysis_columns():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SHOW COLUMNS FROM work_item_analysis")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def load_work_item_analysis_data():
    conn = get_conn()
    try:
        query = """
            SELECT *
            FROM work_item_analysis
            ORDER BY sor_code, subpackage_code, id
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_material_code_lookup():
    conn = get_conn()
    try:
        query = """
            SELECT
                m.unique_code,
                COALESCE(c.category_name, '') AS category_name,
                COALESCE(m.subcategory_name, '') AS subcategory_name,
                COALESCE(m.description, '') AS description
            FROM sor_material_data m
            LEFT JOIN sor_material_category c
              ON c.sor_code = m.sor_code
             AND c.category_code = m.category_code
            ORDER BY m.unique_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_labour_code_lookup():
    conn = get_conn()
    try:
        query = """
            SELECT
                l.unique_code,
                COALESCE(c.category_name, '') AS category_name,
                COALESCE(l.description, '') AS description
            FROM sor_labour_data l
            LEFT JOIN sor_labour_category c
              ON c.sor_code = l.sor_code
             AND c.category_code = l.category_code
            ORDER BY l.unique_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_equipment_code_lookup():
    conn = get_conn()
    try:
        query = """
            SELECT unique_code, COALESCE(description, '') AS description
            FROM sor_equipment_data
            ORDER BY unique_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


@st.cache_data(show_spinner=False, ttl=300)
def load_lead_lift_code_lookup():
    conn = get_conn()
    try:
        query = """
            SELECT ll_code, COALESCE(item_name, '') AS item_name
            FROM lead_lift_item_master
            ORDER BY ll_code
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def save_labour_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            category_code = "" if pd.isna(row.get("category_code")) else str(row.get("category_code")).strip()
            unique_code = "" if pd.isna(row.get("unique_code")) else str(row.get("unique_code")).strip()
            description = None if pd.isna(row.get("description")) else str(row.get("description")).strip()
            unit = None if pd.isna(row.get("unit")) else str(row.get("unit")).strip()

            base_rate_val = row.get("base_rate")
            base_rate = None
            if pd.notna(base_rate_val) and str(base_rate_val).strip() != "":
                base_rate = float(base_rate_val)

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            # Ignore blank dynamic rows from the editor.
            if not has_id and not sor_code and not category_code and not unique_code and description in (None, "") and unit in (None, "") and base_rate is None:
                continue

            if not unique_code:
                raise ValueError("unique_code is required for each labour row.")

            if has_id:
                cur.execute(
                    """
                    UPDATE sor_labour_data
                    SET sor_code=%s, category_code=%s, unique_code=%s, description=%s, unit=%s, base_rate=%s
                    WHERE id=%s
                    """,
                    (sor_code or None, category_code or None, unique_code, description, unit, base_rate, int(float(id_val))),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sor_labour_data (sor_code, category_code, unique_code, description, unit, base_rate)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sor_code=VALUES(sor_code),
                        category_code=VALUES(category_code),
                        description=VALUES(description),
                        unit=VALUES(unit),
                        base_rate=VALUES(base_rate)
                    """,
                    (sor_code or None, category_code or None, unique_code, description, unit, base_rate),
                )

        conn.commit()
    finally:
        conn.close()


def save_material_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            category_code = "" if pd.isna(row.get("category_code")) else str(row.get("category_code")).strip()
            subcategory_name = None if pd.isna(row.get("subcategory_name")) else str(row.get("subcategory_name")).strip()
            unique_code = "" if pd.isna(row.get("unique_code")) else str(row.get("unique_code")).strip()
            description = None if pd.isna(row.get("description")) else str(row.get("description")).strip()
            unit = None if pd.isna(row.get("unit")) else str(row.get("unit")).strip()

            unit_multiplier_val = row.get("unit_multiplier")
            unit_multiplier = None
            if pd.notna(unit_multiplier_val) and str(unit_multiplier_val).strip() != "":
                unit_multiplier = int(float(unit_multiplier_val))

            base_rate_val = row.get("base_rate")
            base_rate = None
            if pd.notna(base_rate_val) and str(base_rate_val).strip() != "":
                base_rate = float(base_rate_val)

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            # Ignore blank dynamic rows.
            if not has_id and not sor_code and not category_code and not unique_code and description in (None, "") and unit in (None, "") and base_rate is None:
                continue

            if not unique_code:
                raise ValueError("unique_code is required for each material row.")

            if has_id:
                cur.execute(
                    """
                    UPDATE sor_material_data
                    SET sor_code=%s, category_code=%s, subcategory_name=%s, unique_code=%s, description=%s, unit=%s, unit_multiplier=%s, base_rate=%s
                    WHERE id=%s
                    """,
                    (
                        sor_code or None,
                        category_code or None,
                        subcategory_name or None,
                        unique_code,
                        description,
                        unit,
                        unit_multiplier,
                        base_rate,
                        int(float(id_val)),
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sor_material_data (sor_code, category_code, subcategory_name, unique_code, description, unit, unit_multiplier, base_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sor_code=VALUES(sor_code),
                        category_code=VALUES(category_code),
                        subcategory_name=VALUES(subcategory_name),
                        description=VALUES(description),
                        unit=VALUES(unit),
                        unit_multiplier=VALUES(unit_multiplier),
                        base_rate=VALUES(base_rate)
                    """,
                    (
                        sor_code or None,
                        category_code or None,
                        subcategory_name or None,
                        unique_code,
                        description,
                        unit,
                        unit_multiplier,
                        base_rate,
                    ),
                )

        conn.commit()
    finally:
        conn.close()


def save_equipment_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            unique_code = "" if pd.isna(row.get("unique_code")) else str(row.get("unique_code")).strip()
            description = None if pd.isna(row.get("description")) else str(row.get("description")).strip()
            unit = None if pd.isna(row.get("unit")) else str(row.get("unit")).strip()

            base_rate_val = row.get("base_rate")
            base_rate = None
            if pd.notna(base_rate_val) and str(base_rate_val).strip() != "":
                base_rate = float(base_rate_val)

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            if not has_id and not sor_code and not unique_code and description in (None, "") and unit in (None, "") and base_rate is None:
                continue

            if not unique_code:
                raise ValueError("unique_code is required for each equipment row.")

            if has_id:
                cur.execute(
                    """
                    UPDATE sor_equipment_data
                    SET sor_code=%s, unique_code=%s, description=%s, unit=%s, base_rate=%s
                    WHERE id=%s
                    """,
                    (sor_code or None, unique_code, description, unit, base_rate, int(float(id_val))),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO sor_equipment_data (sor_code, unique_code, description, unit, base_rate)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        sor_code=VALUES(sor_code),
                        description=VALUES(description),
                        unit=VALUES(unit),
                        base_rate=VALUES(base_rate)
                    """,
                    (sor_code or None, unique_code, description, unit, base_rate),
                )

        conn.commit()
    finally:
        conn.close()


def save_work_item_package_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            package_code = "" if pd.isna(row.get("package_code")) else str(row.get("package_code")).strip()
            package_name = None if pd.isna(row.get("package_name")) else str(row.get("package_name")).strip()

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            if not has_id and not sor_code and not package_code and package_name in (None, ""):
                continue

            if not sor_code or not package_code:
                raise ValueError("sor_code and package_code are required for each work_item_package row.")

            if has_id:
                cur.execute(
                    """
                    UPDATE work_item_package
                    SET sor_code=%s, package_code=%s, package_name=%s
                    WHERE id=%s
                    """,
                    (sor_code, package_code, package_name, int(float(id_val))),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO work_item_package (sor_code, package_code, package_name)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        package_name=VALUES(package_name)
                    """,
                    (sor_code, package_code, package_name),
                )

        conn.commit()
    finally:
        conn.close()


def save_work_item_subpackage_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            package_code = "" if pd.isna(row.get("package_code")) else str(row.get("package_code")).strip()
            subpackage_code = "" if pd.isna(row.get("subpackage_code")) else str(row.get("subpackage_code")).strip()
            subpackage_name = None if pd.isna(row.get("subpackage_name")) else str(row.get("subpackage_name")).strip()
            description = None if pd.isna(row.get("description")) else str(row.get("description")).strip()
            analysis_unit = None if pd.isna(row.get("analysis_unit")) else str(row.get("analysis_unit")).strip()

            analysis_quantity_val = row.get("analysis_quantity")
            analysis_quantity = None
            if pd.notna(analysis_quantity_val) and str(analysis_quantity_val).strip() != "":
                analysis_quantity = float(analysis_quantity_val)

            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            if not has_id and not sor_code and not package_code and not subpackage_code and subpackage_name in (None, ""):
                continue

            if not sor_code or not subpackage_code:
                raise ValueError("sor_code and subpackage_code are required for each work_item_subpackage row.")

            if has_id:
                cur.execute(
                    """
                    UPDATE work_item_subpackage
                    SET sor_code=%s, package_code=%s, subpackage_code=%s, subpackage_name=%s, description=%s, analysis_quantity=%s, analysis_unit=%s
                    WHERE id=%s
                    """,
                    (
                        sor_code,
                        package_code or None,
                        subpackage_code,
                        subpackage_name,
                        description,
                        analysis_quantity,
                        analysis_unit,
                        int(float(id_val)),
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO work_item_subpackage
                    (sor_code, package_code, subpackage_code, subpackage_name, description, analysis_quantity, analysis_unit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        package_code=VALUES(package_code),
                        subpackage_name=VALUES(subpackage_name),
                        description=VALUES(description),
                        analysis_quantity=VALUES(analysis_quantity),
                        analysis_unit=VALUES(analysis_unit)
                    """,
                    (
                        sor_code,
                        package_code or None,
                        subpackage_code,
                        subpackage_name,
                        description,
                        analysis_quantity,
                        analysis_unit,
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO work_item_rate (sor_code, subpackage_code, amount)
                    SELECT %s, %s, 0
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM work_item_rate
                        WHERE sor_code = %s
                          AND subpackage_code = %s
                    )
                    """,
                    (sor_code, subpackage_code, sor_code, subpackage_code),
                )

        conn.commit()
    finally:
        conn.close()


def save_lead_lift_item_master_data(df):
    conn = get_conn()
    try:
        cur = conn.cursor()

        for _, row in df.iterrows():
            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            ll_code = "" if pd.isna(row.get("ll_code")) else str(row.get("ll_code")).strip()
            item_name = None if pd.isna(row.get("item_name")) else str(row.get("item_name")).strip()
            profile_code = None if pd.isna(row.get("profile_code")) else str(row.get("profile_code")).strip()

            distance_val = row.get("distance_km")
            distance_km = None
            if pd.notna(distance_val) and str(distance_val).strip() != "":
                distance_km = float(distance_val)

            if not sor_code and not ll_code and item_name in (None, "") and profile_code in (None, "") and distance_km is None:
                continue

            if not sor_code or not ll_code:
                raise ValueError("sor_code and ll_code are required for lead_lift_item_master rows.")

            cur.execute(
                """
                INSERT INTO lead_lift_item_master (sor_code, ll_code, item_name, profile_code, distance_km)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    item_name=VALUES(item_name),
                    profile_code=VALUES(profile_code),
                    distance_km=VALUES(distance_km)
                """,
                (sor_code, ll_code, item_name, profile_code, distance_km),
            )

        conn.commit()
    finally:
        conn.close()


def save_work_item_analysis_data(df, table_columns):
    conn = get_conn()
    try:
        cur = conn.cursor()
        insertable_cols = [c for c in table_columns if c != "id"]

        for _, row in df.iterrows():
            id_val = row.get("id")
            has_id = pd.notna(id_val) and str(id_val).strip() != ""

            sor_code = "" if pd.isna(row.get("sor_code")) else str(row.get("sor_code")).strip()
            subpackage_code = "" if pd.isna(row.get("subpackage_code")) else str(row.get("subpackage_code")).strip()
            resource_type = "" if pd.isna(row.get("resource_type")) else str(row.get("resource_type")).strip()

            if not has_id and not sor_code and not subpackage_code and not resource_type:
                continue

            if not sor_code or not subpackage_code or not resource_type:
                raise ValueError("sor_code, subpackage_code and resource_type are required for work_item_analysis rows.")

            payload = {}
            for col in insertable_cols:
                if col not in df.columns:
                    continue
                val = row.get(col)
                if pd.isna(val):
                    payload[col] = None
                elif col == "quantity":
                    sval = str(val).strip()
                    payload[col] = float(sval) if sval != "" else None
                else:
                    sval = str(val).strip()
                    payload[col] = sval if sval != "" else None

            if has_id:
                update_cols = [c for c in payload.keys() if c != "id"]
                set_clause = ", ".join([f"{c}=%s" for c in update_cols])
                values = [payload[c] for c in update_cols] + [int(float(id_val))]
                cur.execute(f"UPDATE work_item_analysis SET {set_clause} WHERE id=%s", values)
            else:
                cols = list(payload.keys())
                placeholders = ", ".join(["%s"] * len(cols))
                cols_sql = ", ".join(cols)
                values = [payload[c] for c in cols]
                cur.execute(f"INSERT INTO work_item_analysis ({cols_sql}) VALUES ({placeholders})", values)

        conn.commit()
    finally:
        conn.close()


def delete_work_item_analysis_rows(row_ids):
    clean_ids = []
    for rid in row_ids:
        if rid is None or str(rid).strip() == "":
            continue
        clean_ids.append(int(float(rid)))

    if not clean_ids:
        return

    conn = get_conn()
    try:
        cur = conn.cursor()
        placeholders = ", ".join(["%s"] * len(clean_ids))
        cur.execute(f"DELETE FROM work_item_analysis WHERE id IN ({placeholders})", clean_ids)
        conn.commit()
    finally:
        conn.close()


def recalculate_work_item_rate_admin(sor_code):
    conn = get_conn()
    try:
        cur = conn.cursor()
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
                LEFT JOIN sor_material_data m
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
                GROUP BY a.sor_code, a.subpackage_code
            ) t
                ON t.sor_code = s.sor_code
               AND t.subpackage_code = s.subpackage_code
            CROSS JOIN (
                SELECT COALESCE(SUM(percentage), 0) / 100.0 AS pct
                FROM work_item_charges
            ) cf
            WHERE s.sor_code = %s
              AND s.analysis_quantity IS NOT NULL
              AND s.analysis_quantity > 0
            ON DUPLICATE KEY UPDATE amount = VALUES(amount)
            """,
            (sor_code, sor_code, sor_code),
        )
        conn.commit()
    finally:
        conn.close()


def request_clear_new_labour_inputs():
    st.session_state["clear_new_labour_inputs_pending"] = True


def apply_pending_new_labour_input_reset():
    if st.session_state.pop("clear_new_labour_inputs_pending", False):
        st.session_state["new_labour_sor_code"] = ""
        st.session_state["new_labour_category_choice"] = None
        st.session_state["new_labour_unique_code"] = ""
        st.session_state["new_labour_description"] = ""
        st.session_state["new_labour_unit"] = ""
        st.session_state["new_labour_base_rate"] = ""


def request_clear_new_material_inputs():
    st.session_state["clear_new_material_inputs_pending"] = True


def apply_pending_new_material_input_reset():
    if st.session_state.pop("clear_new_material_inputs_pending", False):
        st.session_state["new_material_sor_code"] = ""
        st.session_state["new_material_category_choice"] = None
        st.session_state["new_material_subcategory_choice"] = None
        st.session_state["new_material_unique_code"] = ""
        st.session_state["new_material_description"] = ""
        st.session_state["new_material_unit"] = ""
        st.session_state["new_material_unit_multiplier"] = "1"
        st.session_state["new_material_base_rate"] = ""


def request_clear_new_equipment_inputs():
    st.session_state["clear_new_equipment_inputs_pending"] = True


def apply_pending_new_equipment_input_reset():
    if st.session_state.pop("clear_new_equipment_inputs_pending", False):
        st.session_state["new_equipment_sor_code"] = ""
        st.session_state["new_equipment_unique_code"] = ""
        st.session_state["new_equipment_description"] = ""
        st.session_state["new_equipment_unit"] = ""
        st.session_state["new_equipment_base_rate"] = ""


def request_clear_new_work_item_package_inputs():
    st.session_state["clear_new_work_item_package_inputs_pending"] = True


def apply_pending_new_work_item_package_input_reset():
    if st.session_state.pop("clear_new_work_item_package_inputs_pending", False):
        st.session_state["new_wip_sor_code"] = ""
        st.session_state["new_wip_package_code"] = ""
        st.session_state["new_wip_package_name"] = ""


def request_clear_new_work_item_subpackage_inputs():
    st.session_state["clear_new_work_item_subpackage_inputs_pending"] = True


def apply_pending_new_work_item_subpackage_input_reset():
    if st.session_state.pop("clear_new_work_item_subpackage_inputs_pending", False):
        st.session_state["new_wisp_sor_code"] = ""
        st.session_state["new_wisp_package_code"] = ""
        st.session_state["new_wisp_subpackage_code"] = ""
        st.session_state["new_wisp_subpackage_name"] = ""
        st.session_state["new_wisp_description"] = ""
        st.session_state["new_wisp_analysis_qty"] = ""
        st.session_state["new_wisp_analysis_unit"] = ""


def clear_new_analysis_row_inputs(subpkg_code):
    keys = [
        f"wia_new_type_{subpkg_code}",
        f"wia_new_ref_{subpkg_code}",
        f"wia_new_qty_{subpkg_code}",
        f"wia_new_rem_{subpkg_code}",
        f"wia_new_item_{subpkg_code}",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("Admin Panel")

analysis_tab_codes = []
analysis_tab_defaults = {}
try:
    _wisp_for_tabs_df = load_work_item_subpackage_data()
    analysis_tab_codes = sorted(
        [
            str(code).strip()
            for code in _wisp_for_tabs_df["subpackage_code"].dropna().unique().tolist()
            if str(code).strip() != ""
        ]
    )
    for _, _row in _wisp_for_tabs_df.iterrows():
        _code = "" if pd.isna(_row.get("subpackage_code")) else str(_row.get("subpackage_code")).strip()
        _sor = "" if pd.isna(_row.get("sor_code")) else str(_row.get("sor_code")).strip()
        if _code and _code not in analysis_tab_defaults:
            analysis_tab_defaults[_code] = _sor
except Exception:
    analysis_tab_codes = []
    analysis_tab_defaults = {}

base_tab_labels = ["SOR Data", "Labour", "Material", "Equipment", "Work Items", "Lead Lift"]
all_tab_labels = base_tab_labels + analysis_tab_codes
active_section = st.selectbox("Section", all_tab_labels, key="active_section")

if active_section == "SOR Data":
    st.subheader("SOR Data")
    st.caption("Edit existing rows or add a new row, then click Save Changes.")

    try:
        df = load_sor_data()
    except Exception as e:
        st.error(f"Failed to load sor_data: {e}")
        st.stop()

    with st.form("sor_data_form", clear_on_submit=False):
        h1, h2, h3, h4 = st.columns([2, 2, 1, 2])
        with h1:
            st.markdown("**sor_code**")
        with h2:
            st.markdown("**state_name**")
        with h3:
            st.markdown("**year**")
        with h4:
            st.markdown("**name**")
        st.divider()

        edited_rows = []
        for _, row in df.iterrows():
            rid = int(row["id"])
            st.markdown(f"**Row ID: {rid}**")
            c1, c2, c3, c4 = st.columns([2, 2, 1, 2])
            with c1:
                sor_code = st.text_input(
                    "sor_code",
                    value="" if pd.isna(row["sor_code"]) else str(row["sor_code"]),
                    key=f"sor_code_{rid}",
                    label_visibility="collapsed",
                )
            with c2:
                state_name = st.text_input(
                    "state_name",
                    value="" if pd.isna(row["state_name"]) else str(row["state_name"]),
                    key=f"state_{rid}",
                    label_visibility="collapsed",
                )
            with c3:
                year_val = "" if pd.isna(row["year"]) else str(int(float(row["year"])))
                year = st.text_input(
                    "year",
                    value=year_val,
                    key=f"year_{rid}",
                    label_visibility="collapsed",
                )
            with c4:
                name = st.text_input(
                    "name",
                    value="" if pd.isna(row["name"]) else str(row["name"]),
                    key=f"name_{rid}",
                    label_visibility="collapsed",
                )

            edited_rows.append(
                {
                    "id": rid,
                    "sor_code": sor_code,
                    "state_name": state_name,
                    "year": year,
                    "name": name,
                }
            )
            st.divider()

        st.markdown("### Add New Row")
        n1, n2, n3, n4 = st.columns([2, 2, 1, 2])
        with n1:
            new_sor_code = st.text_input("new_sor_code", key="new_sor_code", placeholder="TN_SOR_2026", label_visibility="collapsed")
        with n2:
            new_state = st.text_input("new_state", key="new_state", placeholder="State Name", label_visibility="collapsed")
        with n3:
            new_year = st.text_input("new_year", key="new_year", placeholder="2026", label_visibility="collapsed")
        with n4:
            new_name = st.text_input("new_name", key="new_name", placeholder="SOR Name", label_visibility="collapsed")

        save_clicked = st.form_submit_button("Save Changes", type="primary")

    if save_clicked:
        rows_to_save = edited_rows[:]
        if new_sor_code.strip():
            rows_to_save.append(
                {
                    "id": None,
                    "sor_code": new_sor_code.strip(),
                    "state_name": new_state.strip() or None,
                    "year": new_year.strip() or None,
                    "name": new_name.strip() or None,
                }
            )
        try:
            save_sor_data(pd.DataFrame(rows_to_save))
            st.success("sor_data updated successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save sor_data: {e}")

    if st.button("Reload"):
        st.rerun()

if active_section == "Labour":
    st.subheader("Labour Data")
    st.caption("Edit rows in `sor_labour_data` and click Save Labour Changes at the bottom.")
    apply_pending_new_labour_input_reset()

    try:
        labour_df = load_labour_data()
    except Exception as e:
        st.error(f"Failed to load sor_labour_data: {e}")
        st.stop()
    try:
        labour_categories_df = load_labour_categories()
    except Exception as e:
        st.error(f"Failed to load sor_labour_category: {e}")
        st.stop()

    with st.form("labour_data_form", clear_on_submit=False):
        h1, h2, h3, h4, h5, h6, h7 = st.columns([0.8, 1.6, 1.1, 1.6, 4.0, 1.0, 0.9])
        with h1:
            st.markdown("**id**")
        with h2:
            st.markdown("**sor_code**")
        with h3:
            st.markdown("**category**")
        with h4:
            st.markdown("**unique_code**")
        with h5:
            st.markdown("**description**")
        with h6:
            st.markdown("**unit**")
        with h7:
            st.markdown("**base_rate**")
        st.divider()

        edited_labour_rows = []
        for _, row in labour_df.iterrows():
            rid = int(row["id"])
            c1, c2, c3, c4, c5, c6, c7 = st.columns([0.7, 1.6, 1.1, 1.6, 4.0, 1.0, 1.0])
            orig_sor_code = "" if pd.isna(row["sor_code"]) else str(row["sor_code"]).strip()
            orig_category_code = "" if pd.isna(row["category_code"]) else str(row["category_code"]).strip()
            orig_unique_code = "" if pd.isna(row["unique_code"]) else str(row["unique_code"]).strip()
            orig_description = "" if pd.isna(row["description"]) else str(row["description"]).strip()
            orig_unit = "" if pd.isna(row["unit"]) else str(row["unit"]).strip()
            orig_base_rate = "" if pd.isna(row["base_rate"]) else str(float(row["base_rate"]))

            with c1:
                st.text_input("id", value=str(rid), key=f"labour_id_{rid}", disabled=True, label_visibility="collapsed")
            with c2:
                sor_code = st.text_input(
                    "sor_code",
                    value=orig_sor_code,
                    key=f"labour_sor_{rid}",
                    label_visibility="collapsed",
                )
            with c3:
                category_code = st.text_input(
                    "category_code",
                    value=orig_category_code,
                    key=f"labour_cat_{rid}",
                    label_visibility="collapsed",
                )
            with c4:
                unique_code = st.text_input(
                    "unique_code",
                    value=orig_unique_code,
                    key=f"labour_ucode_{rid}",
                    label_visibility="collapsed",
                )
            with c5:
                description = st.text_input(
                    "description",
                    value=orig_description,
                    key=f"labour_desc_{rid}",
                    label_visibility="collapsed",
                )
            with c6:
                unit = st.text_input(
                    "unit",
                    value=orig_unit,
                    key=f"labour_unit_{rid}",
                    label_visibility="collapsed",
                )
            with c7:
                base_rate = st.text_input(
                    "base_rate",
                    value=orig_base_rate,
                    key=f"labour_rate_{rid}",
                    label_visibility="collapsed",
                )

            row_payload = {
                "id": rid,
                "sor_code": sor_code.strip(),
                "category_code": category_code.strip(),
                "unique_code": unique_code.strip(),
                "description": description.strip() or None,
                "unit": unit.strip() or None,
                "base_rate": base_rate.strip() or None,
            }
            edited_labour_rows.append(row_payload)
            st.divider()

        st.markdown("### Add New Labour Row")
        n1, n2, n3, n4, n5, n6 = st.columns([1.6, 1.1, 1.6, 4.0, 1.0, 0.9])
        with n1:
            new_sor_code = st.text_input("new_labour_sor_code", key="new_labour_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
        with n2:
            category_options = [
                (
                    "" if pd.isna(cat_row["category_code"]) else str(cat_row["category_code"]).strip(),
                    "" if pd.isna(cat_row["category_name"]) else str(cat_row["category_name"]).strip(),
                )
                for _, cat_row in labour_categories_df.iterrows()
            ]
            selected_option = st.session_state.get("new_labour_category_choice")

            def _format_category_option(opt):
                code, name = opt
                if selected_option == opt:
                    return code
                return f"{code} - {name}" if name else code

            selected_category = st.selectbox(
                "new_labour_category_code",
                options=category_options,
                index=None if category_options else 0,
                placeholder="Select category code",
                format_func=_format_category_option,
                key="new_labour_category_choice",
                label_visibility="collapsed",
            )
            new_category_code = selected_category[0] if selected_category else ""
        with n3:
            new_unique_code = st.text_input("new_labour_unique_code", key="new_labour_unique_code", placeholder="L-9999", label_visibility="collapsed")
        with n4:
            new_description = st.text_input("new_labour_description", key="new_labour_description", placeholder="Description", label_visibility="collapsed")
        with n5:
            new_unit = st.text_input("new_labour_unit", key="new_labour_unit", placeholder="Day", label_visibility="collapsed")
        with n6:
            new_base_rate = st.text_input("new_labour_base_rate", key="new_labour_base_rate", placeholder="0.00", label_visibility="collapsed")

        save_labour_clicked = st.form_submit_button("Save Labour Changes", type="primary")

    if save_labour_clicked:
        rows_to_save = edited_labour_rows[:]
        if new_unique_code.strip():
            rows_to_save.append(
                {
                    "id": None,
                    "sor_code": new_sor_code.strip() or None,
                    "category_code": new_category_code.strip() or None,
                    "unique_code": new_unique_code.strip(),
                    "description": new_description.strip() or None,
                    "unit": new_unit.strip() or None,
                    "base_rate": new_base_rate.strip() or None,
                }
            )

        try:
            save_labour_data(pd.DataFrame(rows_to_save))
            st.success("sor_labour_data updated successfully.")
            request_clear_new_labour_inputs()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save sor_labour_data: {e}")

    if st.button("Reload Labour"):
        st.rerun()

if active_section == "Material":
    st.subheader("Material Data")
    st.caption("Existing rows are edited in-form; add-new row is outside with category-dependent subcategory dropdown.")
    apply_pending_new_material_input_reset()

    try:
        material_df = load_material_data()
    except Exception as e:
        st.error(f"Failed to load sor_material_data: {e}")
        st.stop()
    try:
        material_categories_df = load_material_categories()
    except Exception as e:
        st.error(f"Failed to load material category/subcategory tables: {e}")
        st.stop()

    st.markdown("### Add New Material Row")
    n1, n2, n3, n4, n5, n6, n7, n8 = st.columns([1.4, 1.3, 2.8, 1.4, 3.0, 1.0, 0.9, 0.9])
    with n1:
        new_sor_code = st.text_input("new_material_sor_code", key="new_material_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
    with n2:
        category_options = [
            (
                "" if pd.isna(cat_row["sor_code"]) else str(cat_row["sor_code"]).strip(),
                "" if pd.isna(cat_row["category_code"]) else str(cat_row["category_code"]).strip(),
                "" if pd.isna(cat_row["category_name"]) else str(cat_row["category_name"]).strip(),
            )
            for _, cat_row in material_categories_df.iterrows()
        ]
        selected_material_category = st.selectbox(
            "new_material_category_code",
            options=category_options,
            index=None if category_options else 0,
            placeholder="Select category",
            format_func=lambda opt: f"{opt[1]} - {opt[2]}" if opt[2] else opt[1],
            key="new_material_category_choice",
            label_visibility="collapsed",
        )
        new_material_category_code = selected_material_category[1] if selected_material_category else ""

    with n3:
        if new_material_category_code:
            try:
                matched_subcat_df = load_material_subcategories_by_category(new_material_category_code)
            except Exception as e:
                st.error(f"Failed to load subcategories: {e}")
                matched_subcat_df = pd.DataFrame({"subcategory_name": []})
        else:
            matched_subcat_df = pd.DataFrame({"subcategory_name": []})

        subcategory_options = [None] + [
            "" if pd.isna(sc["subcategory_name"]) else str(sc["subcategory_name"]).strip()
            for _, sc in matched_subcat_df.iterrows()
        ]
        selected_subcategory = st.selectbox(
            "new_material_subcategory_name",
            options=subcategory_options,
            index=0 if subcategory_options else None,
            placeholder="Select subcategory",
            format_func=lambda s: "None" if s in (None, "") else s,
            key="new_material_subcategory_choice",
            label_visibility="collapsed",
        )
        new_material_subcategory_name = selected_subcategory if selected_subcategory else None
    with n4:
        new_material_unique_code = st.text_input("new_material_unique_code", key="new_material_unique_code", placeholder="M-9999", label_visibility="collapsed")
    with n5:
        new_material_description = st.text_input("new_material_description", key="new_material_description", placeholder="Description", label_visibility="collapsed")
    with n6:
        new_material_unit = st.text_input("new_material_unit", key="new_material_unit", placeholder="Nos", label_visibility="collapsed")
    with n7:
        new_material_unit_multiplier = st.text_input("new_material_unit_multiplier", key="new_material_unit_multiplier", placeholder="1", label_visibility="collapsed")
    with n8:
        new_material_base_rate = st.text_input("new_material_base_rate", key="new_material_base_rate", placeholder="0.00", label_visibility="collapsed")

    if st.button("Add Material Row", type="primary"):
        if not new_material_unique_code.strip():
            st.error("unique_code is required to add a new material row.")
        else:
            new_row_df = pd.DataFrame(
                [
                    {
                        "id": None,
                        "sor_code": new_sor_code.strip() or None,
                        "category_code": new_material_category_code.strip() or None,
                        "subcategory_name": new_material_subcategory_name,
                        "unique_code": new_material_unique_code.strip(),
                        "description": new_material_description.strip() or None,
                        "unit": new_material_unit.strip() or None,
                        "unit_multiplier": new_material_unit_multiplier.strip() or None,
                        "base_rate": new_material_base_rate.strip() or None,
                    }
                ]
            )
            try:
                save_material_data(new_row_df)
                load_material_data.clear()
                load_material_categories.clear()
                load_material_subcategories_by_category.clear()
                st.success("New material row added successfully.")
                request_clear_new_material_inputs()
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add material row: {e}")

    st.divider()
    st.markdown("### Edit Existing Material Rows")
    with st.form("material_edit_form", clear_on_submit=False):
        h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([0.7, 1.4, 1.0, 2.8, 1.4, 3.0, 1.0, 0.9, 0.9])
        with h1:
            st.markdown("**id**")
        with h2:
            st.markdown("**sor_code**")
        with h3:
            st.markdown("**category**")
        with h4:
            st.markdown("**subcategory**")
        with h5:
            st.markdown("**unique_code**")
        with h6:
            st.markdown("**description**")
        with h7:
            st.markdown("**unit**")
        with h8:
            st.markdown("**mult**")
        with h9:
            st.markdown("**base_rate**")
        st.divider()

        edited_material_rows = []
        for _, row in material_df.iterrows():
            rid = int(row["id"])
            c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([0.7, 1.4, 1.0, 2.8, 1.4, 3.0, 1.0, 0.9, 0.9])
            orig_sor_code = "" if pd.isna(row["sor_code"]) else str(row["sor_code"]).strip()
            orig_category_code = "" if pd.isna(row["category_code"]) else str(row["category_code"]).strip()
            orig_subcategory = "" if pd.isna(row["subcategory_name"]) else str(row["subcategory_name"]).strip()
            orig_unique_code = "" if pd.isna(row["unique_code"]) else str(row["unique_code"]).strip()
            orig_description = "" if pd.isna(row["description"]) else str(row["description"]).strip()
            orig_unit = "" if pd.isna(row["unit"]) else str(row["unit"]).strip()
            orig_multiplier = "" if pd.isna(row["unit_multiplier"]) else str(int(float(row["unit_multiplier"])))
            orig_base_rate = "" if pd.isna(row["base_rate"]) else str(float(row["base_rate"]))

            with c1:
                st.text_input("id", value=str(rid), key=f"mat_id_{rid}", disabled=True, label_visibility="collapsed")
            with c2:
                sor_code = st.text_input("sor_code", value=orig_sor_code, key=f"mat_sor_{rid}", label_visibility="collapsed")
            with c3:
                category_code = st.text_input("category_code", value=orig_category_code, key=f"mat_cat_{rid}", label_visibility="collapsed")
            with c4:
                subcategory_name = st.text_input("subcategory_name", value=orig_subcategory, key=f"mat_subcat_{rid}", label_visibility="collapsed")
            with c5:
                unique_code = st.text_input("unique_code", value=orig_unique_code, key=f"mat_ucode_{rid}", label_visibility="collapsed")
            with c6:
                description = st.text_input("description", value=orig_description, key=f"mat_desc_{rid}", label_visibility="collapsed")
            with c7:
                unit = st.text_input("unit", value=orig_unit, key=f"mat_unit_{rid}", label_visibility="collapsed")
            with c8:
                unit_multiplier = st.text_input("unit_multiplier", value=orig_multiplier, key=f"mat_mult_{rid}", label_visibility="collapsed")
            with c9:
                base_rate = st.text_input("base_rate", value=orig_base_rate, key=f"mat_rate_{rid}", label_visibility="collapsed")

            edited_material_rows.append(
                {
                    "id": rid,
                    "sor_code": sor_code.strip(),
                    "category_code": category_code.strip(),
                    "subcategory_name": subcategory_name.strip() or None,
                    "unique_code": unique_code.strip(),
                    "description": description.strip() or None,
                    "unit": unit.strip() or None,
                    "unit_multiplier": unit_multiplier.strip() or None,
                    "base_rate": base_rate.strip() or None,
                }
            )
            st.divider()

        save_material_clicked = st.form_submit_button("Save Material Changes", type="primary")

    if save_material_clicked:
        try:
            save_material_data(pd.DataFrame(edited_material_rows))
            load_material_data.clear()
            load_material_categories.clear()
            load_material_subcategories_by_category.clear()
            st.success("sor_material_data updated successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save sor_material_data: {e}")

    if st.button("Reload Material"):
        st.rerun()

if active_section == "Equipment":
    st.subheader("Equipment Data")
    st.caption("Edit rows in `sor_equipment_data` and click Save Equipment Changes.")
    apply_pending_new_equipment_input_reset()

    try:
        equipment_df = load_equipment_data()
    except Exception as e:
        st.error(f"Failed to load sor_equipment_data: {e}")
        st.stop()

    with st.form("equipment_data_form", clear_on_submit=False):
        h1, h2, h3, h4, h5, h6 = st.columns([0.7, 1.6, 1.6, 4.0, 1.0, 1.0])
        with h1:
            st.markdown("**id**")
        with h2:
            st.markdown("**sor_code**")
        with h3:
            st.markdown("**unique_code**")
        with h4:
            st.markdown("**description**")
        with h5:
            st.markdown("**unit**")
        with h6:
            st.markdown("**base_rate**")
        st.divider()

        edited_equipment_rows = []
        for _, row in equipment_df.iterrows():
            rid = int(row["id"])
            c1, c2, c3, c4, c5, c6 = st.columns([0.7, 1.6, 1.6, 4.0, 1.0, 1.0])
            with c1:
                st.text_input("id", value=str(rid), key=f"eq_id_{rid}", disabled=True, label_visibility="collapsed")
            with c2:
                sor_code = st.text_input(
                    "sor_code",
                    value="" if pd.isna(row["sor_code"]) else str(row["sor_code"]),
                    key=f"eq_sor_{rid}",
                    label_visibility="collapsed",
                )
            with c3:
                unique_code = st.text_input(
                    "unique_code",
                    value="" if pd.isna(row["unique_code"]) else str(row["unique_code"]),
                    key=f"eq_ucode_{rid}",
                    label_visibility="collapsed",
                )
            with c4:
                description = st.text_input(
                    "description",
                    value="" if pd.isna(row["description"]) else str(row["description"]),
                    key=f"eq_desc_{rid}",
                    label_visibility="collapsed",
                )
            with c5:
                unit = st.text_input(
                    "unit",
                    value="" if pd.isna(row["unit"]) else str(row["unit"]),
                    key=f"eq_unit_{rid}",
                    label_visibility="collapsed",
                )
            with c6:
                base_rate = st.text_input(
                    "base_rate",
                    value="" if pd.isna(row["base_rate"]) else str(float(row["base_rate"])),
                    key=f"eq_rate_{rid}",
                    label_visibility="collapsed",
                )

            edited_equipment_rows.append(
                {
                    "id": rid,
                    "sor_code": sor_code.strip(),
                    "unique_code": unique_code.strip(),
                    "description": description.strip() or None,
                    "unit": unit.strip() or None,
                    "base_rate": base_rate.strip() or None,
                }
            )
            st.divider()

        st.markdown("### Add New Equipment Row")
        n1, n2, n3, n4, n5 = st.columns([1.6, 1.6, 4.0, 1.0, 1.0])
        with n1:
            new_sor_code = st.text_input("new_equipment_sor_code", key="new_equipment_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
        with n2:
            new_unique_code = st.text_input("new_equipment_unique_code", key="new_equipment_unique_code", placeholder="H-9999", label_visibility="collapsed")
        with n3:
            new_description = st.text_input("new_equipment_description", key="new_equipment_description", placeholder="Description", label_visibility="collapsed")
        with n4:
            new_unit = st.text_input("new_equipment_unit", key="new_equipment_unit", placeholder="Day", label_visibility="collapsed")
        with n5:
            new_base_rate = st.text_input("new_equipment_base_rate", key="new_equipment_base_rate", placeholder="0.00", label_visibility="collapsed")

        save_equipment_clicked = st.form_submit_button("Save Equipment Changes", type="primary")

    if save_equipment_clicked:
        rows_to_save = edited_equipment_rows[:]
        if new_unique_code.strip():
            rows_to_save.append(
                {
                    "id": None,
                    "sor_code": new_sor_code.strip() or None,
                    "unique_code": new_unique_code.strip(),
                    "description": new_description.strip() or None,
                    "unit": new_unit.strip() or None,
                    "base_rate": new_base_rate.strip() or None,
                }
            )

        try:
            save_equipment_data(pd.DataFrame(rows_to_save))
            st.success("sor_equipment_data updated successfully.")
            request_clear_new_equipment_inputs()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save sor_equipment_data: {e}")

    if st.button("Reload Equipment"):
        st.rerun()

if active_section == "Work Items":
    st.subheader("Work Item Package Data")
    st.caption("Edit rows in `work_item_package` and click Save Work Item Package Changes.")
    apply_pending_new_work_item_package_input_reset()

    try:
        work_item_package_df = load_work_item_package_data()
    except Exception as e:
        st.error(f"Failed to load work_item_package: {e}")
        st.stop()

    st.markdown("### Recalculate Work Item Rate")
    sor_options = sorted(
        [
            str(x).strip()
            for x in work_item_package_df["sor_code"].dropna().unique().tolist()
            if str(x).strip() != ""
        ]
    )
    if sor_options:
        recalc_sor_code = st.selectbox(
            "Select sor_code for rate recalculation",
            options=sor_options,
            key="recalc_work_item_rate_sor_code",
        )
        if st.button("Recalculate work_item_rate", type="primary"):
            try:
                recalculate_work_item_rate_admin(recalc_sor_code)
                st.success(f"work_item_rate recalculated for {recalc_sor_code}.")
            except Exception as e:
                st.error(f"Failed to recalculate work_item_rate for {recalc_sor_code}: {e}")
    else:
        st.info("No sor_code found in work_item_package to recalculate.")

    st.divider()

    with st.form("work_item_package_form", clear_on_submit=False):
        h1, h2, h3, h4 = st.columns([0.8, 1.6, 1.2, 3.5])
        with h1:
            st.markdown("**id**")
        with h2:
            st.markdown("**sor_code**")
        with h3:
            st.markdown("**package_code**")
        with h4:
            st.markdown("**package_name**")
        st.divider()

        edited_wip_rows = []
        for _, row in work_item_package_df.iterrows():
            rid = int(row["id"])
            c1, c2, c3, c4 = st.columns([0.8, 1.6, 1.2, 3.5])
            with c1:
                st.text_input("id", value=str(rid), key=f"wip_id_{rid}", disabled=True, label_visibility="collapsed")
            with c2:
                sor_code = st.text_input(
                    "sor_code",
                    value="" if pd.isna(row["sor_code"]) else str(row["sor_code"]),
                    key=f"wip_sor_{rid}",
                    label_visibility="collapsed",
                )
            with c3:
                package_code = st.text_input(
                    "package_code",
                    value="" if pd.isna(row["package_code"]) else str(row["package_code"]),
                    key=f"wip_code_{rid}",
                    label_visibility="collapsed",
                )
            with c4:
                package_name = st.text_input(
                    "package_name",
                    value="" if pd.isna(row["package_name"]) else str(row["package_name"]),
                    key=f"wip_name_{rid}",
                    label_visibility="collapsed",
                )

            edited_wip_rows.append(
                {
                    "id": rid,
                    "sor_code": sor_code.strip(),
                    "package_code": package_code.strip(),
                    "package_name": package_name.strip() or None,
                }
            )
            st.divider()

        st.markdown("### Add New Work Item Package Row")
        n1, n2, n3 = st.columns([1.6, 1.2, 3.5])
        with n1:
            new_sor_code = st.text_input("new_wip_sor_code", key="new_wip_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
        with n2:
            new_package_code = st.text_input("new_wip_package_code", key="new_wip_package_code", placeholder="A", label_visibility="collapsed")
        with n3:
            new_package_name = st.text_input("new_wip_package_name", key="new_wip_package_name", placeholder="Package Name", label_visibility="collapsed")

        save_wip_clicked = st.form_submit_button("Save Work Item Package Changes", type="primary")

    if save_wip_clicked:
        rows_to_save = edited_wip_rows[:]
        if new_sor_code.strip() and new_package_code.strip():
            rows_to_save.append(
                {
                    "id": None,
                    "sor_code": new_sor_code.strip(),
                    "package_code": new_package_code.strip(),
                    "package_name": new_package_name.strip() or None,
                }
            )

        try:
            save_work_item_package_data(pd.DataFrame(rows_to_save))
            st.success("work_item_package updated successfully.")
            request_clear_new_work_item_package_inputs()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save work_item_package: {e}")

    if st.button("Reload Work Item Package"):
        st.rerun()

    st.divider()
    st.subheader("Work Item Subpackage Data")
    st.caption("Edit rows in `work_item_subpackage` and click Save Work Item Subpackage Changes.")
    apply_pending_new_work_item_subpackage_input_reset()

    try:
        work_item_subpackage_df = load_work_item_subpackage_data()
    except Exception as e:
        st.error(f"Failed to load work_item_subpackage: {e}")
        st.stop()

    with st.form("work_item_subpackage_form", clear_on_submit=False):
        h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([0.7, 1.4, 1.1, 1.2, 2.0, 2.2, 1.1, 1.0])
        with h1:
            st.markdown("**id**")
        with h2:
            st.markdown("**sor_code**")
        with h3:
            st.markdown("**package_code**")
        with h4:
            st.markdown("**subpackage_code**")
        with h5:
            st.markdown("**subpackage_name**")
        with h6:
            st.markdown("**description**")
        with h7:
            st.markdown("**analysis_qty**")
        with h8:
            st.markdown("**analysis_unit**")
        st.divider()

        edited_wisp_rows = []
        for _, row in work_item_subpackage_df.iterrows():
            rid = int(row["id"])
            c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.7, 1.4, 1.1, 1.2, 2.0, 2.2, 1.1, 1.0])
            with c1:
                st.text_input("id", value=str(rid), key=f"wisp_id_{rid}", disabled=True, label_visibility="collapsed")
            with c2:
                sor_code = st.text_input(
                    "sor_code",
                    value="" if pd.isna(row["sor_code"]) else str(row["sor_code"]),
                    key=f"wisp_sor_{rid}",
                    label_visibility="collapsed",
                )
            with c3:
                package_code = st.text_input(
                    "package_code",
                    value="" if pd.isna(row["package_code"]) else str(row["package_code"]),
                    key=f"wisp_pkg_{rid}",
                    label_visibility="collapsed",
                )
            with c4:
                subpackage_code = st.text_input(
                    "subpackage_code",
                    value="" if pd.isna(row["subpackage_code"]) else str(row["subpackage_code"]),
                    key=f"wisp_code_{rid}",
                    label_visibility="collapsed",
                )
            with c5:
                subpackage_name = st.text_input(
                    "subpackage_name",
                    value="" if pd.isna(row["subpackage_name"]) else str(row["subpackage_name"]),
                    key=f"wisp_name_{rid}",
                    label_visibility="collapsed",
                )
            with c6:
                description = st.text_input(
                    "description",
                    value="" if pd.isna(row["description"]) else str(row["description"]),
                    key=f"wisp_desc_{rid}",
                    label_visibility="collapsed",
                )
            with c7:
                analysis_quantity = st.text_input(
                    "analysis_quantity",
                    value="" if pd.isna(row["analysis_quantity"]) else str(float(row["analysis_quantity"])),
                    key=f"wisp_qty_{rid}",
                    label_visibility="collapsed",
                )
            with c8:
                analysis_unit = st.text_input(
                    "analysis_unit",
                    value="" if pd.isna(row["analysis_unit"]) else str(row["analysis_unit"]),
                    key=f"wisp_unit_{rid}",
                    label_visibility="collapsed",
                )

            edited_wisp_rows.append(
                {
                    "id": rid,
                    "sor_code": sor_code.strip(),
                    "package_code": package_code.strip(),
                    "subpackage_code": subpackage_code.strip(),
                    "subpackage_name": subpackage_name.strip() or None,
                    "description": description.strip() or None,
                    "analysis_quantity": analysis_quantity.strip() or None,
                    "analysis_unit": analysis_unit.strip() or None,
                }
            )
            st.divider()

        st.markdown("### Add New Work Item Subpackage Row")
        n1, n2, n3, n4, n5, n6, n7 = st.columns([1.4, 1.1, 1.2, 2.0, 2.2, 1.1, 1.0])
        with n1:
            new_sor_code = st.text_input("new_wisp_sor_code", key="new_wisp_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
        with n2:
            new_package_code = st.text_input("new_wisp_package_code", key="new_wisp_package_code", placeholder="A", label_visibility="collapsed")
        with n3:
            new_subpackage_code = st.text_input("new_wisp_subpackage_code", key="new_wisp_subpackage_code", placeholder="A1", label_visibility="collapsed")
        with n4:
            new_subpackage_name = st.text_input("new_wisp_subpackage_name", key="new_wisp_subpackage_name", placeholder="Subpackage Name", label_visibility="collapsed")
        with n5:
            new_description = st.text_input("new_wisp_description", key="new_wisp_description", placeholder="Description", label_visibility="collapsed")
        with n6:
            new_analysis_qty = st.text_input("new_wisp_analysis_qty", key="new_wisp_analysis_qty", placeholder="0.00", label_visibility="collapsed")
        with n7:
            new_analysis_unit = st.text_input("new_wisp_analysis_unit", key="new_wisp_analysis_unit", placeholder="Cu.M", label_visibility="collapsed")

        save_wisp_clicked = st.form_submit_button("Save Work Item Subpackage Changes", type="primary")

    if save_wisp_clicked:
        rows_to_save = edited_wisp_rows[:]
        if new_sor_code.strip() and new_subpackage_code.strip():
            rows_to_save.append(
                {
                    "id": None,
                    "sor_code": new_sor_code.strip(),
                    "package_code": new_package_code.strip() or None,
                    "subpackage_code": new_subpackage_code.strip(),
                    "subpackage_name": new_subpackage_name.strip() or None,
                    "description": new_description.strip() or None,
                    "analysis_quantity": new_analysis_qty.strip() or None,
                    "analysis_unit": new_analysis_unit.strip() or None,
                }
            )

        try:
            save_work_item_subpackage_data(pd.DataFrame(rows_to_save))
            st.success("work_item_subpackage updated successfully.")
            request_clear_new_work_item_subpackage_inputs()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save work_item_subpackage: {e}")

    if st.button("Reload Work Item Subpackage"):
        st.rerun()

if active_section == "Lead Lift":
    st.subheader("Lead Lift Item Master")
    st.caption("Edit rows in `lead_lift_item_master` and save changes.")

    try:
        ll_df = load_lead_lift_item_master_data()
    except Exception as e:
        st.error(f"Failed to load lead_lift_item_master: {e}")
        st.stop()

    with st.form("lead_lift_item_master_form", clear_on_submit=False):
        h1, h2, h3, h4, h5 = st.columns([1.6, 1.2, 3.2, 1.2, 1.2])
        with h1:
            st.markdown("**sor_code**")
        with h2:
            st.markdown("**ll_code**")
        with h3:
            st.markdown("**item_name**")
        with h4:
            st.markdown("**profile_code**")
        with h5:
            st.markdown("**distance_km**")
        st.divider()

        edited_ll_rows = []
        for _, row in ll_df.iterrows():
            row_sor = "" if pd.isna(row["sor_code"]) else str(row["sor_code"]).strip()
            row_ll = "" if pd.isna(row["ll_code"]) else str(row["ll_code"]).strip()
            c1, c2, c3, c4, c5 = st.columns([1.6, 1.2, 3.2, 1.2, 1.2])
            with c1:
                sor_code = st.text_input(
                    "sor_code",
                    value=row_sor,
                    key=f"ll_sor_{row_sor}_{row_ll}",
                    label_visibility="collapsed",
                )
            with c2:
                ll_code = st.text_input(
                    "ll_code",
                    value=row_ll,
                    key=f"ll_code_{row_sor}_{row_ll}",
                    label_visibility="collapsed",
                )
            with c3:
                item_name = st.text_input(
                    "item_name",
                    value="" if pd.isna(row["item_name"]) else str(row["item_name"]),
                    key=f"ll_item_{row_sor}_{row_ll}",
                    label_visibility="collapsed",
                )
            with c4:
                profile_code = st.text_input(
                    "profile_code",
                    value="" if pd.isna(row["profile_code"]) else str(row["profile_code"]),
                    key=f"ll_profile_{row_sor}_{row_ll}",
                    label_visibility="collapsed",
                )
            with c5:
                distance_km = st.text_input(
                    "distance_km",
                    value="" if pd.isna(row["distance_km"]) else str(float(row["distance_km"])),
                    key=f"ll_dist_{row_sor}_{row_ll}",
                    label_visibility="collapsed",
                )

            edited_ll_rows.append(
                {
                    "sor_code": sor_code.strip(),
                    "ll_code": ll_code.strip(),
                    "item_name": item_name.strip() or None,
                    "profile_code": profile_code.strip() or None,
                    "distance_km": distance_km.strip() or None,
                }
            )
            st.divider()

        st.markdown("### Add New Lead Lift Item")
        n1, n2, n3, n4, n5 = st.columns([1.6, 1.2, 3.2, 1.2, 1.2])
        with n1:
            new_sor_code = st.text_input("new_ll_sor_code", key="new_ll_sor_code", placeholder="TN_SOR_2025", label_visibility="collapsed")
        with n2:
            new_ll_code = st.text_input("new_ll_code", key="new_ll_code", placeholder="LL6", label_visibility="collapsed")
        with n3:
            new_item_name = st.text_input("new_ll_item_name", key="new_ll_item_name", placeholder="Item Name", label_visibility="collapsed")
        with n4:
            new_profile_code = st.text_input("new_ll_profile_code", key="new_ll_profile_code", placeholder="TP1", label_visibility="collapsed")
        with n5:
            new_distance_km = st.text_input("new_ll_distance_km", key="new_ll_distance_km", placeholder="0.00", label_visibility="collapsed")

        save_ll_clicked = st.form_submit_button("Save Lead Lift Changes", type="primary")

    if save_ll_clicked:
        rows_to_save = edited_ll_rows[:]
        if new_sor_code.strip() and new_ll_code.strip():
            rows_to_save.append(
                {
                    "sor_code": new_sor_code.strip(),
                    "ll_code": new_ll_code.strip(),
                    "item_name": new_item_name.strip() or None,
                    "profile_code": new_profile_code.strip() or None,
                    "distance_km": new_distance_km.strip() or None,
                }
            )
        try:
            save_lead_lift_item_master_data(pd.DataFrame(rows_to_save))
            st.success("lead_lift_item_master updated successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to save lead_lift_item_master: {e}")

    if st.button("Reload Lead Lift"):
        st.rerun()

try:
    _work_item_analysis_df = load_work_item_analysis_data()
    _work_item_analysis_columns = get_work_item_analysis_columns()
except Exception as _e:
    _work_item_analysis_df = pd.DataFrame()
    _work_item_analysis_columns = []
    st.warning(f"Could not load work_item_analysis tabs: {_e}")

for _subpkg_code in analysis_tab_codes:
    if active_section == _subpkg_code:
        st.subheader(f"Work Item Analysis - {_subpkg_code}")
        st.caption(f"Rows from `work_item_analysis` for subpackage `{_subpkg_code}`.")
        _enable_editor = st.toggle(
            "Enable editor for this subpackage",
            key=f"wia_enable_{_subpkg_code}",
            value=False,
            help="Keeps page fast by rendering add/edit controls only for the subpackage you are working on.",
        )
        if not _enable_editor:
            st.info("Editor is paused for this subpackage. Turn on the toggle above to edit or add rows.")
            continue

        _sub_df = _work_item_analysis_df[
            _work_item_analysis_df["subpackage_code"].astype(str).str.strip() == _subpkg_code
        ] if not _work_item_analysis_df.empty else pd.DataFrame()

        _has_lead_lift = "lead_lift_code" in _work_item_analysis_columns
        _header_cols = [0.7, 1.3, 1.2, 1.7, 1.4, 1.2, 1.2, 1.1, 0.9, 1.5, 0.9]
        if _has_lead_lift:
            _header_cols = [0.7, 1.3, 1.2, 1.7, 1.2, 1.1, 1.1, 1.1, 0.9, 1.4, 0.9]

        with st.form(f"wia_form_{_subpkg_code}", clear_on_submit=False):
            _h = st.columns(_header_cols)
            _h[0].markdown("**id**")
            _h[1].markdown("**sor_code**")
            _h[2].markdown("**resource_type**")
            _h[3].markdown("**item**")
            _h[4].markdown("**material_code**")
            _h[5].markdown("**labour_code**")
            _h[6].markdown("**equipment_code**")
            _idx_after_equipment = 7
            if _has_lead_lift:
                _h[7].markdown("**lead_lift_code**")
                _idx_after_equipment = 8
            _h[_idx_after_equipment].markdown("**qty**")
            _h[_idx_after_equipment + 1].markdown("**remark**")
            _h[_idx_after_equipment + 2].markdown("**delete**")
            st.divider()

            _edited_rows = []
            _ids_to_delete = []
            for _, _row in _sub_df.iterrows():
                _rid = int(_row["id"])
                _c = st.columns(_header_cols)
                _c[0].text_input("id", value=str(_rid), key=f"wia_id_{_subpkg_code}_{_rid}", disabled=True, label_visibility="collapsed")
                _sor_code = _c[1].text_input(
                    "sor_code",
                    value="" if pd.isna(_row.get("sor_code")) else str(_row.get("sor_code")),
                    key=f"wia_sor_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _resource_type = _c[2].selectbox(
                    "resource_type",
                    options=["MATERIAL", "LABOUR", "EQUIPMENT", "LEAD & LIFT"],
                    index=["MATERIAL", "LABOUR", "EQUIPMENT", "LEAD & LIFT"].index(str(_row.get("resource_type"))) if str(_row.get("resource_type")) in ["MATERIAL", "LABOUR", "EQUIPMENT", "LEAD & LIFT"] else 0,
                    key=f"wia_type_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _item = _c[3].text_input(
                    "item",
                    value="" if pd.isna(_row.get("item")) else str(_row.get("item")),
                    key=f"wia_item_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _material_code = _c[4].text_input(
                    "material_code",
                    value="" if pd.isna(_row.get("material_code")) else str(_row.get("material_code")),
                    key=f"wia_mat_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _labour_code = _c[5].text_input(
                    "labour_code",
                    value="" if pd.isna(_row.get("labour_code")) else str(_row.get("labour_code")),
                    key=f"wia_lab_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _equipment_code = _c[6].text_input(
                    "equipment_code",
                    value="" if pd.isna(_row.get("equipment_code")) else str(_row.get("equipment_code")),
                    key=f"wia_eq_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _lead_lift_code = None
                _col_idx = 7
                if _has_lead_lift:
                    _lead_lift_code = _c[7].text_input(
                        "lead_lift_code",
                        value="" if pd.isna(_row.get("lead_lift_code")) else str(_row.get("lead_lift_code")),
                        key=f"wia_ll_{_subpkg_code}_{_rid}",
                        label_visibility="collapsed",
                    )
                    _col_idx = 8
                _quantity = _c[_col_idx].text_input(
                    "quantity",
                    value="" if pd.isna(_row.get("quantity")) else str(float(_row.get("quantity"))),
                    key=f"wia_qty_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _remark = _c[_col_idx + 1].text_input(
                    "remark",
                    value="" if pd.isna(_row.get("remark")) else str(_row.get("remark")),
                    key=f"wia_rem_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )
                _delete_row = _c[_col_idx + 2].checkbox(
                    "delete",
                    key=f"wia_del_{_subpkg_code}_{_rid}",
                    label_visibility="collapsed",
                )

                _row_payload = {
                    "id": _rid,
                    "sor_code": _sor_code.strip(),
                    "subpackage_code": _subpkg_code,
                    "resource_type": _resource_type.strip(),
                    "item": _item.strip() or None,
                    "material_code": _material_code.strip() or None,
                    "labour_code": _labour_code.strip() or None,
                    "equipment_code": _equipment_code.strip() or None,
                    "quantity": _quantity.strip() or None,
                    "remark": _remark.strip() or None,
                }
                if _has_lead_lift:
                    _row_payload["lead_lift_code"] = _lead_lift_code.strip() if _lead_lift_code else None

                _edited_rows.append(_row_payload)
                if _delete_row:
                    _ids_to_delete.append(_rid)
                st.divider()
            _a_save, _a_spacer, _a_del = st.columns([2, 5, 2])
            with _a_save:
                _save_existing_wia_clicked = st.form_submit_button(
                    f"Save Existing {_subpkg_code} Analysis",
                    type="primary",
                    use_container_width=True,
                )
            with _a_del:
                _delete_existing_wia_clicked = st.form_submit_button(
                    f"Delete Selected {_subpkg_code}",
                    type="secondary",
                    use_container_width=True,
                )

        if _save_existing_wia_clicked:
            try:
                save_work_item_analysis_data(pd.DataFrame(_edited_rows), _work_item_analysis_columns)
                st.success(f"Existing work_item_analysis rows updated for {_subpkg_code}.")
                st.rerun()
            except Exception as _e:
                st.error(f"Failed to save existing work_item_analysis rows for {_subpkg_code}: {_e}")

        if _delete_existing_wia_clicked:
            if not _ids_to_delete:
                st.warning("Select at least one row in the delete column.")
            else:
                try:
                    delete_work_item_analysis_rows(_ids_to_delete)
                    _recalc_sor = (_sub_df["sor_code"].iloc[0] if not _sub_df.empty else analysis_tab_defaults.get(_subpkg_code, "TN_SOR_2025"))
                    recalculate_work_item_rate_admin(str(_recalc_sor).strip())
                    st.success(f"Deleted {len(_ids_to_delete)} row(s) from {_subpkg_code}.")
                    st.rerun()
                except Exception as _e:
                    st.error(f"Failed to delete rows for {_subpkg_code}: {_e}")

        st.markdown("### Add New Analysis Row")
        _default_sor = analysis_tab_defaults.get(_subpkg_code, "TN_SOR_2025")
        _a1, _a2, _a3, _a4, _a5 = st.columns([1.4, 1.4, 4.6, 1.2, 2.0])
        with _a1:
            _new_sor_code = st.text_input(
                "new_sor",
                key=f"wia_new_sor_{_subpkg_code}",
                value=_default_sor,
                label_visibility="collapsed",
            )
        with _a2:
            _resource_options = ["MATERIAL", "LABOUR", "EQUIPMENT"]
            if _has_lead_lift:
                _resource_options.append("LEAD & LIFT")
            _new_resource_type = st.selectbox(
                "new_resource_type",
                options=_resource_options,
                key=f"wia_new_type_{_subpkg_code}",
                label_visibility="collapsed",
            )
        with _a3:
            _selected_ref = None
            _selected_item_text = ""
            if _new_resource_type == "MATERIAL":
                _mat_df = load_material_code_lookup()
                _mat_options = [
                    (
                        str(r["unique_code"]).strip(),
                        str(r["category_name"]).strip(),
                        str(r["subcategory_name"]).strip(),
                        str(r["description"]).strip(),
                    )
                    for _, r in _mat_df.iterrows()
                ]
                _selected_ref = st.selectbox(
                    "material_ref",
                    options=_mat_options,
                    index=None if _mat_options else 0,
                    placeholder="Select material code",
                    format_func=lambda o: f"{o[0]} - {o[1]} - {o[2]} - {o[3]}",
                    key=f"wia_new_ref_{_subpkg_code}",
                    label_visibility="collapsed",
                )
                _selected_item_text = _selected_ref[3] if _selected_ref else ""
            elif _new_resource_type == "LABOUR":
                _lab_df = load_labour_code_lookup()
                _lab_options = [
                    (
                        str(r["unique_code"]).strip(),
                        str(r["category_name"]).strip(),
                        str(r["description"]).strip(),
                    )
                    for _, r in _lab_df.iterrows()
                ]
                _selected_ref = st.selectbox(
                    "labour_ref",
                    options=_lab_options,
                    index=None if _lab_options else 0,
                    placeholder="Select labour code",
                    format_func=lambda o: f"{o[0]} - {o[1]} - {o[2]}",
                    key=f"wia_new_ref_{_subpkg_code}",
                    label_visibility="collapsed",
                )
                _selected_item_text = _selected_ref[2] if _selected_ref else ""
            elif _new_resource_type == "EQUIPMENT":
                _eq_df = load_equipment_code_lookup()
                _eq_options = [
                    (str(r["unique_code"]).strip(), str(r["description"]).strip())
                    for _, r in _eq_df.iterrows()
                ]
                _selected_ref = st.selectbox(
                    "equipment_ref",
                    options=_eq_options,
                    index=None if _eq_options else 0,
                    placeholder="Select equipment code",
                    format_func=lambda o: f"{o[0]} - {o[1]}",
                    key=f"wia_new_ref_{_subpkg_code}",
                    label_visibility="collapsed",
                )
                _selected_item_text = _selected_ref[1] if _selected_ref else ""
            elif _new_resource_type == "LEAD & LIFT":
                _ll_df = load_lead_lift_code_lookup()
                _ll_options = [
                    (str(r["ll_code"]).strip(), str(r["item_name"]).strip())
                    for _, r in _ll_df.iterrows()
                ]
                _selected_ref = st.selectbox(
                    "leadlift_ref",
                    options=_ll_options,
                    index=None if _ll_options else 0,
                    placeholder="Select lead & lift code",
                    format_func=lambda o: f"{o[0]} - {o[1]}",
                    key=f"wia_new_ref_{_subpkg_code}",
                    label_visibility="collapsed",
                )
                _selected_item_text = _selected_ref[1] if _selected_ref else ""
        with _a4:
            _new_quantity = st.text_input(
                "new_qty",
                key=f"wia_new_qty_{_subpkg_code}",
                placeholder="0.000",
                label_visibility="collapsed",
            )
        with _a5:
            _new_remark = st.text_input(
                "new_rem",
                key=f"wia_new_rem_{_subpkg_code}",
                placeholder="Remark",
                label_visibility="collapsed",
            )

        _b1, _b2 = st.columns([3, 2])
        with _b1:
            _item_override_key = f"wia_new_item_{_subpkg_code}"
            if _item_override_key not in st.session_state:
                st.session_state[_item_override_key] = _selected_item_text
            elif st.session_state.get(f"wia_new_ref_{_subpkg_code}") != _selected_ref:
                st.session_state[_item_override_key] = _selected_item_text

            st.caption("Item (editable)")
            _new_item = st.text_input(
                "Item",
                key=_item_override_key,
                help="Auto-filled from selected code. You can edit it before saving.",
            )
        with _b2:
            _add_wia_clicked = st.button(f"Add New {_subpkg_code} Analysis Row", key=f"wia_add_btn_{_subpkg_code}", type="primary")

        if _add_wia_clicked:
            _new_row = {
                "id": None,
                "sor_code": _new_sor_code.strip(),
                "subpackage_code": _subpkg_code,
                "resource_type": _new_resource_type.strip(),
                "item": (_new_item.strip() or _selected_item_text or None),
                "material_code": None,
                "labour_code": None,
                "equipment_code": None,
                "quantity": _new_quantity.strip() or None,
                "remark": _new_remark.strip() or None,
            }
            if _new_resource_type == "MATERIAL":
                _new_row["material_code"] = _selected_ref[0] if _selected_ref else None
            elif _new_resource_type == "LABOUR":
                _new_row["labour_code"] = _selected_ref[0] if _selected_ref else None
            elif _new_resource_type == "EQUIPMENT":
                _new_row["equipment_code"] = _selected_ref[0] if _selected_ref else None
            elif _new_resource_type == "LEAD & LIFT" and _has_lead_lift:
                _new_row["lead_lift_code"] = _selected_ref[0] if _selected_ref else None

            if not _new_row["sor_code"] or not _selected_ref:
                st.error("Please select sor_code and a valid code from the dropdown.")
            else:
                try:
                    save_work_item_analysis_data(pd.DataFrame([_new_row]), _work_item_analysis_columns)
                    st.success(f"New work_item_analysis row added for {_subpkg_code}.")
                    clear_new_analysis_row_inputs(_subpkg_code)
                    st.rerun()
                except Exception as _e:
                    st.error(f"Failed to add work_item_analysis row for {_subpkg_code}: {_e}")
