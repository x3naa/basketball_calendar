"""
This script uses extracted data to create an iCalendar (.ics) file.

Each match becomes a calendar event containing:
    - Title (Teams — League (Calibre))
    - Start time (Date + Heure)
    - End time (90 minutes after start)
    - Location (Terrain)
    - Description (match metadata)

The .ics file can be imported into:
    - Google Calendar
    - Apple Calendar (iPhone/macOS)
    - Microsoft Outlook
    - Android Calendar apps

Dependencies:
    pip install ics

INPUT: 
    - None

OUTPUT: 
    - .ics file
"""
# ------------------------------
# IMPORTS
# ------------------------------
import csv                                  # STANDARD: Read CSV input files
import os                                   # STANDARD: Path handling and file checks
from ics import Calendar, Event             # THIRD-PARTY: Create .ics calendar files
from datetime import datetime, timedelta    # STANDARD: Date/time arithmetic
from zoneinfo import ZoneInfo               # STANDARD (Python ≥3.9): Timezone support
import unicodedata                          # STANDARD: Unicode normalization (accents)
import re                                   # STANDARD: Regular expressions (text cleanup)

# customed functions
from import_data import load_and_import_data    # Local module: fetch HTML
from extract_necessary_data import load_html    # Local module: parse HTML → CSV

# ------------------------------
# CONSTANTS
# ------------------------------

COOKIES = "cookies.json" 

# Ensure output folder exists
os.makedirs("output", exist_ok=True)

# Directories
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "output")

COOKIES = os.path.join(DATA_DIR, "cookies.json") # Cookies upon loggin on website


# URL of pages
DOMAIN = "aabrq.ca"
URL_MATCHES = f"https://{DOMAIN}/arbitres/index.php?option=com_aabrq&view=assignmentlist&Itemid=78" # refer to page "Mes assignations"
URL_ADDRESSES = f"https://{DOMAIN}/arbitres/index.php?option=com_aabrq&view=schoollist&id=47&Itemid=54" # refer to page "Plans de route"
URL_REFEREES = f"https://{DOMAIN}/arbitres/index.php?option=com_aabrq&view=addressbook&Itemid=80" # refer to page "Bottin téléphonique"

# Generated HTML of page response
HTML_MATCHES = os.path.join(OUTPUT_DIR, "matches_response.html")
HTML_ADDRESSES = os.path.join(OUTPUT_DIR, "addresses_response.html")
HTML_REFEREES = os.path.join(OUTPUT_DIR, "referees_response.html")

# Generated CSV files
MATCHES_CSV = os.path.join(OUTPUT_DIR, "matches.csv")
ADDRESSES_CSV = os.path.join(OUTPUT_DIR, "addresses.csv")
REFEREES_CSV = os.path.join(OUTPUT_DIR, "referees.csv")

# Generated calendar file (.ics file)
ICS_FILE = os.path.join(OUTPUT_DIR, "matches_calendar.ics")

# Mappings of columns to be retrieved
COLUMN_MAP_ASSIGNATIONS = {
    '#': 0,
    'Ligue': 1,
    'Calibre': 2,
    'Jour': 4,
    'Date': 5,
    'Heure': 6,
    'Equipes': 7,
    'Terrain': 8,
    'Autre arbitre': 9,
    'Accepté/Refusé': 10,
    'Match fait': 11
}

COLUMN_MAP_ADDRESSES = {
    'School Name': 0,
    'Address': 1,
    'Map Link': 2
}

COLUMN_MAP_REFEREE = {
    'Numéro': 0,
    'Nom': 1,
    'Prénom': 2,
    'Ville': 3,
    'Téléphone 1': 4,
    'Téléphone 2': 5,
    'Courriel': 6
}


# Regex-based so we catch Sém, Sém., Sém., St, St-, etc.
ABBREVIATIONS = {
    r"\bs[eé]m\.?\b": "séminaire",
    r"\bst[\.]?\b": "saint",
    r"\bste[\.]?\b": "sainte",
    r"\bcoll\.?\b": "collège",
    r"\ble\b": "le",
    r"\bla\b": "la",
    r"\bcfp\b": "Centre de formation professionnel",
}

# New special-case rule
SPECIAL_CASES = [
    (r"\bLe\s+May\b", "Lemay"),
    (r"\bL\.-?J\.?\.?\s*Casault\b", "Louis-Jacques Casault"),
]

# ------------------------------
# Functions
# -----------------------------
def expand_abbreviations(text):
    """Replace known abbreviations with full words."""
    result = text
    for pattern, replacement in ABBREVIATIONS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result



