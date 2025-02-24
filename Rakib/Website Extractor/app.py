from flask import Flask, request, render_template, jsonify, session
from flask_session import Session
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import unquote
import json
import pandas as pd
import os
import logging
from datetime import timedelta

app = Flask(__name__)

# Set the secret key using environment variables for production
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")  # Use an environment variable for secret key
app.config["SESSION_TYPE"] = "filesystem"
app.config["DEBUG"] = False  # Disable debugging in production
app.config["ENV"] = "production"
app.config["SESSION_COOKIE_SECURE"] = True  # Use secure cookies for production (requires HTTPS)

# Set session to expire immediately after browser is closed
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=1)  # Forces session to expire immediately
app.permanent_session_lifetime = timedelta(seconds=1)

# Initialize session
Session(app)

# Set up logging for production
logging.basicConfig(level=logging.INFO)

# Predefined list of valid passwords
user_passwords = ["pass1", "pass2", "pass3"]

# Index route (home page)
@app.route('/')
def index():
    if session.get("authenticated"):
        return render_template('index.html')
    return render_template('password.html')  # Redirect to password input page

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data.get("password") in user_passwords:
        session["authenticated"] = True
        session.permanent = True  # Make the session permanent so it won't expire during the current session
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid password"}), 401

# Logout route
@app.route('/logout')
def logout():
    session.pop("authenticated", None)
    return jsonify({"success": True, "message": "Logged out successfully"})

# Keywords and blacklist for email and social media extraction
CONTACT_KEYWORDS = ['contact', 'contact-us', 'contacts']
BLACKLIST_EMAILS = [
    "@godaddy", ", ", ".png", ".jpg", "@example", "domain", "jane.doe@", "jdoe@", "john.doe", 
    "first@", "last@", ".svg", ".webp", "sentry", "company", ".jped", "?", "%", "(", ")", "<", 
    ">", ";", ":", "[", "]", "{", "}", "\\", "|", '"', "'", "!", "#", "$", "^", "&", "*"
]

EMAIL_REGEX = re.compile(r'([a-zA-Z0-9._%+-]+@[a-zAZ0-9.-]+\.[a-zA-Z]{2,})')

SOCIAL_MEDIA_PATTERNS = {
    "instagram": r'https?://(?:www\.)?instagram\.com/@?[\w.-]+',
    "facebook": r'https?://(?:www\.)?facebook\.com/(?!tr\?id=)[\w.-]+',
    "youtube": r'https?://(?:www\.)?youtube\.com/(?:@[\w.-]+|channel/[\w-]+|user/[\w.-]+|c/[\w.-]+)', 
    "linkedin": r'https?://(?:www\.)?linkedin\.com/(?:in|company|edu|school)/[\w.-]+(?:\?[^\s]+)?',
    "twitter": r'https?://(?:www\.)?(?:twitter\.com|x\.com)/@?[\w.-]+',
    "tiktok": r'https?://(?:www\.)?tiktok\.com/@[\w.-]+'
}

BLACKLIST_SOCIAL_MEDIA = {
    "facebook": ['/plugins', '/embed', 'facebook.com/tr?id=', '/2008', '/business', '/people'],
    "instagram": ['/explore/', 'instagram.com/p/', 'instagram.com/stories/', 'instagram.com/accounts/'],
    "twitter": ['/search', 'twitter.com/explore', 'twitter.com/i/', '/intent'],
    "linkedin": ['/jobs'],
    "youtube": ['/shorts', '/music'],
    "tiktok": ['/video/', '/discover', 'tiktok.com/hashtag/']
}

# Helper function to format phone numbers
def format_phone_number(phone):
    digits = re.sub(r'\D', '', phone)  # Remove all non-numeric characters
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]  # Remove leading '1'
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"  # Format as (000) 000-0000
    return phone  # Return the phone number as is if it doesn't meet the criteria

# Helper function to extract phone numbers
def extract_phone_from_soup(soup):
    phone_links = set()
    for element in soup.find_all(href=True):
        href = element['href']
        if href.startswith("tel:"):
            phone = href[4:].strip()
            phone = unquote(phone).replace("%20", " ")  # Decode URL encoding & replace %20 with space
            formatted_phone = format_phone_number(phone)
            digits_only = re.sub(r'\D', '', formatted_phone)  # Remove all non-numeric characters
            if len(digits_only) >= 5:
                phone_links.add(formatted_phone)
    return phone_links

# Helper function to extract email addresses
def extract_email_from_soup(soup):
    email_links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("mailto:"):
            email = href[7:].strip()
            if not any(black in email for black in BLACKLIST_EMAILS):
                email_links.add(email)
    text = soup.get_text(" ", strip=True)
    matches = EMAIL_REGEX.findall(text)
    for match in matches:
        if not any(black in match for black in BLACKLIST_EMAILS):
            email_links.add(match)
    return email_links

# Helper function to extract social media links
def extract_social_media_links(soup):
    social_media_links = {
        "instagram": set(),
        "facebook": set(),
        "youtube": set(),
        "linkedin": set(),
        "twitter": set(),
        "tiktok": set()
    }
    for platform, pattern in SOCIAL_MEDIA_PATTERNS.items():
        for match in re.findall(pattern, str(soup)):
            if any(black in match for black in BLACKLIST_SOCIAL_MEDIA.get(platform, [])):
                continue
            social_media_links[platform].add(match)
    return social_media_links

# Function to extract phone, email, and social media info from a URL
def extract_phone_and_email(url):
    print(f"Extracting phone and email from: {url}")

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
        return {"website": url, "phone": "", "email": "", "social_media": {}}

    page_source = response.text
    soup = BeautifulSoup(page_source, 'html.parser')

    phone_links = extract_phone_from_soup(soup)
    email_links = extract_email_from_soup(soup)
    social_media_links = extract_social_media_links(soup)

    extracted_data = {
        "website": url,
        "phone": ", ".join(sorted(phone_links)),
        "email": ", ".join(sorted(email_links)),
        "social_media": {platform: ", ".join(sorted(list(links))) for platform, links in social_media_links.items()}
    }

    return extracted_data

# Route to extract data from a given URL
@app.route('/extract', methods=['POST'])
def extract():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    data = extract_phone_and_email(url)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=False)
