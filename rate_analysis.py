import mysql.connector

# ---------------- DATABASE CONNECTION ---------------- #

conn = mysql.connector.connect(
    host="localhost",
    user="architect",
    password="ap@2101",
    database="arch_db"
)

cursor = conn.cursor(dictionary=True)

sor_code = "TN_SOR_2025"
subpackage = "E1"

print("\n==============================")
print("RATE ANALYSIS :", subpackage)
print("==============================\n")

# ---------------- GET ANALYSIS QUANTITY ---------------- #

cursor.execute("""
SELECT analysis_quantity, analysis_unit
FROM work_item_subpackage
WHERE sor_code=%s AND subpackage_code=%s
""",(sor_code,subpackage))

analysis = cursor.fetchone()

analysis_qty = analysis["analysis_quantity"]
analysis_unit = analysis["analysis_unit"]

print(f"Analysis Quantity : {analysis_qty} {analysis_unit}\n")

# ---------------- FETCH MATERIAL + LABOUR ---------------- #

cursor.execute("""
SELECT
a.item,
a.resource_type,
a.quantity,
COALESCE(m.unit,l.unit) AS unit,
COALESCE(m.base_rate,l.base_rate) AS rate,
COALESCE(m.unit_multiplier,l.unit_multiplier) AS multiplier

FROM work_item_analysis a

LEFT JOIN sor_material_data m
ON a.material_code = m.unique_code

LEFT JOIN sor_labour_data l
ON a.labour_code = l.unique_code

WHERE a.sor_code=%s AND a.subpackage_code=%s
""",(sor_code,subpackage))

rows = cursor.fetchall()

print("Item Breakdown")
print("--------------------------------------------")

total_A = 0

for r in rows:

    qty = r["quantity"]
    rate = r["rate"]
    multiplier = r["multiplier"] if r["multiplier"] else 1

    amount = (qty / multiplier) * rate
    total_A += amount

    print(f"{r['item']}")
    print(f"  Type : {r['resource_type']}")
    print(f"  Qty  : {qty}")
    print(f"  Rate : {rate}")
    print(f"  Amount = {amount:,.2f}\n")

print("--------------------------------------------")
print(f"TOTAL A (Material + Labour) = {total_A:,.2f}\n")

# ---------------- FETCH CHARGES ---------------- #

cursor.execute("""
SELECT charge_name, percentage
FROM work_item_charges
""")

charges = cursor.fetchall()

print("Charges")
print("--------------------------------------------")

total_B = 0

for c in charges:

    charge_amount = total_A * (c["percentage"] / 100)
    total_B += charge_amount

    print(f"{c['charge_name']} ({c['percentage']}%) = {charge_amount:,.2f}")

print("--------------------------------------------")
print(f"TOTAL B (All Charges) = {total_B:,.2f}\n")

# ---------------- FINAL TOTAL ---------------- #

grand_total = total_A + total_B

print("============================================")
print(f"TOTAL = A + B = {grand_total:,.2f}")

rate_per_unit = grand_total / analysis_qty

print(f"\nRATE PER {analysis_unit} = {rate_per_unit:,.2f}")
print("============================================")

# ---------------- WRITE FINAL RATE TO DATABASE ---------------- #

cursor.execute("""
UPDATE work_item_rate
SET amount=%s
WHERE sor_code=%s AND subpackage_code=%s
""",(rate_per_unit, sor_code, subpackage))

conn.commit()

print("\n✅ Final Rate Stored in work_item_rate Table")

# ---------------- CLOSE CONNECTION ---------------- #

cursor.close()
conn.close()