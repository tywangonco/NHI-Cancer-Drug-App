import docx
import json
import re
import os

# === Cancer Synonym Mapping ===
CANCER_MAPPING = {
    # === 肺癌大一統 (全部歸類為 '肺癌') ===
    '非鱗狀非小細胞肺癌': '肺癌',
    '非小細胞肺癌': '肺癌',
    '小細胞肺癌': '肺癌',
    '鱗狀細胞肺癌': '肺癌',
    '鱗狀上皮細胞癌': '肺癌',
    '肺癌': '肺癌',
    'NSCLC': '肺癌',
    'SCLC': '肺癌',
    # === 其他既有的癌別 ===
    '直腸癌': '結直腸癌',
    '結腸癌': '結直腸癌',
    '大腸癌': '結直腸癌',
    '大腸直腸癌': '結直腸癌',
    '結直腸癌': '結直腸癌',
    '胃癌': '胃癌',
    '胃食道接合處': '胃癌',
    '乳癌': '乳癌',
    '胰臟癌': '胰臟癌', '胰腺癌': '胰臟癌',
    '肝癌': '肝癌', '肝細胞癌': '肝癌',
    '膽道癌': '膽道癌', '膽管癌': '膽道癌',
    '攝護腺癌': '攝護腺癌', '前列腺癌': '攝護腺癌',
    '黑色素瘤': '黑色素瘤',
    '泌尿道上皮癌': '尿路上皮癌', '泌尿道癌': '尿路上皮癌', '尿路上皮癌': '尿路上皮癌',
    '膀胱癌': '尿路上皮癌',
    '輸尿管癌': '尿路上皮癌',
    '腎盂癌': '尿路上皮癌',
    '頭頸癌': '頭頸癌',
    '口腔癌': '頭頸癌',
    '下咽癌': '頭頸癌',
    '口咽癌': '頭頸癌',
    '喉癌': '頭頸癌',
    '卵巢癌': '卵巢癌',
    '輸卵管癌': '卵巢癌',
    '腹膜癌': '卵巢癌',
    '子宮頸癌': '子宮頸癌',
    '子宮體癌': '子宮體癌', '子宮內膜癌': '子宮體癌',
    '淋巴瘤': '淋巴瘤',
    '白血病': '白血病',
    '多發性骨髓瘤': '多發性骨髓瘤',
    '神經母細胞瘤': '神經母細胞瘤',
    'GIST': '胃腸道基質瘤',
    '胃腸道基質瘤': '胃腸道基質瘤',
    '軟組織肉瘤': '軟組織肉瘤',
    '甲狀腺癌': '甲狀腺癌',
    '腎細胞癌': '腎細胞癌', '腎癌': '腎細胞癌',
    '骨癌': '骨癌',
    '皮膚癌': '皮膚癌', '基底細胞癌': '皮膚癌'
}

