import csv
import os
import zipfile
from typing import List, Tuple
from xml.sax.saxutils import escape


def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def read_csv_rows(path: str) -> List[List[str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return [[c if c is not None else "" for c in row] for row in reader]


def sanitize_sheet_name(name: str) -> str:
    bad = ['\\', '/', '*', '?', ':', '[', ']']
    out = "".join("_" if ch in bad else ch for ch in name)
    out = out.strip() or "Sheet"
    return out[:31]


def col_name(index_1_based: int) -> str:
    n = index_1_based
    out = []
    while n > 0:
        n, r = divmod(n - 1, 26)
        out.append(chr(65 + r))
    return "".join(reversed(out))


def is_number(value: str) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    try:
        float(s)
        return True
    except Exception:
        return False


def worksheet_xml(rows: List[List[str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    for r_idx, row in enumerate(rows, start=1):
        lines.append(f'<row r="{r_idx}">')
        for c_idx, val in enumerate(row, start=1):
            ref = f"{col_name(c_idx)}{r_idx}"
            txt = "" if val is None else str(val)
            if is_number(txt):
                lines.append(f'<c r="{ref}"><v>{escape(txt)}</v></c>')
            else:
                lines.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(txt)}</t></is></c>')
        lines.append("</row>")
    lines.append("</sheetData>")
    lines.append("</worksheet>")
    return "".join(lines)


def workbook_xml(sheet_names: List[str]) -> str:
    sheets = []
    for i, n in enumerate(sheet_names, start=1):
        sheets.append(
            f'<sheet name="{escape(n)}" sheetId="{i}" r:id="rId{i}"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{''.join(sheets)}</sheets>"
        "</workbook>"
    )


def workbook_rels_xml(sheet_count: int) -> str:
    rels = []
    for i in range(1, sheet_count + 1):
        rels.append(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i}.xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{''.join(rels)}"
        "</Relationships>"
    )


def root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def content_types_xml(sheet_count: int) -> str:
    overrides = [
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    ]
    for i in range(1, sheet_count + 1):
        overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{''.join(overrides)}"
        "</Types>"
    )


def build_workbook(sheets: List[Tuple[str, List[List[str]]]], out_path: str) -> None:
    sheet_names = [sanitize_sheet_name(n) for n, _ in sheets]
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(sheets)))
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(sheets)))
        for i, (_, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", worksheet_xml(rows))


def ensure_inputs(base: str, required_csvs: List[str]) -> None:
    # Regenerate only if one or more source CSVs are missing.
    missing = [p for p in required_csvs if not os.path.exists(p)]
    if not missing:
        return

    wall_py = os.path.join(base, "Wall.py")
    rcc_py = os.path.join(base, "RCC.py")
    if os.path.exists(wall_py):
        os.system(f'python "{wall_py}"')
    if os.path.exists(rcc_py):
        os.system(f'python "{rcc_py}"')


def main() -> None:
    base = script_dir()
    wall_sheet = os.path.join(base, "Wall_Sheet.csv")
    wall_summary = os.path.join(base, "Wall_Sheet_Summary.csv")
    rcc_sheet = os.path.join(base, "RCC_sheet.csv")
    rcc_summary = os.path.join(base, "RCC_Summary.csv")

    required = [wall_sheet, wall_summary, rcc_sheet, rcc_summary]
    ensure_inputs(base, required)
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        raise SystemExit(f"Missing input CSV(s): {', '.join(missing)}")

    sheets = [
        ("Wall_Sheet", read_csv_rows(wall_sheet)),
        ("Wall_Summary", read_csv_rows(wall_summary)),
        ("RCC_Sheet", read_csv_rows(rcc_sheet)),
        ("RCC_Summary", read_csv_rows(rcc_summary)),
    ]

    out_xlsx = os.path.join(base, "final.xlsx")
    build_workbook(sheets, out_xlsx)
    print(f"Created {out_xlsx} with 4 sheets.")
    print("Note: CSV format cannot contain multiple sheets, so output is .xlsx.")


if __name__ == "__main__":
    main()
