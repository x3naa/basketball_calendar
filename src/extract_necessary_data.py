"""
This script extracts necessary details needed from an HTML page

INPUT: 
    - html_file: name of html file from which data needs to be extracted
    - csv_file: name of file to store output
    - column_mapping: specific columns needed from HTML page

OUTPUT: 
    - csv file containing only data required

"""
# ------------------------------
# IMPORTS
# ------------------------------
from bs4 import BeautifulSoup       # THIRD-PARTY: Parse and navigate HTML content
import csv                          # STANDARD: Read/write CSV files
import os                           # STANDARD: File existence checks
from typing import List             # STANDARD: Type hints for better readability

# ------------------------------
# CONSTANTS
# ------------------------------



# ------------------------------
# Helper Functions
# -----------------------------
def _td_text_safe(cols: List, idx: int) -> str:
    """Return trimmed visible text of cols[idx] or empty string if index missing."""
    try:
        td = cols[idx]
        td_copy = td.__copy__() # Make a shallow copy so we do NOT mutate the original BeautifulSoup tree

        # Remove non-visible elements (hidden inputs, scripts, styles)
        for tag in td_copy.find_all(['input', 'script', 'style']):
            tag.decompose()

        return td_copy.get_text(strip=True)
    except Exception:
        return ""



def _td_link_safe(cols: List, idx: int) -> str:
    """Return the first <a href=""> link in this <td>, or empty string."""
    try:
        td = cols[idx]
        a = td.find("a", href=True)
        return a["href"].strip() if a else ""
    except Exception:
        return ""
    

# ------------------------------
# Functions
# -----------------------------
def load_html(html_file, csv_file, column_mapping):
    """
    Load HTML file and extract table data based on column mapping.
    
    html_file: str -> path to HTML file
    csv_file: str -> path to output CSV
    column_mapping: dict -> {column_name: td_index_in_row}
    
    Notes:
    - Automatically handles pages with or without checkboxes/radios.
    - Special columns like 'Accepte/Refuse' or 'Match fait' are handled only if present.
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


    extracted = [] # This list will hold all the extracted match data

    # Loop through each row in the table
    for row in rows:
        cols = row.find_all('td') # Find all <td> elements in the row (table cells)
        if not cols:
            continue # skip empty rows or non-table rows

        row_data = {}

        # Extract columns based on mapping
        for col_name, idx in column_mapping.items():
            if "lien" in col_name.lower() or "link" in col_name.lower():
                row_data[col_name] = _td_link_safe(cols, idx)
            else:
                row_data[col_name] = _td_text_safe(cols, idx)
        # print(f"row_data = {row_data}")

        # ------------------ Section only for page 'Mes Assignations': BEGIN --------------------------------
        # Go through row and check if radio buttons or checkboxes exists
        radio_buttons = row.find_all('input', {'type': 'radio'}) # Check if row contains radio buttons
        checkboxes = row.find_all('input', {'type': 'checkbox'}) # Check if row contains checkbox
        if radio_buttons or checkboxes:

            if radio_buttons:
                # If radio buttons exist, find the checked one
                for radio in radio_buttons:
                    radio_button_name = radio.attrs.get('name', '')
                    if 'isgameaccepted' in radio_button_name and 'checked' in radio.attrs:
                        value = radio.attrs.get('value')
                        if value == '1':
                            row_data['Accepté/Refusé'] = 'Accepté'
                        elif value == '2':
                            row_data['Accepté/Refusé'] = 'Refusé'
                        # print(f"..................radio_button_name = {radio_button_name};row_data = {row_data}")

            
            checkbox_value = ""
            match_done = "no"
            if checkboxes:
                for checkbox in checkboxes:
                    checkbox_name = checkbox.attrs.get('name', '')
                    # print(f"..................checkbox_name = {checkbox_name}")
                    if 'isgamedone' in checkbox_name and not 'isgamedonealone' in checkbox_name:
                        checkbox_value = checkbox.attrs.get('value', '')
                        # print(f"..................checkbox_value = {checkbox_value}")
                        if checkbox.has_attr('checked'):
                            match_done = "yes"
                            row_data['Match fait'] = match_done
                    row_data['Match fait'] = match_done
                    # print(f"..................match_done = {match_done}")

            # print(f"row_data = {row_data}")
            # --- FILTER CONDITION : only include rows to data list where match is accepted AND not done yet
            match_accepted_or_refused = list(row_data.values())[9] # said if match has been accepted or refused
            match_completed = list(row_data.values())[10] # said if match has been played or not
            # print(f"........XXXXXX..........match_accepted_or_refused = {match_accepted_or_refused}; match_completed = {match_completed}; row_data.values() = {row_data.values()}")
            if match_accepted_or_refused == 'Accepté' and match_completed == 'no':
            # if  accepte_refuse == 'Accepté' and match_done_checked == 'no' :
                extracted.append(row_data)
            
            # ------------------ Section only for page 'Mes Assignations': END ----------------------------------

        else:
            # still append data even if there is no radio buttons and no checkboxes present in table 
            extracted.append(row_data)
    
    
    # print(f"HERE=========================================")
    # print(f"extracted: {extracted}")


    # Once looped through table and data extracted, save result to CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        headers = list(column_mapping.keys())
        writer.writerow(headers) # Write header
        for row in extracted:
            writer.writerow([row.get(h, "") for h in headers])  # Write values in header order
    print(f"Extraction complete: {len(extracted)} rows written to '{csv_file}'.")


    

