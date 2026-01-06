<!-- markdownlint-disable -->

# Project Name: Basketball_calendar

## Description
Basketball_calendar is a Python application designed to generate a calendar file (`.ics`) for basketball matches that have been accepted by a referee on the official basketball association website.

The generated calendar can be imported into **Google Calendar** or **Apple Calendar**, allowing referees to automatically keep track of all their assigned matches with the necessary details (date, time, location, etc.), without manual entry.

This project aims to simplify match scheduling and reduce the risk of missed or incorrectly recorded games.

---

## Table of Contents
- [Project Name: Basketball\_calendar](#project-name-basketball_calendar)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Step 0: Setup your cookies.json](#step-0-setup-your-cookiesjson)
    - [Step 1: Run the main script](#step-1-run-the-main-script)
  - [Project Structure](#project-structure)
  - [Requirements](#requirements)
  - [Contributing](#contributing)
  - [License](#license)

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/basketball_calendar.git
```

2. Navigate into the project directory:
```bash
cd basketball_calendar
```

3. (Optional but recommended) Create a virtual environment:
```bash
python -m venv venv
```

4. Activate the virtual environment:

- **Windows**
```bash
venv\Scripts\activate
```

- **macOS / Linux**
```bash
source venv/bin/activate
```

5. Install the required dependencies:
```bash
pip install -r requirements.txt
```

---

## Usage

### Step 0: Setup your cookies.json

Before running the script, you need to provide a `cookies.json` file containing your login cookies from the official basketball website.

1. Go to [https://aabrq.ca/](https://aabrq.ca/) and log in with your credentials.
2. Install the browser extension **EditThisCookie (V3)** (only needs to be done once).
3. Click on the extension icon, then click **Export** to copy your cookies.
4. In Visual Studio Code, navigate to the `data/` folder in the project.
5. Create a file named `cookies.json` and paste the exported value from the extension.

> ⚠️ Make sure `cookies.json` is **kept private**. It is ignored by Git and should **never be pushed to GitHub**.

---

### Step 1: Run the main script

Run the main script to generate the calendar file:
```bash
python src/create_calendar.py
```

After execution:
- An `.ics` calendar file will be generated
- Import the file into:
  - **Google Calendar**: Settings → Import
  - **Apple Calendar**: File → Import

> ⚠️ **Security note**  
> `cookies.json` contains authentication data exported from your browser and should **never be committed** to version control.  
> Add it to `.gitignore`.

All generated files (HTML, CSV, and `.ics`) are written to the `output/` directory.

---

## Project Structure

```
basketball_calendar/
│
├── src/
│   ├── __init__.py                 # empty, just to make `src` a Python package
│   ├── create_calendar.py          # main script
│   ├── import_data.py              # fetches protected HTML pages
│   └── extract_necessary_data.py   # parses HTML into CSV files
│
├── data/                           # user-provided input
│   ├── .gitkeep                    # Git tracks this, folder exists
│   └── cookies.json
│
├── output/                         # auto-generated HTML, CSV, ICS
│   ├── matches_response.html
│   ├── addresses_response.html
│   ├── referees_response.html
│   ├── matches.csv
│   ├── addresses.csv
│   ├── referees.csv
│   └── matches_calendar.ics
│
└── tests/
│   ├── sample_data_addresses_special_test_cases.csv
│   ├── sample_data_matches.csv
│   └── test.py
│
├── requirements.txt
├── README.md
└── LICENSE

```

---

## Requirements
- Python 3.9 or higher
- Third-party Python packages:
  - requests
  - beautifulsoup4
  - ics

Install dependencies with:

```bash
pip install -r requirements.txt
```
---

## Contributing
Contributions are welcome.

To contribute:
1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

---

## License
This project is licensed under the MIT License.
