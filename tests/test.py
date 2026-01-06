"""
This script extract necessary details needed from HTML page 
"""
# ------------------------------
# IMPORTS
# ------------------------------
from bs4 import BeautifulSoup       # For parsing HTML
import csv                          # For writing CSV files
import os
from typing import Dict, List

# ------------------------------
# CONSTANTS
# ------------------------------



# ------------------------------
# Functions
# -----------------------------
def _td_text_safe(cols: List, idx: int) -> str:
    """Return trimmed text of cols[idx] or empty string if index missing."""
    try:
        return cols[idx].get_text(strip=True)
    except Exception:
        return ""
    

def _radio_checked_value(radios) -> str:
    """
    Function for page "Mes assignations" only

    Given list of radio input tags, return:
        'Accepté' if checked radio has value '1'
        'Refusé' if checked radio has value '2'
        '' otherwise
    """
    for r in radios:
        # Use has_attr to reliably detect presence of checked attribute
        if r.has_attr('checked'):
            val = r.attrs.get('value', '').strip()
            if val == '1':
                return 'Accepté'
            elif val == '2':
                return 'Refusé'
            else:
                # if checked but value is something else, return raw value
                return val
    return ""



def _checkbox_checked_status_for_name(checkboxes, name_contains: str) -> str:
    """
    Look for a checkbox whose 'name' contains name_contains.
    Return 'yes' if that checkbox has checked attribute, 'no' if not checked,
    or '' when not found.
    """
    for cb in checkboxes:
        cname = cb.attrs.get('name', '')
        if name_contains in cname and 'isgamedonealone' not in cname:
            return 'yes' if cb.has_attr('checked') else 'no'
    return ""



def load_html(html_file: str, csv_file: str, column_mapping: Dict[str, int]):
    """
    Generic loader to extract rows from an HTML table and save to CSV.
    
    Parameters
    ----------
    html_file: str
        path to HTML file
    csv_file: str
        path to output CSV
    column_mapping: dict {column_name: td_index_in_row}
        mapping of columns and their indexes to retrieve from HTML file
    
    """

    # Check if HTML file exists
    if not os.path.exists(html_file):
        print(f"ERROR: '{html_file}' not found in the current directory.")
        return
    
    # Load HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = BeautifulSoup(file, 'html.parser')

    # Find all table rows represented by <tr> tag in HTML file
    rows = html_content.find_all('tr')
    print(f"Number of records found on page: {len(rows)}")

    # DEBUG : write ALL <tr> rows exactly as BeautifulSoup sees them
    with open("debug_rows.html", "w", encoding="utf-8") as dbg:
        for i, r in enumerate(rows):
            dbg.write(f"\n\n==== ROW {i} START ====\n")
            dbg.write(str(r))
            dbg.write(f"\n==== ROW {i} END ====\n")


    extracted = [] # This list will hold all the extracted data from HTML file

    # Loop through each row in the table
    for row in rows:
        cols = row.find_all('td') # Find all <td> elements in the row (table cells)
        if not cols:
            # skip empty rows or non-table rows
            continue 
        
        # Basic extraction of mapped columns as text (safe)
        row_values = {col_name: _td_text_safe(cols, idx) for col_name, idx in column_mapping.items()}

        # --- Handle "Accepte/Refuse" when it may be radios OR text ---
        # If radio inputs exist in this row, use them to determine Accepté/Refusé.
        # Otherwise fallback to text inside the mapped column (if provided).
        if 'Accepté/Refusé' in column_mapping:
            td_index = column_mapping['Accepté/Refusé']
            td = cols[td_index] if td_index < len(cols) else None
            print(f"td_index: {td_index}; td: {td}")
            

        # --- Handle "Match fait" when it may be a checkbox OR text ---
        # Prefer checkbox state if present, otherwise use the mapped text.
        if 'Match fait' in column_mapping:
            checkboxes = row.find_all('input', {'type': 'checkbox'})
            if checkboxes:
                cb_status = _checkbox_checked_status_for_name(checkboxes, 'isgamedone')
                if cb_status != "":
                    # store yes/no
                    row_values['Match fait'] = cb_status
                # else: keep mapped text fallback

        # If you wish to filter only accepted & not done rows here, you can.
        # For now we append all rows (caller can filter).  
        extracted.append([row_values.get(col, "") for col in column_mapping.keys()])

    # Once looped through table and data extracted, save result to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = list(column_mapping.keys())
        writer.writerow(headers) # Write header
        writer.writerows(extracted) # Write all rows
    print(f"Extraction complete: {len(extracted)} rows written to '{csv_file}'.")




