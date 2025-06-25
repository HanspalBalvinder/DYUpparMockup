import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
import html
import os

# === URL Generation and Checking ===
def generate_urls(base_url_pattern, start, end):
    return [base_url_pattern.format(i) for i in range(start, end + 1)]

def check_url_exists(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def find_existing_urls(base_url_pattern, start, end):
    urls = generate_urls(base_url_pattern, start, end)
    existing_urls = []
    for url in urls:
        if check_url_exists(url):
            print(f"✅ Exists: {url}")
            existing_urls.append(url)
        else:
            print(f"❌ Not found: {url}")
    return existing_urls

# === HTML Fetching ===
def fetch_and_save_html(url, filepath="siemens_jobs_page_source.html"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ Saved HTML to '{filepath}'")
        return True
    else:
        print(f"❌ Failed to fetch {url}: {response.status_code}")
        return False

# === Job Data Extraction ===
def extract_job_fields_with_regex(html_text):
    fields = {}

    def find(pattern):
        match = re.search(pattern, html_text)
        return match.group(1).strip() if match else ""

    fields["Title"] = find(r'"title"\s*:\s*"([^"]+)"')
    fields["Employment Type"] = find(r'"employmentType"\s*:\s*"([^"]+)"')
    fields["Date Posted"] = find(r'"datePosted"\s*:\s*"([^"]+)"')
    fields["Valid Through"] = find(r'"validThrough"\s*:\s*"([^"]+)"')
    fields["Location"] = find(r'"addressLocality"\s*:\s*"([^"]+)"')
    fields["Country"] = find(r'"addressCountry"\s*:\s*{[^}]*"name"\s*:\s*"([^"]+)"')
    fields["Organization"] = find(r'"hiringOrganization"\s*:\s*{[^}]*"name"\s*:\s*"([^"]+)"')
    fields["Job URL"] = find(r'"url"\s*:\s*"([^"]+)"')

    raw_description = find(r'"description"\s*:\s*"(.+?)"\s*,\s*"identifier"')
    clean_description = BeautifulSoup(html.unescape(raw_description), "html.parser").get_text(" ")
    fields["Description"] = clean_description.strip()

    return fields

def append_job_to_csv(html_filepath, csv_path="parsed_siemens_jobs.csv"):
    try:
        with open(html_filepath, "r", encoding="utf-8") as f:
            html_content = f.read()

        print("🔍 Parsing job from HTML...")
        job = extract_job_fields_with_regex(html_content)

        if job["Title"]:
            df_existing = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()
            df_new = pd.DataFrame([job])
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["Job URL"], inplace=True)
            df_combined.to_csv(csv_path, index=False)
            print(f"✅ Appended job: {job['Title']}")
        else:
            print("❌ Could not extract job title.")
    except Exception as e:
        print(f"❌ Error parsing job HTML: {e}")

# === Main Execution ===
if __name__ == "__main__":
    base_pattern = "https://jobs.siemens.com/careers?location=india&pid={}&domain=siemens.com&sort_by=relevance&triggerGoButton=true"
    existing_urls = find_existing_urls(base_pattern, 563156125652844, 563156125652847)

    for url in existing_urls:
        if fetch_and_save_html(url):
            append_job_to_csv("siemens_jobs_page_source.html")

#563156125641351,563156125653160,563156125653103,563156125650616,563156125652082