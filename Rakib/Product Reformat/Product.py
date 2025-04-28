import pandas as pd

def format_title(title, brand, part_number):
    """
    Format the title using the criteria:
    Brand name + product type + motorcycle model or automobile model + year + part number.
    """
    title = str(title).strip().upper() if pd.notna(title) else ""
    brand = str(brand).strip().upper() if pd.notna(brand) else ""
    part_number = str(part_number).strip().upper() if pd.notna(part_number) else ""
    
    # Remove duplicate brand name and part number from title
    if brand and brand in title:
        title = title.replace(brand, "").strip()
    if part_number and part_number in title:
        title = title.replace(part_number, "").strip()
    
    # Construct the formatted title
    parts = [brand, title, part_number]
    formatted_title = " ".join(part for part in parts if part)
    
    return formatted_title.strip()

def format_description(description, brand, part_number):
    """
    Format the description with the specified formatting rules, including breaklines.
    """
    description = str(description) if pd.notna(description) else ""
    lines = [line.strip() for line in description.splitlines()]
    
    if not lines:
        return ""
    
    brand = str(brand).strip().upper() if pd.notna(brand) else ""
    part_number = str(part_number).strip().upper() if pd.notna(part_number) else ""
    
    # First line formatting (title part)
    first_line = lines[0].upper()
    
    if brand and brand in first_line:
        first_line = first_line.replace(brand, "").strip()
    if part_number and part_number in first_line:
        first_line = first_line.replace(part_number, "").strip()
    
    formatted_title = f"{brand} {first_line}".strip() if brand else first_line
    if part_number:
        formatted_title = f"{formatted_title} {part_number}".strip()
    
    # Part number line
    part_number_line = f"Part #: {part_number}" if part_number else "Part #:"
    
    # Prepare body lines
    body_lines = []
    for line in lines[1:]:
        if line and "FOR MORE INFO PLEASE CONTACT US" not in line.upper() and "--------------------" not in line:
            body_lines.append("\n" + line.strip())
    
    # Add one additional breakline before the last paragraph
    if len(body_lines) > 1:
        body_lines[-1] = "\n" + body_lines[-1]
    
    # Combine all parts
    formatted_lines = [formatted_title, part_number_line] + body_lines
    
    return "\n".join(formatted_lines).strip() + "\n\n"

def main():
    # Read Excel file
    df = pd.read_excel("input.xlsx")
    df.columns = df.columns.str.strip()  # Clean column names

    # Ensure required columns exist
    for col in ["Part Number", "Brand", "Title", "Description"]:
        if col not in df.columns:
            df[col] = ""

    # Apply formatting
    df["Formatted Title"] = df.apply(lambda row: format_title(row["Title"], row["Brand"], row["Part Number"]), axis=1)
    df["Formatted Description"] = df.apply(lambda row: format_description(row["Description"], row["Brand"], row["Part Number"]), axis=1)

    # Save output
    df.to_excel("output.xlsx", index=False)
    print("Processing complete. Output saved to output.xlsx.")

if __name__ == "__main__":
    main()
