from bs4 import BeautifulSoup
import html
import pandas as pd
import re


# ============================================================
# CONFIG
# ============================================================

HTML_FILE = r"D:\SIH_EXTRACTOR\view-source_https___www.sih.gov.in_sih2026PS.html"
OUTPUT_FILE = r"D:\SIH_EXTRACTOR\SIH_2026_Hardware.xlsx"


# ============================================================
# 1. READ CHROME VIEW-SOURCE FILE
# ============================================================

with open(
    HTML_FILE,
    "r",
    encoding="utf-8",
    errors="replace"
) as f:
    chrome_html = f.read()

print("Chrome source loaded.")
print("File size:", len(chrome_html))


# ============================================================
# 2. RECONSTRUCT ORIGINAL HTML
# ============================================================

outer = BeautifulSoup(
    chrome_html,
    "html.parser"
)

source_lines = outer.select("td.line-content")

if not source_lines:
    print("ERROR: Chrome source lines not found.")
    raise SystemExit

original_html = "\n".join(
    line.get_text()
    for line in source_lines
)

original_html = html.unescape(original_html)

print("Original SIH HTML reconstructed.")


# ============================================================
# 3. PARSE ORIGINAL SIH HTML
# ============================================================

soup = BeautifulSoup(
    original_html,
    "html.parser"
)

print("HTML parsed.")


# ============================================================
# 4. FIND THE MAIN SIH TABLE
# ============================================================

tables = soup.find_all("table")

print("Tables found:", len(tables))

main_table = None

for table in tables:

    # Get text from first few rows
    table_text = table.get_text(
        " ",
        strip=True
    )

    # The main SIH table contains these distinctive labels
    required = [
        "S.No.",
        "Organization",
        "Problem Statement Title",
        "Category",
        "PS Number",
        "Theme"
    ]

    if all(
        item.lower() in table_text.lower()
        for item in required
    ):

        main_table = table
        break


if main_table is None:

    print("ERROR: SIH main table not found.")

    for i, table in enumerate(tables[:20]):

        text = table.get_text(
            " ",
            strip=True
        )

        print(
            f"Table {i}: {text[:200]}"
        )

    raise SystemExit


print("SIH main table FOUND!")


# ============================================================
# 5. GET MAIN TABLE ROWS
# ============================================================

rows = main_table.find_all("tr")

print("Total HTML rows:", len(rows))


# ============================================================
# 6. EXTRACT ONLY MAIN PROBLEM ROWS
# ============================================================

records = []


