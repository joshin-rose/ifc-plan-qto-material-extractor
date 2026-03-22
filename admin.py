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


st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("Admin Panel")

tabs = st.tabs(["SOR Data", "Labour", "Material", "Work Items"])

with tabs[0]:
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

with tabs[1]:
    st.info("Labour tab placeholder. Add next based on your workflow.")

with tabs[2]:
    st.info("Material tab placeholder. Add next based on your workflow.")

with tabs[3]:
    st.info("Work Items tab placeholder. Add next based on your workflow.")
