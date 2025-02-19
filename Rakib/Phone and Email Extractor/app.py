from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

app = Flask(__name__)

# List of keywords to search for in contact-related URLs
CONTACT_KEYWORDS = ['contact', 'contact-us', 'contacts']

# Blacklist for email and phone numbers
blacklist_emails = ['.png', '.jpg', '@example', 'domain', 'jane.doe@', 'jdoe@', 'john.doe', 'first@', 'last@', ".svg", ".webp", "sentry", "company", ".jped"]
blacklist_phone = ['/plugins', '/embed', 'phone.com/tr?id=', '/2008']

# Regex pattern to match phone numbers (e.g., 416-979-5000, (416) 979-5000, +1 416 979 5000, etc.)
PHONE_REGEX = re.compile(
    r'(\+?\d{1,2}\s*[\-\.\s]?)?'        # Country code (optional)
    r'(\(?\d{3}\)?[\s\-\.\)]*)'          # Area code with optional parentheses
    r'(\d{3}[\s\-\.\)]*\d{4})'           # Local number
)

# Regex pattern to match emails
EMAIL_REGEX = re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

def extract_phone_from_soup(soup):
    """Extract phone numbers from <a href="tel:..."> links within a BeautifulSoup-parsed page."""
    phone_links = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("tel:"):
            # Remove the 'tel:' prefix and any whitespace/newline characters
            phone = href[4:].replace(" ", "").replace("\n", "")
            phone_links.add(phone)
    
    return phone_links

def extract_email_from_soup(soup):
    """Extract emails from mailto links and text using regex."""
    email_links = set()
    
    # Extract emails from <a href="mailto:..."> links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("mailto:"):
            email = href[7:].strip()
            email_links.add(email)
    
    # Extract emails from visible text
    text = soup.get_text(" ", strip=True)
    matches = EMAIL_REGEX.findall(text)
    for match in matches:
        email_links.add(match)
    
    return email_links

def extract_phone_and_email(url):
    print(f"Extracting phone and email from: {url}")  # Debugging

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.93 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {"website": url, "phone": "", "email": ""}

    page_source = response.text
    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract phone numbers and emails
    phone_links = extract_phone_from_soup(soup)
    email_links = extract_email_from_soup(soup)

    # Filter out blacklisted emails
    email_links = {email for email in email_links if not any(black in email for black in blacklist_emails)}

    # Filter out blacklisted phone numbers
    phone_links = {link for link in phone_links if not any(black in link for black in blacklist_phone)}

    # If no phone numbers or emails found on the main page, check contact pages
    if not phone_links or not email_links:
        print("No phone numbers or emails found on main page; checking contact pages...")
        contact_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if any(keyword in href for keyword in CONTACT_KEYWORDS):
                full_url = urljoin(url, a['href'])
                contact_links.add(full_url)

        for contact_url in contact_links:
            try:
                print(f"Checking contact page: {contact_url}")
                contact_resp = requests.get(contact_url, headers=headers, timeout=10)
                contact_soup = BeautifulSoup(contact_resp.text, 'html.parser')
                contact_phones = extract_phone_from_soup(contact_soup)
                contact_emails = extract_email_from_soup(contact_soup)

                # Combine phone numbers and emails from contact pages
                phone_links = phone_links.union(contact_phones)
                email_links = email_links.union(contact_emails)
            except Exception as e:
                print(f"Error fetching contact page {contact_url}: {e}")
                continue

    # Final extracted data, excluding blacklisted emails and phones
    extracted_data = {
        "website": url,
        "phone": ", ".join(sorted(phone_links)),
        "email": ", ".join(sorted(email_links))
    }

    print("Extracted Data:", extracted_data)
    return extracted_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    data = extract_phone_and_email(url)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
