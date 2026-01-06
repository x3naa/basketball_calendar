"""
This script loads exported cookies from a web browser, 
uses them to fetch a protected basketball page,
and stores the HTTP response.

INPUT:
    - cookies: obtained from website once user has logged in and pasted in json file
    - domain: basketball website
    - url: specific page from basketball website
    - html_file: name of html file to be saved with page response


OUTPUT: 
    - html file containing page response

"""
# ------------------------------
# IMPORTS
# ------------------------------
import json         # STANDARD: Read and parse JSON files (cookies.json)
import os           # STANDARD: File paths, existence checks, OS interaction
import requests     # THIRD-PARTY: Send HTTP requests (GET/POST) to websites
import datetime     # STANDARD: Handle dates and times (cookie expiration)

# ------------------------------
# CONSTANTS
# ------------------------------


# ------------------------------
# Functions
# -----------------------------

def load_cookies(cookies_json, domain):
    """Load cookies from JSON and convert to a dictionary usable by requests (with error handling)"""
    # Check if the json file exists
    if not os.path.exists(cookies_json):
        print(f"\nERROR: '{cookies_json}' not found in the current directory.")
        print("Please export your cookies as JSON from your browser and save them as 'cookies.json'.")
        exit(1)
    else:
        print(f"\nSUCCESS: '{cookies_json}' found in the current directory.")

    # Try to open and parse the JSON file
    try:
        with open(cookies_json, "r", encoding="utf-8") as f:
            raw = json.load(f)

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to read '{cookies_json}'. The file is not valid JSON.")
        print("Please make sure you exported the cookies correctly.")
        print("Details:", e)
        exit(1)

    except Exception as e:
        print(f"Unexpected error while loading '{cookies_json}':", e)
        exit(1)

    # Check if the data retrieved from JSON is empty
    if not raw:
        print("WARNING: No cookies found in the JSON file.")
        print("You may need to log in again and re-export your cookies.")
        exit(1)


    # Convert list of cookies → dictionary for requests
    cookies = {}
    for c in raw:
        # Make sure it's a dict representing a cookie
        if isinstance(c, dict):
            # Only keep cookies for our domain
            if domain in c.get("domain", ""):
                cookies[c["name"]] = c["value"]
                # Let user know when cookies will expire if present
                if "expirationDate" in c: 
                    exp_timestamp_utc = datetime.datetime.fromtimestamp(c["expirationDate"], tz=datetime.timezone.utc)
                    print(f"Cookie expires at: {exp_timestamp_utc}")
                else:
                    print(f"Cookie is a session cookie")

    print(f"Loaded {len(cookies)} cookies for {domain}")
    return cookies



def fetch_page(cookies, url):
    """Request the basketball page using the provided cookies."""
    print("Fetching page...")
    try:
        resp = requests.get(url, cookies=cookies, timeout=10)
        print("Status code:", resp.status_code) # Print the HTTP status code (e.g., 200, 404, 500)
        return resp
    except Exception as e:
        print("Request failed:", e)
        exit(1)



def cookies_are_valid(html):
    """Check if the returned HTML contains the login page."""
    html_lower = html.lower()   # convert the entire HTML to lowercase
    login_keywords = ["se connecter", "mot de passe", "identifiant"] #list of words that normally appear on the login page
    found_login_keyword = False # assume cookies are valid unless we find a login keyword

    # look for each keyword in the HTML
    for word in login_keywords:
        if word.lower() in html_lower:
            found_login_keyword = True # If any word is found, cookies are invalid
            # print(f"keyword: {word.lower()}; found: found_login_keyword")
            break  # No need to continue checking

    # If login keywords were found → cookies invalid → return False
    if found_login_keyword:
        return False
    else:
        return True

def load_and_import_data(cookies, domain, url, html_file):
    
    cookies = load_cookies(cookies, domain)
    response = fetch_page(cookies, url)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"Response saved to '{html_file}'")

    if cookies_are_valid(response.text):
        print("SUCCESS: Cookies are valid! You are logged in.")
    else:
        print("ERROR: Cookies expired or invalid - export new cookies.json from browser")
        exit(1)