def normalize(text):
    """Normalize for comparison: expand abbreviations, remove accents, punctuation, lowercase."""
    if not text:
        return ""
    # expand known abbreviations first
    # print(f"TEXT before normalization................text = {text}")
    text = expand_abbreviations(text)
    # print(f"TEXT after abbreviation................text = {text}")
    # apply special-case rules
    for pattern, replacement in SPECIAL_CASES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # remove accents
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    # lowercase
    text = text.lower()
    # remove parentheses and content in parentheses
    text = re.sub(r"\(.*?\)", "", text)
    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # collapse spaces
    # print(f"BEFORE STRIP................text normalized = {text}")
    text = re.sub(r"\s+", " ", text).strip()
    # print(f"AFTER STRIP................text normalized = {text}")
    # remove any spaces within text
    # text = text.replace(" ", "")
    # print(f"AFTER REPLACING SPACES WITHIN................text = {text}")
    return text



def load_addresses(file_path):
    """Load addresses from compiled address file
        Columns in file: 
            1. School Name - needed as link to file 'matches'
            2. Address - need to add in calendar
            3. Map Link - need to add in calendar as Google map link
    """
    addresses = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            school_name = row["School Name"].strip()
            addresses[school_name] = {
                "address": row["Address"].strip(),
                "map_link": row["Map Link"].strip()
            }
    return addresses



def load_referees(file_path):
    """Load referees from compiled referees file
        Columns in file:
        1. Numéro - needed as link to file 'matches'
        2. Nom - need to add in calendar
        3. Prénom - need to add in calendar
        4. Ville - not needed
        5. Téléphone 1 - need to add in calendar
        6. Téléphone 2 - need to add in calendar
        7. Courriel - need to add in calendar
    """
    referees = {}
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ref_id = row["Numéro"].strip()
            ref_name = f"{row['Nom'].strip()} {row['Prénom'].strip()}"
            referees[ref_id] = {
                "Nom": ref_name,
                "Téléphone 1": row["Téléphone 1"].strip(),
                "Téléphone 2": row["Téléphone 2"].strip(),
                "Courriel": row["Courriel"].strip()
            }
    return referees



def load_matches(file_path):
    """Load matches from compiled matches file
        Columns in file:
        1. # - not needed
        2. Ligue - need to add in calendar
        3. Calibre - need to add in calendar
        4. Jour - need to add in calendar
        5. Date - need to add in calendar
        6. Heure - need to add in calendar
        7. Equipes - need to add in calendar
        8. Terrain - needed as link to file 'addresses'
        9. Autre arbitre  - needed as link to file 'referees'
        10. Accepté/Refusé  - not needed
        11. Match fait  - not needed
    """
    matches = []
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            matches.append(row)
    return matches



def parse_datetime(date_str, time_str):
    """
    Convert the given date and time strings into a datetime object.
    Tries several known formats used by browsers or exported HTML pages.

    Parameters
    ----------
    date_str : str
        Date extracted from CSV (e.g., "2025-11-21")
    time_str : str
        Time extracted from CSV (e.g., "18:30")

    Returns
    -------
    datetime
        Combined datetime object
    """

    possible_formats = [
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y/%m/%d %H:%M",
        "%d.%m.%Y %H:%M",
    ]

    for fmt in possible_formats:
        try:
            return datetime.strptime(f"{date_str} {time_str}", fmt)
        except ValueError:
            pass

    raise ValueError(f"Unrecognized date/time format: '{date_str} {time_str}'")



def overlap_score(a, b):
    """
    Returns value between 0 and 1 based on shared words.
    """
    set_a = set(a.split())
    set_b = set(b.split())
    if not set_a or not set_b:
        return 0
    overlap = len(set_a & set_b)
    total = max(len(set_a), len(set_b))
    # print(f"set_a = {set_a}; set_b = {set_b}; overlap = {overlap}; total = {total}")
    return overlap / total




def find_address_for_terrain(terrain, addresses_dict):
    """
    Try to return best address + map link for a given terrain name.
    Uses normalization and partial substring match.
    """

    if not terrain:
        return None, None

    norm_terrain = normalize(terrain)
    # print(f"terrain = {terrain}; Normalised terrain: {norm_terrain}")
    best_score = 0
    best_entry = None
    
    for school_name, row in addresses_dict.items():
        norm_school = normalize(school_name)
        

        # direct substring either direction
        if norm_terrain in norm_school or norm_school in norm_terrain:
            return row["address"], row["map_link"]

        # compute simple overlap score
        score = overlap_score(norm_terrain, norm_school)
        # print(f"Normalised school name: {norm_school}; score = {score}")
        if score > best_score:
            best_score = score
            best_entry = row

    # pick match only if similarity high enough
    if best_score > 0.45:  # tweakable threshold
        return best_entry["address"], best_entry["map_link"]

    return None, None




