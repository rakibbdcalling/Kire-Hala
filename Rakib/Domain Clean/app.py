from flask import Flask, render_template, request
import re

app = Flask(__name__)

# Function to process URLs based on the button clicked
def modify_urls(urls, action):
    modified_urls = []
    
    # Function to clean the URL by removing anything after the domain extension
    def clean_url(url):
        # Remove the protocol (http://, https://) and www.
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        
        # Use regex to remove everything after the domain extension
        match = re.match(r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', url)
        if match:
            return match.group(0)  # Return the domain part only
        return None  # Return None for invalid domains

    # Clean domains per line and apply actions only for valid URLs
    for url in urls:
        cleaned_url = url.strip()
        
        if cleaned_url:  # Only clean if there's a non-empty line
            cleaned_url = clean_url(cleaned_url)
            if cleaned_url is None:  # If the line doesn't contain a valid domain, keep it unchanged
                modified_urls.append(url.strip())
                continue
        
        # Apply the appropriate action after cleaning the domain
        if action == "add_https":
            if cleaned_url and not cleaned_url.startswith("https://"):
                cleaned_url = "https://" + cleaned_url
        elif action == "add_http":
            if cleaned_url and not cleaned_url.startswith("http://"):
                cleaned_url = "http://" + cleaned_url
        elif action == "add_https_www":
            if cleaned_url and not cleaned_url.startswith("https://www."):
                cleaned_url = "https://www." + cleaned_url
        elif action == "add_http_www":
            if cleaned_url and not cleaned_url.startswith("http://www."):
                cleaned_url = "http://www." + cleaned_url
        # If the action is "add https", "add http", "add https://www", "add http://www", ensure the URL ends with a slash
        if action in ["add_https", "add_http", "add_https_www", "add_http_www"]:
            if cleaned_url and not cleaned_url.endswith("/"):
                cleaned_url = cleaned_url + "/"
        
        # If action is "clean", no other changes are made, just add the cleaned domain
        if cleaned_url:
            modified_urls.append(cleaned_url)
        else:
            modified_urls.append(url.strip())  # Keep empty lines unchanged
    
    return modified_urls

@app.route("/", methods=["GET", "POST"])
def index():
    result = []
    if request.method == "POST":
        # Get the URLs and action from the form
        urls = request.form["urls"].split("\n")
        action = request.form["action"]
        
        # Modify URLs based on action
        result = modify_urls(urls, action)
    
    # Ensure the input box retains its value after submission
    input_urls = request.form.get("urls", "")
    
    return render_template("index.html", result="\n".join(result), input_urls=input_urls)

if __name__ == "__main__":
    app.run(debug=True)
