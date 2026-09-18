import csv
import json
import re
import os

CSV_FILE = "Portfolio_API_Master.csv"
HTML_FILE = "index.html"
IMAGE_DIRS = ["KAHF Portfolio Images", "KCPIF Images"]

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
            def safe_float(val):
                try: return float(val.replace(',','').replace('%','').strip())
                except: return 0.0
            def safe_int(val):
                try: return int(float(val.replace(',','').replace('%','').strip()))
                except: return 0
            
            asset_id = row.get("id", "").strip()
            asset_name = row.get("name", "").strip()
            if not asset_id:
                continue
            
            # Match disk images by ID, asset name, or fuzzy substring
            matched_images = []
            norm_id = normalize(asset_id)
            norm_name = normalize(asset_name)
            
            for folder_norm, paths in disk_images.items():
                if folder_norm == norm_id or folder_norm == norm_name or folder_norm in norm_name or norm_id in folder_norm:
                    matched_images = paths
                    break
            
            milestones = [m.strip() for m in row.get("milestones", "").split('|') if m.strip()]
            covenants = [c.strip() for c in row.get("covenants", "").split('|') if c.strip()]
            
            asset = {
                "id": asset_id,
                "fund": row.get("fund", ""),
                "fundLabel": f"{row.get('fund', '')} · {row.get('fund_long_name', '')}",
                "name": asset_name,
                "sector": row.get("sector", ""),
                "sectorLabel": row.get("sector_label", ""),
                "region": row.get("region", ""),
                "regionLabel": row.get("region_label", ""),
                "location": row.get("location", ""),
                "status": row.get("status", ""),
                "statusLabel": row.get("status_label", ""),
                "statusBadge": row.get("status_badge", ""),
                "pct": safe_float(row.get("pct", 0)),
                "units": safe_int(row.get("units", 0)) if row.get("units", "").strip() else None,
                "unitsDisplay": row.get("units_display", ""),
                "areaM2": safe_int(row.get("area_m2", 0)),
                "irr": safe_float(row.get("irr", 0)),
                "irrType": row.get("irr_type", ""),
                "metric2Label": row.get("metric2_label", ""),
                "metric2Value": row.get("metric2_value", ""),
                "dealSize": safe_int(row.get("deal_size", 0)),
                "equityInvested": safe_int(row.get("equity_invested", 0)),
                "debtFacility": safe_int(row.get("debt_facility", 0)),
                "equityPct": safe_int(row.get("equity_pct", 0)),
                "valuation": safe_int(row.get("valuation", 0)) if row.get("valuation", "").strip() else None,
                "coInvest": row.get("co_invest", ""),
                "holdPeriod": row.get("hold_period", ""),
                "exitMultiple": row.get("exit_multiple", ""),
                "moicNumeric": safe_float(row.get("moic_numeric", 0)) if row.get("moic_numeric", "").strip() else None,
                "secondary": row.get("secondary_text", ""),
                "images": matched_images,
                "overview": row.get("overview", ""),
                "milestones": milestones,
                "waterfallText": row.get("waterfall_text", ""),
                "covenants": covenants,
                "esgUnits": row.get("esg_units", ""),
                "esgJobs": row.get("esg_jobs", ""),
                "esgGreen": row.get("esg_green", ""),
                "esgNotes": row.get("esg_notes", "")
            }
            assets.append(asset)
    return assets

def inject_json_into_html(fresh_data, html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    pattern = r'(<script id="assets-data" type="application/json">)(.*?)(</script>)'
    match = re.search(pattern, html, re.DOTALL)

    if match:
        new_json_str = json.dumps(fresh_data, indent=2, ensure_ascii=False)
        # String slicing completely avoids regex backslash escape errors (\u, \Users, etc.)
        new_html = html[:match.start(2)] + "\n" + new_json_str + "\n" + html[match.end(2):]
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_html)
        print("✓ Successfully injected updated data & images into HTML.")
    else:
        print("Error: Could not locate <script id=\"assets-data\"> tag in HTML.")

if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        print(f"Error: '{CSV_FILE}' not found. Please save your Excel Master as a CSV first.")
    else:
        print("1. Scanning local image directories...")
        disk_images = scan_disk_for_images()
        
        print("2. Parsing CSV data and mapping image folders...")
        fresh_data = csv_to_json(CSV_FILE, disk_images)
        
        print("3. Injecting payload into HTML...")
        inject_json_into_html(fresh_data, HTML_FILE)