for row in rows:

    cells = row.find_all(
        "td",
        recursive=False
    )

    # Main rows have 8 columns
    if len(cells) != 8:
        continue


    # --------------------------------------------------------
    # Column 0 = S.No.
    # --------------------------------------------------------

    sno = cells[0].get_text(
        " ",
        strip=True
    )

    if not sno.isdigit():
        continue


    # --------------------------------------------------------
    # Extract visible table columns
    # --------------------------------------------------------

    organization = cells[1].get_text(
        " ",
        strip=True
    )

    title = cells[2].get_text(
        " ",
        strip=True
    )

    category = cells[3].get_text(
        " ",
        strip=True
    )

    ps_number = cells[4].get_text(
        " ",
        strip=True
    )

    submitted_ideas = cells[5].get_text(
        " ",
        strip=True
    )

    theme = cells[6].get_text(
        " ",
        strip=True
    )

    deadline = cells[7].get_text(
        " ",
        strip=True
    )


    # --------------------------------------------------------
    # Remove modal text from title
    # --------------------------------------------------------

    if "× Problem Statement Details" in title:

        title = title.split(
            "× Problem Statement Details"
        )[0].strip()


    # --------------------------------------------------------
    # Normalize PS number
    # --------------------------------------------------------

    if ps_number.isdigit():

        ps_number = "SIH" + ps_number


    # --------------------------------------------------------
    # Find detailed modal
    # --------------------------------------------------------

    ps_id = ps_number.replace(
        "SIH",
        ""
    )

    modal = soup.find(
        id=f"ViewProblemStatement{ps_id}"
    )


    description = ""
    department = ""
    modal_category = ""
    modal_theme = ""
    youtube = ""
    dataset = ""
    contact = ""

    modal_title = title
    modal_organization = organization


    # ========================================================
    # Extract modal fields
    # ========================================================

    if modal:

        detail_rows = modal.find_all("tr")

        for detail_row in detail_rows:

            cells2 = detail_row.find_all(
                ["th", "td"],
                recursive=False
            )

            if len(cells2) < 2:
                continue

            key = cells2[0].get_text(
                " ",
                strip=True
            )

            value = cells2[1].get_text(
                " ",
                strip=True
            )

            key_lower = key.lower()


            if key_lower == "problem statement title":

                modal_title = value


            elif key_lower == "description":

                description = value


            elif key_lower == "organization":

                modal_organization = value


            elif key_lower == "department":

                department = value


            elif key_lower == "category":

                modal_category = value


            elif key_lower == "theme":

                modal_theme = value


            elif key_lower == "youtube link":

                youtube = value


            elif key_lower == "dataset link":

                dataset = value


            elif key_lower == "contact info":

                contact = value


    # ========================================================
    # IMPORTANT:
    # Prefer the modal Category if it exists.
    # Otherwise use the main table category.
    # ========================================================

    final_category = (
        modal_category
        if modal_category
        else category
    )


    final_theme = (
        modal_theme
        if modal_theme
        else theme
    )


    final_title = (
        modal_title
        if modal_title
        else title
    )


    # ========================================================
    # Create record
    # ========================================================

    record = {

        "S.No.": int(sno),

        "PS Number": ps_number,

        "Problem Statement Title":
            final_title,

        "Organization":
            modal_organization,

        "Department":
            department,

        "Category":
            final_category,

        "Theme":
            final_theme,

        "Deadline":
            deadline,

        "Submitted Ideas":
            submitted_ideas,

        "Description":
            description,

        "YouTube Link":
            youtube,

        "Dataset Link":
            dataset,

        "Contact Info":
            contact
    }


    records.append(record)


# ============================================================
# 7. CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(records)


print()
print("=" * 60)
print("EXTRACTION RESULT")
print("=" * 60)

print(
    "Total projects extracted:",
    len(df)
)


# ============================================================
# 8. CLEAN CATEGORY
# ============================================================

df["Category"] = (
    df["Category"]
    .astype(str)
    .str.strip()
)


# Show categories for debugging
print()
print("Categories found:")

print(
    df["Category"]
    .value_counts()
)


# ============================================================
# 9. FILTER HARDWARE
# ============================================================

hardware = df[
    df["Category"]
    .str.casefold()
    .eq("hardware")
].copy()


software = df[
    df["Category"]
    .str.casefold()
    .eq("software")
].copy()


print()
print("Hardware projects:", len(hardware))
print("Software projects:", len(software))


# ============================================================
# 10. CLEAN EXCEL-INCOMPATIBLE CHARACTERS
# ============================================================

def clean_excel_text(value):

    if isinstance(value, str):

        value = re.sub(
            r"[\x00-\x08\x0B\x0C\x0E-\x1F]",
            "",
            value
        )

        return value[:32767]

    return value


df = df.map(clean_excel_text)
hardware = hardware.map(clean_excel_text)


# ============================================================
# 11. CREATE EXCEL
# ============================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    hardware.to_excel(
        writer,
        sheet_name="Hardware Projects",
        index=False
    )

    df.to_excel(
        writer,
        sheet_name="All Projects",
        index=False
    )

    summary = pd.DataFrame({

        "Metric": [

            "Total Projects",

            "Hardware Projects",

            "Software Projects",

            "Hardware Percentage"

        ],

        "Value": [

            len(df),

            len(hardware),

            len(software),

            f"{len(hardware) / len(df) * 100:.1f}%"

        ]

    })

    summary.to_excel(
        writer,
        sheet_name="Summary",
        index=False
    )


print()
print("=" * 60)
print("EXCEL CREATED")
print("=" * 60)

print(
    "Output:",
    OUTPUT_FILE
)

print(
    "Hardware projects:",
    len(hardware)
)