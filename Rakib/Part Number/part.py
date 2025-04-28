import pandas as pd
import re

def load_excluded_parts(file_path):
    try:
        with open(file_path, 'r') as file:
            excluded_parts = set(line.strip() for line in file)
        return excluded_parts
    except FileNotFoundError:
        print(f"Warning: {file_path} not found. No parts will be excluded.")
        return set()

def extract_part_number(description, excluded_parts):
    lines = description.split("\n")  # Split by lines
    extracted_part = None
    new_description = []
    
    for line in lines:
        match = re.search(r'(?i)\bpart\s*#\s*:?\s*(.+)', line)
        if match:
            part_number = match.group(1).strip()
            if part_number and part_number not in excluded_parts:
                extracted_part = part_number
                continue  # Skip adding this line to new description
        new_description.append(line)
    
    return extracted_part, "\n".join(new_description)

def process_excel(file_path, output_path, exclude_file):
    df = pd.read_excel(file_path)
    excluded_parts = load_excluded_parts(exclude_file)
    
    extracted_parts = []
    new_descriptions = []
    
    for desc in df['Description']:
        part_number, new_desc = extract_part_number(str(desc), excluded_parts)
        extracted_parts.append(part_number)
        new_descriptions.append(new_desc)
    
    df['Part Number'] = extracted_parts
    df['Description'] = new_descriptions
    
    df.to_excel(output_path, index=False)
    print(f"Processed file saved as {output_path}")

# Example Usage
input_file = "input.xlsx"  # Replace with your input file name
output_file = "output.xlsx"  # Replace with your output file name
exclude_file = "exclude_parts.txt"  # File containing parts to exclude
process_excel(input_file, output_file, exclude_file)