def create_calendar(matches, addresses, referees):
    """
    Read match data from various csv files (matches, addresses, and referees) and generate a calendar event
    """
    calendar = Calendar()

    # open csv and extract details needed for calendar
    for row in matches:

        # Extract required fields
        ligue = row["Ligue"]
        calibre = row["Calibre"]
        jour = row["Jour"]
        date = row["Date"]
        heure = row["Heure"]
        equipes = row["Equipes"]
        school_name = row["Terrain"]
        referee_id = row["Autre arbitre"]

        # address_info = addresses.get(school_name, {"address": "Unknown", "map_link": ""}) # Lookup the school's address
        # address = address_info["address"]
        # map_link = address_info["map_link"]
        address, map_link = find_address_for_terrain(school_name, addresses)  # Lookup the school's address

        referee_name = referees.get(referee_id, "Unknown") # Lookup the referee's details

        title = f"Ligue: {ligue} - Calibre: {calibre}" # Build event title
        # print(f"date: {date}, heure: {heure}")
        if date != "" and heure != "":
            dt_start = parse_datetime(date, heure).replace(tzinfo=ZoneInfo("America/Toronto")) # Convert start datetime and ensure time is in correct timezone
            dt_end = dt_start + timedelta(minutes=90) # End time = 90 minutes after start
            # print(f"heure = {heure}; dt_start = {dt_start}; dt_end = {dt_end}")
        
            # Clean event description
            description = (
                f"Ligue: {ligue}\n"
                f"Calibre: {calibre}\n"
                f"Jour: {jour}\n"
                f"Date: {date}\n"
                f"Heure: {heure}\n"
                f"Équipes: {equipes}\n"
                f"Autre arbitre: {referee_name}\n"
                f"École: {school_name}\n"
                f"Addresse: {address}\n"
                f"\nGoogle Maps Link:\n{map_link}\n"
            )

            # Build calendar event
            event = Event()
            event.name = title
            event.begin = dt_start
            event.end = dt_end
            event.location = event.location = f"{school_name} - {address}\nGoogle Maps: {map_link}"
            event.description = description

            # Add event to calendar
            calendar.events.add(event)
    
    return calendar



# ------------------------------
# Main
# -----------------------------
def main():
    
    # Retrieve match details
    load_and_import_data(COOKIES, DOMAIN, URL_MATCHES, HTML_MATCHES) # load page "Mes assignations" which contains match details and save html response
    load_html(HTML_MATCHES, MATCHES_CSV, COLUMN_MAP_ASSIGNATIONS) # from html response, retrieve only necessary data and store them in a csv file

    # Retrieve addresses
    load_and_import_data(COOKIES, DOMAIN, URL_ADDRESSES, HTML_ADDRESSES) # load page "Plans de route" which contains location match details and save html response
    load_html(HTML_ADDRESSES, ADDRESSES_CSV, COLUMN_MAP_ADDRESSES) # from html response, retrieve only necessary data and store them in a csv file

    # Retrieve referees details
    load_and_import_data(COOKIES, DOMAIN, URL_REFEREES, HTML_REFEREES) # load page "Bottin téléphonique" which contains referees details and save html response
    load_html(HTML_REFEREES, REFEREES_CSV, COLUMN_MAP_REFEREE) # from html response, retrieve only necessary data and store them in a csv file

    # Load match, location and referee details from csv files into dictionaries 
    files_to_check = {MATCHES_CSV, ADDRESSES_CSV, REFEREES_CSV}
    for file in files_to_check:
        if not os.path.exists(file): # Check if CSV files exists
            print(f"ERROR: '{file}' not found.") 
            return
    print("\nAll necessary files exist. Can proceed.")
    # MATCHES_CSV =  'matches_test_copy.csv' #'matches_test.csv' # special test cases - to delete afterwards
    matches = load_matches(MATCHES_CSV)
    # ADDRESSES_CSV = 'addresses_special_test_cases_copy.csv' # 'addresses_special_test_cases.csv' # special test cases - to delete afterwards
    addresses = load_addresses(ADDRESSES_CSV)
    referees = load_referees(REFEREES_CSV)

    # Create calendar events based on the dictionaries created
    cal = create_calendar(matches, addresses, referees)

    # Combine all calendar events to a calendar file (.ics file)
    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.writelines(cal.serialize())
    print(f"\nSUCCESS: Calendar file '{ICS_FILE}' created successfully!")
    

if __name__ == "__main__":
    main()