def parse_docx(file_path):
    """
    Parses the DOCX file with strict hierarchical logic.
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return []

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return []

    # === Regex Patterns ===
    # Drug Header: 9.xx (e.g. 9.1, 9.10)
    drug_pattern = re.compile(r'^9\.\d+')
    
    # Hierarchy Levels
    level_1_pattern = re.compile(r'^\d+\.')        # 1., 2.
    level_2_pattern = re.compile(r'^\(\d+\)')      # (1), (2)
    level_3_pattern = re.compile(r'^[IVX]+\.')     # I., II.
    level_4_pattern = re.compile(r'^[ivx]+\.')     # i., ii.

    parsed_data = []
    
    # State Variables
    current_drug_name = None
    current_cancer = 'General'
    
    # Buffer: { 'General': [lines], 'Lung Cancer': [lines], ... }
    # Using a list to preserve order of appearance if needed, but dict makes it easier to group.
    # We'll use a dict where keys are cancer types and values are lists of formatted strings.
    drug_cancer_buckets = {} 
    
    # Indentation State (for visual hierarchy)
    # Stores the prefix string (e.g., "", "> ", ">> ")
    current_visual_prefix = "" 

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # -- Check for New Drug Section --
        if drug_pattern.match(text):
            # 1. Flush previous drug data
            if current_drug_name:
                flush_drug_data(parsed_data, current_drug_name, drug_cancer_buckets)
            
            # 2. Reset State
            clean_name = re.split(r'[:：]', text)[0].strip()
            current_drug_name = clean_name
            current_cancer = 'General'
            drug_cancer_buckets = {}
            current_visual_prefix = "" 
            continue

        # -- If we are not inside a drug section yet, skip --
        if not current_drug_name:
            continue

        # -- Determine Line Hierarchy & Classification --
        
        # Level 1: Main Item (e.g., 1., 2.)
        # Decision Maker for Cancer Type
        if level_1_pattern.match(text):
            # Formatting: Bold, No Indent
            formatted_text = f"**{text}**"
            current_visual_prefix = "" 
            
            # Logic: Scan for Cancer Type
            found_cancer = None
            for keyword, standard_type in CANCER_MAPPING.items():
                if keyword in text:
                    found_cancer = standard_type
                    break # First match wins (or could be improved, but usually sufficient)
            
            if found_cancer:
                current_cancer = found_cancer
            else:
                current_cancer = 'General' # Reset if no cancer found in Level 1

        # Level 2: Sub Item (e.g., (1), (2))
        # Inherit Cancer Type
        elif level_2_pattern.match(text):
            current_visual_prefix = "> "
            formatted_text = f"> {text}"
            # STRICT: No cancer scanning

        # Level 3: Detail (e.g., I., II.)
        # Inherit Cancer Type
        elif level_3_pattern.match(text):
            current_visual_prefix = ">> "
            formatted_text = f">> {text}"
            # STRICT: No cancer scanning

        # Level 4: Micro Detail (e.g., i., ii.)
        # Inherit Cancer Type
        elif level_4_pattern.match(text):
            current_visual_prefix = ">>> "
            formatted_text = f">>> {text}"
            # STRICT: No cancer scanning

        # Plain Text (No Numbering)
        # Inherit Cancer Type AND Visual Prefix
        else:
            # Maintain previous indentation
            if current_visual_prefix:
                formatted_text = f"{current_visual_prefix}{text}"
            else:
                formatted_text = text # No indent if Level 1 follower or top level

        # -- Add to Bucket --
        if current_cancer not in drug_cancer_buckets:
            drug_cancer_buckets[current_cancer] = []
        
        drug_cancer_buckets[current_cancer].append(formatted_text)

    # -- Flush the last drug --
    if current_drug_name:
        flush_drug_data(parsed_data, current_drug_name, drug_cancer_buckets)

    return parsed_data

def flush_drug_data(parsed_data, drug_name, buckets):
    """
    Helper to finalize a drug's data and append to the list.
    We ensure 'General' comes first if present.
    """
    if not buckets:
        # Fallback if drug header exists but no content
        parsed_data.append({
            "drug_name": drug_name,
            "cancer_type": "General",
            "regulation": ""
        })
        return

    # Sort keys: General first, then others alphabetically or by insertion?
    # Insertion order is preserved in Python 3.7+, but let's be explicit about General.
    cancer_types = list(buckets.keys())
    
    # Move General to front if exists
    if 'General' in cancer_types:
        cancer_types.remove('General')
        cancer_types.insert(0, 'General')
    
    for c_type in cancer_types:
        lines = buckets[c_type]
        full_text = "\n\n".join(lines).strip() # Multi-line join
        
        parsed_data.append({
            "drug_name": drug_name,
            "cancer_type": c_type,
            "regulation": full_text
        })

def main():
    input_file = 'regulations.docx' # Or whatever default
    output_file = 'nhi_data.json'
    
    # Check if input file exists, maybe use absolute path or relative
    if not os.path.exists(input_file):
        # Fallback to search or prompt? For script logic, we just print error.
        # But based on user context, they probably have this file.
        # We will try to find it in the current directory.
        pass

    print(f"Reading {input_file} w/ Strict Hierarchy Parser...")
    final_data = parse_docx(input_file)
    print(f"Extracted {len(final_data)} entries.")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
