from flask import Flask, request, render_template, jsonify
import requests
import re
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

def extract_emails_from_page(url):
    """Helper function to extract emails from a given URL."""
    response = requests.get(url)
    page_content = response.text
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_content)
    
    # Filter out unwanted emails
    blacklist = ['.png', '.jpg', 'example', 'email@', 'domain', 'jane.doe@', 'jdoe@', 'john.doe', 'first@', 'last@', ".svg", ".webp"]
    filtered_emails = [email for email in emails if not any(black.lower() in email.lower() for black in blacklist)]
    
    return filtered_emails

def extract_data(url):
    print(f"Extracting data from: {url}")  # Debugging

    # Get the raw HTML of the page
    response = requests.get(url)
    page_source = response.text

    soup = BeautifulSoup(page_source, 'html.parser')

    # Extract JSON-LD data (structured data)
    json_ld_data = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            json_data = json.loads(script.string)
            if isinstance(json_data, list):
                json_ld_data.extend(json_data)
            else:
                json_ld_data.append(json_data)
        except (json.JSONDecodeError, TypeError):
            continue

    # Extract social media profiles from JSON-LD
    json_social_links = []
    for item in json_ld_data:
        if isinstance(item, dict) and "sameAs" in item:
            json_social_links.extend(item.get("sameAs", []))

    # Extract all visible text and attribute values
    all_text = soup.get_text(separator=' ', strip=True)
    attribute_texts = ' '.join(attr for tag in soup.find_all() for attr in tag.attrs.values() if isinstance(attr, str))

    # Combine all extracted text sources
    combined_text = f"{all_text} {attribute_texts} {' '.join(json_social_links)}"

    # Extract social media profiles
    social_media_patterns = {
        "instagram": r'https?://(?:www\.)?instagram\.com/@?[\w.-]+',
        "facebook": r'https?://(?:www\.)?facebook\.com/(?!tr\?id=)[\w.-]+',
        "youtube": r'https?://(?:www\.)?youtube\.com/@?[\w.-]+',
        "linkedin": r'https?://(?:[a-zA-Z]{2,3}\.)?linkedin\.com/(?:in|company)/[\w.-]+',
        "twitter": r'https?://(?:www\.)?twitter\.com/@?[\w.-]+',
        "tiktok": r'https?://(?:www\.)?tiktok\.com/@[\w.-]+'
    }
    
    # Extract social media profiles and make them unique by converting to sets
    social_data = {platform: ", ".join(sorted(set(re.findall(pattern, combined_text)))) for platform, pattern in social_media_patterns.items()}

    # Extract and filter email addresses
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined_text)))
    blacklist = ['.png', '.jpg', 'example', 'email@', 'domain', 'jane.doe@', 'jdoe@', 'john.doe', 'first@', 'last@', ".svg", ".webp"]
    filtered_emails = [email for email in emails if not any(black.lower() in email.lower() for black in blacklist)]

    # If no email is found, check contact pages
    if not filtered_emails:
        contact_pages = ["/contact-us", "/contact"]
        for page in contact_pages:
            contact_url = url.rstrip('/') + page
            print(f"Checking contact page: {contact_url}")
            contact_emails = extract_emails_from_page(contact_url)
            if contact_emails:
                filtered_emails = contact_emails
                break

    extracted_data = {
        "website": url,
        "email": ", ".join(sorted(set(filtered_emails))),
        **social_data
    }

    print("Extracted Data:", extracted_data)  # Debugging output
    return extracted_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    data = extract_data(url)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
