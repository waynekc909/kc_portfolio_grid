import os
import json
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VALID_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.svg', '.JPG', '.JPEG', '.PNG')

# 1. Auto-detect the HTML file
candidate_files = glob.glob(os.path.join(BASE_DIR, "*.html"))
target_html_path = next((f for f in candidate_files if any(x in os.path.basename(f).lower() for x in ["portfolio", "konigstein", "index"])), candidate_files[0] if candidate_files else None)

if not target_html_path:
    print(f"Error: No .html file found in {BASE_DIR}")
    exit(1)

html_filename = os.path.basename(target_html_path)

# 2. Map all local folders to their image files
folder_images = {}
for root, _, files in os.walk(BASE_DIR):
    rel_root = os.path.relpath(root, BASE_DIR).replace("\\", "/")
    if rel_root == ".": continue
    valid_files = [f for f in files if f.endswith(VALID_EXTS)]
    if valid_files:
        sorted_files = sorted(valid_files, key=lambda x: (0 if "_profile" in x.lower() else 1, x.lower()))
        folder_images[rel_root] = [f"./{rel_root}/{f}" for f in sorted_files]

# 3. Read the portfolio HTML file
with open(target_html_path, "r", encoding="utf-8") as f:
    html = f.read()

pattern = r'(<script id="assets-data" type="application/json">)(.*?)(</script>)'
match = re.search(pattern, html, re.DOTALL)
assets = json.loads(match.group(2))

# 4. UPDATED EXACT PATH MAPPING
folder_mapping = {
    "otjomuise": "KAHF Portfolio Images/Otjomuise Lifestyle (MPG)",
    "erf1470": "KAHF Portfolio Images/Khomasdal Erf 1470",
    "nkurenkuru": "KAHF Portfolio Images/Nkurenkuru Ext 2 Phase 2(Lithon)",
    "lih": "KAHF Portfolio Images/Nkurenkuru Ext 2 Phase 1 (LIH)",
    "dumatau_krohnlein": "KAHF Portfolio Images/Duma Tau Kronlein",
    "turnstone": "KAHF Portfolio Images/Turnstone Images",
    "dunescape": "KAHF Portfolio Images/Dunescape Swakopmund", 
    "rockycrest": "KAHF Portfolio Images/Damask Erf 5159 The Ridge", 
    "lazarett": "KCPIF Images/51 on Lazarett",
    "beethoven": "KCPIF Images/Beethoven Heights",
    "citygardens": "KCPIF Images/City Gardens",
    "dumatau_omuthiya": "KCPIF Images/Duma Tau - Omuthiya",
    "dumatau_tsei": "KCPIF Images/Duma Tau - Tseiblaagte",
    "morningside": "KCPIF Images/Morning Side",
    "sturrock": "KCPIF Images/Niilenge - Sturrock Lofts",
    "gobabis11": "KCPIF Images/Nilenge - Gobabis (Ext 11)", # Note: Script recursively checks subfolders like "Gobabis 2022"
    "riverthorn": "KCPIF Images/Riverthorn",
    "turahill": "KCPIF Images/Tura Hill Okahandja",
    "calgrokuumba_otjomuise10": "KCPIF Images/CalgroKuumba Otjomuise 10",
    "eureka": "KCPIF Images/Eureka",
    "heikky": "KCPIF Images/Heikky",
    "hoseakutako": "KCPIF Images/Hosea Kutako Apartments",
    "jedidja": "KCPIF Images/Jedidja",
    "okamita_osona": "KCPIF Images/Okamita(Osona Village)",
    "ongoshi": "KCPIF Images/Ongoshi",
    "raotra": "KCPIF Images/Raotra",
    "riverport": "KCPIF Images/Riverport"
}

# 5. Update asset image lists
updated = 0
for asset in assets:
    aid = asset.get("id")
    target_folder = folder_mapping.get(aid)
    if target_folder and target_folder in folder_images:
        asset["images"] = folder_images[target_folder]
        updated += 1

# 6. Write back to HTML file
new_json = json.dumps(assets, indent=2)
new_html = html[:match.start(2)] + new_json + html[match.end(2):]

with open(target_html_path, "w", encoding="utf-8") as f:
    f.write(new_html)

print(f"✓ Sync complete: Updated {updated} projects with the exact KAHF/KCPIF images.")