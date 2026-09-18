import csv
import json
import re
import os

# File paths
CSV_FILE = "Portfolio_API_Master.csv"
HTML_FILE = "index.html"

def get_existing_images(html_path):
    """Extracts existing images from the HTML so the CSV doesn't overwrite them."""
    if not os.path.exists(html_path):
        return {}
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    pattern = r'(<script id="assets-data" type="application/json">)(.*?)(</script>)'
    match = re.search(pattern, html, re.DOTALL)
    
    image_map = {}
    if match:
        try:
            assets = json.loads(match.group(2))
            for a in assets:
                image_map[a.get("id")] = a.get("images", [])
        except Exception as e:
            print(f"Warning: Could not parse existing JSON images. {e}")
    return image_map

def csv_to_json(csv_path, image_map):
    assets = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Safely handle empty strings and formatted numbers (e.g. "33,000,000")
            def safe_float(val):
                try: return float(val.replace(',','').replace('%','').strip())
                except: return 0.0
            def safe_int(val):
                try: return int(float(val.replace(',','').replace('%','').strip()))
                except: return 0
            
            asset_id = row.get("id", "").strip()
            if not asset_id:
                continue # Skip empty rows
            
            # Convert pipe-separated strings into formal bullet lists
            milestones = [m.strip() for m in row.get("milestones", "").split('|') if m.strip()]
            covenants = [c.strip() for c in row.get("covenants", "").split('|') if c.strip()]
            
            asset = {
                "id": asset_id,
                "fund": row.get("fund", ""),
                "fundLabel": f"{row.get('fund', '')} · {row.get('fund_long_name', '')}",
                "name": row.get("name", ""),
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
                "images": image_map.get(asset_id, []), # Inject preserved image paths
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

def inject_json_into_html(json_data, html_path):
    if not os.path.exists(html_path):
        print(f"Error: HTML file '{html_path}' not found.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Target the specific <script> tag block
    pattern = r'(<script id="assets-data" type="application/json">)(.*?)(</script>)'
    
    if not re.search(pattern, html, re.DOTALL):
        print("Error: Could not find <script id='assets-data'> tag in HTML.")
        return

    new_json_str = json.dumps(json_data, indent=2)
    new_html = re.sub(pattern, rf'\g<1>{new_json_str}\g<3>', html, flags=re.DOTALL)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"✓ Success! Injected {len(json_data)} active project ledgers into the web dashboard.")

if __name__ == "__main__":
    if not os.path.exists(CSV_FILE):
        print(f"Error: '{CSV_FILE}' not found. Please save your Excel Master as a CSV first.")
    else:
        print("1. Locking existing image paths...")
        img_map = get_existing_images(HTML_FILE)
        
        print("2. Parsing live CSV data...")
        fresh_data = csv_to_json(CSV_FILE, img_map)
        
        print("3. Updating web presentation...")
        inject_json_into_html(fresh_data, HTML_FILE)
        