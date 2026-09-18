import openpyxl

wb = openpyxl.load_workbook('KAHF_Consolidated_Fund_Model  Updated.xlsx', data_only=True)
ws = wb['2. Project Performance']

print("\n--- EXCEL ROW & COLUMN INSPECTION ---")
for r in range(1, 25):
    row_vals = [ws.cell(r, c).value for c in range(1, 15)]
    if any(row_vals):
        # Format values cleanly for quick reading
        clean_vals = [f"{v:.4f}" if isinstance(v, float) else str(v) for v in row_vals]
        print(f"Row {r:2d}: {clean_vals}")