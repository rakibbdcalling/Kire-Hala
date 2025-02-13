import pandas as pd
import re

def format_title(title, brand, part_number):
    """
    Format the title using the criteria:
    Brand name + product type + motorcycle model or automobile model + year + part number.
    """
    if not isinstance(title, str):
        title = ""
    title = title.strip().upper()
    brand = brand.strip().upper() if pd.notna(brand) else ""
    part_number = str(part_number).strip().upper() if pd.notna(part_number) else ""
    
    # Remove duplicate brand name and part number
    if brand and brand in title:
        title = title.replace(brand, "").strip()
    if part_number and part_number in title:
        title = title.replace(part_number, "").strip()
    
    # Construct the new title
    formatted_title = f"{brand} {title}".strip()
    if part_number:
        formatted_title += f" {part_number}"
    
    return formatted_title.strip()

def format_description(description, brand, part_number):
    """
    Format the description with the specified formatting rules.
    """
    if not isinstance(description, str):
        description = ""
    
    lines = description.split('\n')
    if not lines:
        return ""
    
    # Convert part_number to string to prevent AttributeError
    part_number = str(part_number).strip().upper()
    brand = brand.strip().upper() if pd.notna(brand) else ""
    
    # Format the first line as a title following the same formatting rules as the main title
    first_line = lines[0].strip().upper()
    has_brand = brand and brand in first_line
    has_part_number = part_number and part_number in first_line
    
    formatted_title = first_line
    if has_brand:
        formatted_title = formatted_title.replace(brand, "").strip()
    if has_part_number:
        formatted_title = formatted_title.replace(part_number, "").strip()
    
    if has_brand:
        formatted_title = f"{brand} {formatted_title}".strip()
    if has_part_number:
        formatted_title += f" {part_number}".strip()
    
    # Ensure part number is always in the second line
    part_number_line = f"Part #: {part_number}" if part_number else "Part #:"
    
    # Remove extra spaces and add line breaks
    formatted_lines = [formatted_title, part_number_line]
    
    for line in lines[1:]:
        line = line.strip()
        if line and "FOR MORE INFO PLEASE CONTACT US" not in line.upper() and "--------------------" not in line:
            formatted_lines.append("\n" + line)
    
    # Add one breakline before the last paragraph
    if len(formatted_lines) > 2:
        formatted_lines[-1] = "\n" + formatted_lines[-1]
    
    return "\n".join(formatted_lines).strip() + "\n\n"

# Read Excel file
df = pd.read_excel("input.xlsx")
df.columns = df.columns.str.strip()  # Remove extra spaces from column names

# Ensure necessary columns exist
if "Part Number" not in df.columns:
    df["Part Number"] = ""
if "Brand" not in df.columns:
    df["Brand"] = ""
if "Title" not in df.columns:
    df["Title"] = ""
if "Description" not in df.columns:
    df["Description"] = ""

# Process each row
df["Formatted Title"] = df.apply(lambda row: format_title(row["Title"], row["Brand"], row["Part Number"]), axis=1)
df["Formatted Description"] = df.apply(lambda row: format_description(row["Description"], row["Brand"], row["Part Number"]), axis=1)

# Save the updated file
df.to_excel("output.xlsx", index=False)
print("Processing complete. Output saved to output.xlsx")
