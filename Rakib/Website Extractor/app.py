from flask import Flask, request, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, unquote

app = Flask(__name__)

# List of keywords to search for in contact-related URLs
CONTACT_KEYWORDS = ['contact', 'contact-us', 'contacts']

# Blacklist for email
blacklist_emails = [", ", ".png", ".jpg", "@example", "domain", "jane.doe@", "jdoe@", "john.doe", "first@", "last@", ".svg", ".webp", "sentry", "company", ".jped", "?", "%", "(", ")", "<", ">", ";", ":", "[", "]", "{", "}", "\\", "|", '"', "'", "!", "#", "$", "^", "&", "*" ]
# Regex pattern to match emails
EMAIL_REGEX = re.compile(r'([a-zA-Z0-9._%+-]+@[a-zAZ0-9.-]+\.[a-zA-Z]{2,})')

def format_phone_number(phone):
    """Format phone numbers based on the given rules."""
    digits = re.sub(r'\D', '', phone)  # Remove all non-numeric characters
    
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]  # Remove leading '1'
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"  # Format as (000) 000-0000
    
    return phone  # Return the phone number as is if it doesn't meet the criteria

def extract_phone_from_soup(soup):
    """Extract phone numbers from any href="tel:..." and format them properly."""
    phone_links = set()

    # Extract phone numbers from any href="tel:..." occurrences
    for element in soup.find_all(href=True):
        href = element['href']
        if href.startswith("tel:"):
            # Extract the phone number, decode URL encoding, and replace %20 with a space
            phone = href[4:].strip()
            phone = unquote(phone).replace("%20", " ")  # Decode URL encoding & replace %20 with space
            
            # Format the phone number based on the given rules
            formatted_phone = format_phone_number(phone)
            
            # Check if the phone number has at least 5 digits
            digits_only = re.sub(r'\D', '', formatted_phone)  # Remove all non-numeric characters
            if len(digits_only) >= 5:
                phone_links.add(formatted_phone)

    return phone_links

def extract_email_from_soup(soup):
    """Extract emails from mailto links and text using regex."""
    email_links = set()

    # Extract emails from <a href="mailto:..."> links
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("mailto:"):
            email = href[7:].strip()
            if not any(black in email for black in blacklist_emails):  # Apply blacklist filter here
                email_links.add(email)

    # Extract emails from visible text using regex
    text = soup.get_text(" ", strip=True)
    matches = EMAIL_REGEX.findall(text)
    for match in matches:
        if not any(black in match for black in blacklist_emails):  # Apply blacklist filter here
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

    # Final extracted data, excluding blacklisted emails
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
