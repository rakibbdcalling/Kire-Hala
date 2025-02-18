from flask import Flask, request, render_template, jsonify
import requests
import re
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# Helper function to extract emails from a given URL
def extract_emails_from_page(url):
    response = requests.get(url)
    page_content = response.text
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_content)
    
    # Filter out unwanted emails
    blacklist_emails = ['.png', '.jpg', 'example', 'email@', 'domain', 'jane.doe@', 'jdoe@', 'john.doe', 'first@', 'last@', ".svg", ".webp"]
    filtered_emails = [email for email in emails if not any(black.lower() in email.lower() for black in blacklist_emails)]
    
    return filtered_emails

# Extract data function to get emails and social media profiles
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

    # Social media profile patterns
    social_media_patterns = {
        "instagram": r'https?://(?:www\.)?instagram\.com/@?[\w.-]+',
        "facebook": r'https?://(?:www\.)?facebook\.com/(?!tr\?id=)[\w.-]+',
        "youtube": r'https?://(?:www\.)?youtube\.com/(?:@[\w.-]+|channel/[\w-]+|user/[\w.-]+|c/[\w.-]+)',  # Added 'c/' for custom URLs
        "linkedin": r'https?://(?:www\.)?linkedin\.com/(?:in|company|edu|school)/[\w.-]+(?:\?[^\s]+)?',
        "twitter": r'https?://(?:www\.)?(?:twitter\.com|x\.com)/@?[\w.-]+',
        "tiktok": r'https?://(?:www\.)?tiktok\.com/@[\w.-]+'
    }

    # Blacklist for social media links to exclude unnecessary URLs
    blacklist_emails = ['.png', '.jpg', 'example', 'email@', 'domain', 'jane.doe@', 'jdoe@', 'john.doe', 'first@', 'last@', ".svg", ".webp", "sentry", "company"]
    blacklist_facebook = ['/plugins', '/embed', 'facebook.com/tr?id=', '/2008']
    blacklist_instagram = ['/explore/', 'instagram.com/p/', 'instagram.com/stories/', 'instagram.com/accounts/']
    blacklist_twitter = ['/search', 'twitter.com/explore', 'twitter.com/i/', '/intent']
    blacklist_linkedin = ['/jobs']
    blacklist_youtube = ['/shorts', '/music']
    blacklist_tiktok = ['/video/', '/discover', 'tiktok.com/hashtag/']

    # Extract and filter social media profiles
    social_data = {}

    # For anchor tags <a> with 'social-link' class, specifically extract YouTube user URLs
    youtube_links_from_a_tags = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if 'youtube.com/c/' in href:  # Matching YouTube custom channel URLs
            youtube_links_from_a_tags.add(href)

    # Combine these with the general YouTube search (channel/ and @ username formats)
    found_links = set(re.findall(social_media_patterns["youtube"], combined_text)) | youtube_links_from_a_tags
    found_links = {link for link in found_links if not any(black in link for black in blacklist_youtube)}
    social_data['youtube'] = ", ".join(sorted(found_links))

    # Extract other social media links based on patterns
    for platform, pattern in social_media_patterns.items():
        if platform != "youtube":
            found_links = set(re.findall(pattern, combined_text))
            if platform == "facebook":
                found_links = {link for link in found_links if not any(black in link for black in blacklist_facebook)}
            elif platform == "instagram":
                found_links = {link for link in found_links if not any(black in link for black in blacklist_instagram)}
            elif platform == "twitter":
                found_links = {link for link in found_links if not any(black in link for black in blacklist_twitter)}
            elif platform == "linkedin":
                found_links = {link for link in found_links if not any(black in link for black in blacklist_linkedin)}
            elif platform == "tiktok":
                found_links = {link for link in found_links if not any(black in link for black in blacklist_tiktok)}
            social_data[platform] = ", ".join(sorted(found_links))

    # Extract and filter email addresses
    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined_text)))
    filtered_emails = [email for email in emails if not any(black.lower() in email.lower() for black in blacklist_emails)]

    # If no email is found, check contact pages
    if not filtered_emails:
        contact_pages = ["/contact-us", "/contact", "/contacts"]
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
