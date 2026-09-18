import csv
import json
import re
import os

CSV_FILE = "Portfolio_API_Master.csv"
HTML_FILE = "index.html"
IMAGE_DIRS = ["KAHF Portfolio Images", "KCPIF Images"]

def get_row_val(row, *key_names, default=""):
    """Case-insensitive, symbol-agnostic lookup for CSV dictionary keys."""
    for key_name in key_names:
        target_norm = key_name.lower().replace("_", "").replace(" ", "")
        for k, v in row.items():
            if k and k.lower().replace("_", "").replace(" ", "") == target_norm:
                return str(v).strip() if v is not None else default
    return default

def safe_float(val):
    try: return float(str(val).replace(',','').replace('%','').strip())
    except: return 0.0

def safe_int(val):
    try: return int(float(str(val).replace(',','').replace('%','').strip()))
    except: return 0

def normalize(text):
    """Normalizes text for fuzzy matching (removes special chars and lowercase)."""
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def scan_disk_for_images():
    """Scans local image directories and maps files to project search keys."""
    disk_images = {}
    
    for img_dir in IMAGE_DIRS:
        if not os.path.exists(img_dir):
            continue
        
        for root, _, files in os.walk(img_dir):
            if not files:
                continue
            
            folder_name = os.path.basename(root)
            norm_folder = normalize(folder_name)
            
            image_paths = []
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and not file.startswith('~$'):
                    rel_path = os.path.join(root, file).replace("\\", "/")
                    image_paths.append(rel_path)
            
            # Prioritize 'profile' images at the top of the array
            image_paths.sort(key=lambda p: 0 if 'profile' in os.path.basename(p).lower() else 1)
            
            if image_paths and norm_folder:
                disk_images[norm_folder] = image_paths

    return disk_images

def csv_to_json(csv_path, disk_images):
    assets = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            asset_id = get_row_val(row, "id", "asset_id", "assetid", "project_id")
            asset_name = get_row_val(row, "name", "asset_name", "project_name", "title")
            
            # Fallback ID generation if ID is missing but name exists
            if not asset_id and asset_name:
                asset_id = normalize(asset_name)
                
            if not asset_id and not asset_name:
                continue
            
            # Match disk images by ID, asset name, or fuzzy substring
            matched_images = []
            norm_id = normalize(asset_id)
            norm_name = normalize(asset_name)
            
            for folder_norm, paths in disk_images.items():
                if folder_norm == norm_id or folder_norm == norm_name or folder_norm in norm_name or norm_id in folder_norm:
                    matched_images = paths
                    break
            
            milestones = [m.strip() for m in get_row_val(row, "milestones").split('|') if m.strip()]
            covenants = [c.strip() for c in get_row_val(row, "covenants").split('|') if c.strip()]
            
            fund = get_row_val(row, "fund")
            fund_long = get_row_val(row, "fund_long_name", "fundlongname")
            fund_label = f"{fund} · {fund_long}" if fund_long else fund
            
            asset = {
                "id": asset_id,
                "fund": fund,
                "fundLabel": fund_label,
                "name": asset_name,
                "sector": get_row_val(row, "sector"),
                "sectorLabel": get_row_val(row, "sector_label", "sectorlabel"),
                "region": get_row_val(row, "region"),
                "regionLabel": get_row_val(row, "region_label", "regionlabel"),
                "location": get_row_val(row, "location"),
                "status": get_row_val(row, "status"),
                "statusLabel": get_row_val(row, "status_label", "statuslabel"),
                "statusBadge": get_row_val(row, "status_badge", "statusbadge"),
                "pct": safe_float(get_row_val(row, "pct")),
                "units": safe_int(get_row_val(row, "units")) if get_row_val(row, "units") else None,
                "unitsDisplay": get_row_val(row, "units_display", "unitsdisplay"),
                "areaM2": safe_int(get_row_val(row, "area_m2", "aream2")),
                "irr": safe_float(get_row_val(row, "irr")),
                "irrType": get_row_val(row, "irr_type", "irrtype"),
                "metric2Label": get_row_val(row, "metric2_label", "metric2label"),
                "metric2Value": get_row_val(row, "metric2_value", "metric2value"),
                "dealSize": safe_int(get_row_val(row, "deal_size", "dealsize")),
                "equityInvested": safe_int(get_row_val(row, "equity_invested", "equityinvested")),
                "debtFacility": safe_int(get_row_val(row, "debt_facility", "debtfacility")),
                "equityPct": safe_int(get_row_val(row, "equity_pct", "equitypct")),
                "valuation": safe_int(get_row_val(row, "valuation")) if get_row_val(row, "valuation") else None,
                "coInvest": get_row_val(row, "co_invest", "coinvest"),
                "holdPeriod": get_row_val(row, "hold_period", "holdperiod"),
                "exitMultiple": get_row_val(row, "exit_multiple", "exitmultiple"),
                "moicNumeric": safe_float(get_row_val(row, "moic_numeric", "moicnumeric")) if get_row_val(row, "moic_numeric", "moicnumeric") else None,
                "secondary": get_row_val(row, "secondary_text", "secondary"),
                "images": matched_images,
                "overview": get_row_val(row, "overview"),
                "milestones": milestones,
                "waterfallText": get_row_val(row, "waterfall_text", "waterfalltext"),
                "covenants": covenants,
                "esgUnits": get_row_val(row, "esg_units", "esgunits"),
                "esgJobs": get_row_val(row, "esg_jobs", "esgjobs"),
                "esgGreen": get_row_val(row, "esg_green", "esggreen"),
                "esgNotes": get_row_val(row, "esg_notes", "esgnotes")
            }
            assets.append(asset)
    return assets

def inject_json_into_html(fresh_data, html_path):
    if not fresh_data:
        print("⚠️ Warning: No projects found in CSV! Aborting injection to protect index.html.")
        return False

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    pattern = r'(<script id="assets-data" type="application/json">)(.*?)(</script>)'
    match = re.search(pattern, html, re.DOTALL)

    if match:
        new_json_str = json.dumps(fresh_data, indent=2, ensure_ascii=False)
        new_html = html[:match.start(2)] + "\n" + new_json_str + "\n" + html[match.end(2):]
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"✓ Successfully injected {len(fresh_data)} projects into HTML.")
        return True
    else:
        print("Error: Could not locate <script id=\"assets-data\"> tag in HTML.")
        return False

if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        print(f"Error: '{CSV_FILE}' not found.")
    else:
        print("1. Scanning local image directories...")
        disk_images = scan_disk_for_images()
        
        print("2. Parsing CSV data and mapping image folders...")
        fresh_data = csv_to_json(CSV_FILE, disk_images)
        
        print("3. Injecting payload into HTML...")
        inject_json_into_html(fresh_data, HTML_FILE)