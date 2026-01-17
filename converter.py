import docx
import json
import re
import os

def parse_docx(file_path):
    """
    Parses the DOCX file to extract drug names and regulations.
    Assumes drug names start with '9.' (e.g., '9.74').
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return []

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return []

    parsed_data = []
    current_drug = None
    current_regulation_lines = []

    # Regex to identify drug headings like "9.74 Pembrolizumab" or "9.74."
    drug_pattern = re.compile(r'^9\.\d+\.?\s*.*')
    
    # Regex for regulation numbering to apply blockquote: "1.", "2.", "(1)", "9.18.1"
    numbering_pattern = re.compile(r'^(\d+(?:\.\d+)+\.?|\d+\.|\(\d+\))')

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        if drug_pattern.match(text):
            # Save previous drug if exists
            if current_drug:
                # Use double newline for Markdown paragraphs
                full_regulation = "\n\n".join(current_regulation_lines).strip()
                parsed_data.append({
                    "raw_drug_name": current_drug,
                    "raw_regulation": full_regulation
                })
            
            # Start new drug
            # Clean drug name: Remove anything after ":" or "："
            clean_name = re.split(r'[:：]', text)[0].strip()
            current_drug = clean_name
            current_regulation_lines = []
        else:
            if current_drug:
                # Apply blockquote formatting to numbering
                # If the line starts with a number pattern, prepend "> "
                match = numbering_pattern.match(text)
                if match:
                    text = f"> {text}"
                
                current_regulation_lines.append(text)

    # Append the last one
    if current_drug:
        full_regulation = "\n\n".join(current_regulation_lines).strip()
        parsed_data.append({
            "raw_drug_name": current_drug,
            "raw_regulation": full_regulation
        })

    return parsed_data

def classify_and_format(raw_data):
    """
    Classifies regulations by cancer type and formats them for the JSON output.
    Uses 'Hierarchy Inheritance' & 'Synonym Mapping' logic:
    - Normalizes different cancer names to standard ones using SYNONYM_MAPPING.
    - Parent Lines (> 1., > I.): Check for keywords to set context or reset to General.
    - Child Lines (> (1)): Inherit context from parent (do not check keywords).
    - Other Lines: Context is sticky, but updates if new keywords are found.
    - Reset Keywords: Force reset to General.
    """
    
    # 1. Synonym Mapping
    # Maps keywords -> Standardized Cancer Type
    SYNONYM_MAPPING = {
        '直腸癌': '結直腸癌', '結腸癌': '結直腸癌', '大腸癌': '結直腸癌', 
        '大腸直腸癌': '結直腸癌', '結直腸癌': '結直腸癌',
        '胃癌': '胃癌', '胃食道接合處': '胃癌',
        '非小細胞肺癌': '肺癌', '肺癌': '肺癌', '小細胞肺癌': '小細胞肺癌',
        '乳癌': '乳癌',
        '胰臟癌': '胰臟癌', '胰腺癌': '胰臟癌',
        '肝癌': '肝癌', '肝細胞癌': '肝癌',
        '食道癌': '食道癌',
        '膽道癌': '膽道癌', '膽管癌': '膽道癌',
        '黑色素瘤': '黑色素瘤',
        '淋巴瘤': '淋巴瘤',
        '白血病': '白血病',
        '泌尿道癌': '泌尿道癌', '尿路上皮癌': '泌尿道癌',
        '腎細胞癌': '腎細胞癌', '腎癌': '腎細胞癌',
        '頭頸癌': '頭頸癌', '口腔癌': '頭頸癌', '下咽癌': '頭頸癌', '口咽癌': '頭頸癌',
        '卵巢癌': '卵巢癌',
        '攝護腺癌': '攝護腺癌', '前列腺癌': '攝護腺癌',
        '甲狀腺癌': '甲狀腺癌',
        '腦癌': '腦癌', '膠質母細胞瘤': '腦癌',
        '骨癌': '骨癌',
        '軟組織肉瘤': '軟組織肉瘤',
        '子宮頸癌': '子宮頸癌',
        '子宮體癌': '子宮體癌', '子宮內膜癌': '子宮體癌',
        '膀胱癌': '膀胱癌',
        '皮膚癌': '皮膚癌', '基底細胞癌': '皮膚癌',
        '多發性骨髓瘤': '多發性骨髓瘤',
        '神經母細胞瘤': '神經母細胞瘤'
    }

    # Keywords that force a reset to General
    reset_keywords = ['給付規定：', '給付規定:', '通則：', '通則:']

    # Regex patterns for hierarchy
    # Parent: starts with "> 1." or "> I." or "> A."
    # We simplified in parse_docx to "> 1.", "> 9.1.", etc.
    # Note: parse_docx adds "> " to numbering.
    parent_pattern = re.compile(r'^> \d+\.')  # Matches "> 1.", "> 9."
    # Child: starts with "> (1)"
    child_pattern = re.compile(r'^> \(\d+\)') # Matches "> (1)"

    formatted_list = []

    for item in raw_data:
        drug_name_full = item['raw_drug_name']
        raw_regulation = item['raw_regulation']
        
        paragraphs = raw_regulation.split('\n\n')
        
        type_buckets = {} 
        current_cancer_types = ['General']

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 1. Check for Reset Keywords (Global Reset)
            # If explicit reset keyword found, force General immediately
            is_generic_reset = False
            for rk in reset_keywords:
                if rk in para:
                    current_cancer_types = ['General']
                    is_generic_reset = True
                    break
            
            # Determine line type if no generic reset happened
            is_parent = bool(parent_pattern.match(para))
            is_child = bool(child_pattern.match(para))
            
            # Logic Branching
            if is_generic_reset:
                # Already reset above
                pass
            
            elif is_child:
                # CHILD: Inherit context! 
                # Do NOT scan for keywords. Maintain current_cancer_types.
                pass
            
            else:
                # PARENT or Normal Text: Scan for keywords
                # If Parent: We effectively "reset" context before scanning (unless keywords found)
                # Actually, standard behavior: Scan. If found, update. If not found -> ?
                # User request: "If parent... attempt to grab. If not grab -> Reset to General."
                
                found_types_set = set()
                for keyword, standard_type in SYNONYM_MAPPING.items():
                    if keyword in para:
                        found_types_set.add(standard_type)
                
                found_types = list(found_types_set)

                if is_parent:
                    # Parent Line Logic
                    if found_types:
                        current_cancer_types = found_types
                    else:
                        # Parent line with NO keywords -> Reset to General
                        # e.g. "1. Dosage:" (General) vs "1. Breast Cancer:" (Breast Cancer)
                        current_cancer_types = ['General']
                else:
                    # Normal Line (Sticky)
                    # If keywords found -> Switch context
                    # If no keywords -> Keep context
                    if found_types:
                        current_cancer_types = found_types

            # Add to buckets
            for c_type in current_cancer_types:
                if c_type not in type_buckets:
                    type_buckets[c_type] = []
                type_buckets[c_type].append(para)

        # Output Generation
        if not type_buckets:
             formatted_list.append({
                "drug_name": drug_name_full,
                "cancer_type": "未分類",
                "regulation": raw_regulation
            })
        else:
            # Order: General first, then others
            keys = list(type_buckets.keys())
            if 'General' in keys:
                keys.remove('General')
                keys.insert(0, 'General')
            
            for c_type in keys:
                paras = type_buckets[c_type]
                reg_content = "\n\n".join(paras)
                formatted_list.append({
                    "drug_name": drug_name_full,
                    "cancer_type": c_type,
                    "regulation": reg_content
                })

    return formatted_list

def main():
    input_file = 'regulations.docx'
    output_file = 'nhi_data.json'
    
    print(f"Reading {input_file}...")
    raw_data = parse_docx(input_file)
    print(f"Found {len(raw_data)} drug sections.")
    
    print("Classifying and formatting...")
    final_data = classify_and_format(raw_data)
    print(f"Generated {len(final_data)} entries (expanded by cancer type).")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully saved to {output_file}")

if __name__ == "__main__":
    main()
