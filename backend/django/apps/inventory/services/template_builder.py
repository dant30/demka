"""
Generate the DEMKA product import template.

Uses openpyxl to build a workbook in memory with:
  * "Products" sheet — header row, dropdowns for enum fields, sample rows
  * "Instructions" sheet — column-by-column reference
"""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


COLUMNS = [
    # (header,        width, required?)
    ("sku",               18, True),
    ("name",              45, True),
    ("category",          22, True),
    ("product_type",      18, False),
    ("brand",             18, False),
    ("unit",              10, False),
    ("cost_price",        14, False),
    ("retail_price",      14, True),
    ("wholesale_price",   16, True),
    ("is_stocked",        12, False),
    ("reorder_level",     15, False),
    ("reorder_qty",       13, False),
    ("barcode",           20, False),
    ("compatibility_notes", 45, False),
    ("etims_item_cls_cd", 22, False),
    ("part_number",        22, False),
]

SAMPLES = [
    [
        "SAMPLE-AUTO-001", "Oil Filter – Toyota Corolla", "Engine", "AUTO_PART",
        "Toyota", "PIECE", 450, 550, 500, "TRUE", 20, 50, "",
        "Fits Toyota Corolla 2003–2013 (1.8L)", "", "",
    ],
    [
        "SAMPLE-MOTO-001", "Brake Shoe – CG125 Front", "Braking", "MOTORBIKE_PART",
        "Honda", "PAIR", 350, 500, 450, "TRUE", 30, 60, "",
        "Fits CG125, CG150, Bajaj Boxer", "", "",
    ],
]

INSTRUCTIONS = [
    ("DEMKA Product Import Template", ""),
    ("", ""),
    ("How to use", ""),
    ("1.", "Fill in the Products sheet. Do not rename or reorder columns."),
    ("2.", "Required fields: sku, name, category, retail_price, wholesale_price."),
    ("3.", "Delete the SAMPLE-* rows before uploading your data."),
    ("4.", "Save as .xlsx (or .csv) and upload via Inventory → Import Products."),
    ("", ""),
    ("Column reference", ""),
    ("sku", "Unique product code. Required."),
    ("name", "Display name. Required."),
    ("category", "Category name — auto-created if it doesn't exist. Required."),
    ("product_type", "MOTORBIKE_PART, AUTO_PART, or ACCESSORY. Default AUTO_PART."),
    ("brand", "Manufacturer / brand name."),
    ("unit", "PIECE, SET, PAIR, or LITRE. Default PIECE."),
    ("cost_price", "Purchase cost per unit (decimal)."),
    ("retail_price", "Shop selling price (decimal). Required."),
    ("wholesale_price", "Reseller / field selling price (decimal). Required."),
    ("is_stocked", "TRUE or FALSE. Default FALSE for order-on-demand items."),
    ("reorder_level", "Alert when stock hits this level. Integer."),
    ("reorder_qty", "Suggested reorder quantity. Integer."),
    ("barcode", "Optional unique barcode. Leave blank if none."),
    ("part_number", "Manufacturer or supplier part number, if available."),
    ("compatibility_notes", "Free text, e.g. 'Fits Toyota Hilux 2010–2018'."),
    ("etims_item_cls_cd", "KRA eTIMS classification code (10 digits). Optional but required before selling."),
    ("", ""),
    ("Rules & tips", ""),
    ("SKUs must be unique", "Duplicates (existing or within the file) are rejected."),
    ("Prices below cost", "Imported as warnings — the product is still created."),
    ("All-or-nothing mode", "By default, if any row has errors, nothing is imported."),
    ("Skip-invalid mode", "Tick the 'Skip invalid rows' checkbox in the UI to import only the valid rows."),
]


def build_template() -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    # Header row
    header_fill = PatternFill("solid", fgColor="2563EB")
    header_font = Font(bold=True, color="FFFFFF")

    for col_idx, (header, width, _req) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[1].height = 22

    # Sample rows
    for r_idx, row in enumerate(SAMPLES, start=2):
        for c_idx, value in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=value)

    # Dropdowns (rows 2..2000)
    def _add_dropdown(column_letter: str, options: str):
        dv = DataValidation(type="list", formula1=f'"{options}"', allow_blank=True)
        dv.add(f"{column_letter}2:{column_letter}2000")
        ws.add_data_validation(dv)

    _add_dropdown("D", "MOTORBIKE_PART,AUTO_PART,ACCESSORY")
    _add_dropdown("F", "PIECE,SET,PAIR,LITRE")
    _add_dropdown("J", "TRUE,FALSE")

    # Freeze top row
    ws.freeze_panes = "A2"

    # Instructions sheet
    ws2 = wb.create_sheet("Instructions")
    for r_idx, (col1, col2) in enumerate(INSTRUCTIONS, start=1):
        ws2.cell(row=r_idx, column=1, value=col1)
        ws2.cell(row=r_idx, column=2, value=col2)
    ws2.column_dimensions["A"].width = 26
    ws2.column_dimensions["B"].width = 90
    ws2.cell(row=1, column=1).font = Font(bold=True, size=14, color="2563EB")

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer