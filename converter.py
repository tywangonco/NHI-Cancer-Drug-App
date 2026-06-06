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
    '肺腺癌': '肺癌',
    # === 其他既有的癌別 ===
    '直腸癌': '結直腸癌',
    '結腸癌': '結直腸癌',
    '大腸癌': '結直腸癌',
    '大腸直腸癌': '結直腸癌',
    '結直腸癌': '結直腸癌',
    '胃癌': '胃癌',
    '胃腺癌': '胃癌',
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
    '頭頸部鱗狀上皮癌': '頭頸癌',
    '頭頸部鱗狀細胞癌': '頭頸癌',
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
    '皮膚癌': '皮膚癌', '基底細胞癌': '皮膚癌',
    '卡波西氏肉瘤': '卡波西氏肉瘤', '卡波西': '卡波西氏肉瘤',
    '食道癌': '食道癌', '食道鱗狀細胞癌': '食道癌',
    '腦瘤': '腦瘤', '神經膠母細胞瘤': '腦瘤', '星狀細胞瘤': '腦瘤', '寡樹突膠質細胞瘤': '腦瘤',
    '間質細胞瘤': '間質細胞瘤', '肋膜間質': '間質細胞瘤'
}

def parse_docx(file_path):
    """
    Parses the DOCX file with optimized cancer type detection.
    Groups each drug's paragraphs by Level 1 rules, scanning the entire rule block (including sub-paragraphs)
    to resolve the cancer type, fallback to '通則' if no unique cancer name is matched.
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return []

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        print(f"Error reading DOCX file: {e}")
        return []

    drug_pattern = re.compile(r'^9\.\d+')
    
    level_1_pattern = re.compile(r'^\d+\.')
    level_2_pattern = re.compile(r'^\(\d+\)')
    level_3_pattern = re.compile(r'^[IVX]+\.')
    level_4_pattern = re.compile(r'^[ivx]+\.')

    parsed_data = []
    
    # Step 1: Segment paragraphs into separate drugs
    drugs_raw = []
    current_drug = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        if drug_pattern.match(text):
            if current_drug:
                drugs_raw.append(current_drug)
            current_drug = {
                'header': text,
                'paragraphs': []
            }
        else:
            if current_drug:
                current_drug['paragraphs'].append(text)
                
    if current_drug:
        drugs_raw.append(current_drug)
        
    # Step 2: Parse rules for each drug
    for drug in drugs_raw:
        header_text = drug['header']
        clean_name = re.split(r'[:：]', header_text)[0].strip()
        
        rules = []
        current_rule = None
        current_visual_prefix = ""
        
        for text in drug['paragraphs']:
            if level_1_pattern.match(text):
                formatted_text = f"**{text}**"
                current_visual_prefix = ""
                if current_rule:
                    rules.append(current_rule)
                current_rule = {
                    'paragraphs': [formatted_text],
                    'raw_paragraphs': [text]
                }
            elif level_2_pattern.match(text):
                current_visual_prefix = "> "
                formatted_text = f"> {text}"
                if current_rule is None:
                    current_rule = {'paragraphs': [], 'raw_paragraphs': []}
                current_rule['paragraphs'].append(formatted_text)
                current_rule['raw_paragraphs'].append(text)
            elif level_3_pattern.match(text):
                current_visual_prefix = ">> "
                formatted_text = f">> {text}"
                if current_rule is None:
                    current_rule = {'paragraphs': [], 'raw_paragraphs': []}
                current_rule['paragraphs'].append(formatted_text)
                current_rule['raw_paragraphs'].append(text)
            elif level_4_pattern.match(text):
                current_visual_prefix = ">>> "
                formatted_text = f">>> {text}"
                if current_rule is None:
                    current_rule = {'paragraphs': [], 'raw_paragraphs': []}
                current_rule['paragraphs'].append(formatted_text)
                current_rule['raw_paragraphs'].append(text)
            else:
                if current_visual_prefix:
                    formatted_text = f"{current_visual_prefix}{text}"
                else:
                    formatted_text = text
                if current_rule is None:
                    current_rule = {'paragraphs': [], 'raw_paragraphs': []}
                current_rule['paragraphs'].append(formatted_text)
                current_rule['raw_paragraphs'].append(text)
                
        if current_rule:
            rules.append(current_rule)
            
        # Step 3: Scan each rule block for cancer keywords and assign bucket
        drug_cancer_buckets = {}
        for rule in rules:
            combined_text = "\n".join(rule['raw_paragraphs'])
            
            matched_cancers = set()
            for keyword, standard_type in CANCER_MAPPING.items():
                if keyword in combined_text:
                    matched_cancers.add(standard_type)
                    
            # Rule classification: Unique match -> standard cancer, otherwise -> '通則'
            if len(matched_cancers) == 1:
                rule_cancer = list(matched_cancers)[0]
            else:
                rule_cancer = '通則'
                
            if rule_cancer not in drug_cancer_buckets:
                drug_cancer_buckets[rule_cancer] = []
            drug_cancer_buckets[rule_cancer].extend(rule['paragraphs'])
            
        flush_drug_data(parsed_data, clean_name, drug_cancer_buckets, header_text)
        
    return parsed_data

def flush_drug_data(parsed_data, drug_name, buckets, full_header=""):
    """
    Helper to finalize a drug's data and append to the list.
    We ensure '通則' comes first if present.
    """
    if not buckets:
        # Fallback if drug header exists but no content
        parsed_data.append({
            "drug_name": drug_name,
            "cancer_type": "通則",
            "regulation": "",
            "latest_date": None
        })
        return

    # Sort keys: 通則 first, then others alphabetically or by insertion?
    # Insertion order is preserved in Python 3.7+, but let's be explicit about 通則.
    cancer_types = list(buckets.keys())
    
    # Move 通則 to front if exists
    if '通則' in cancer_types:
        cancer_types.remove('通則')
        cancer_types.insert(0, '通則')
    
    for c_type in cancer_types:
        lines = buckets[c_type]
        full_text = "\n\n".join(lines).strip() # Multi-line join
        
        # Date extraction
        date_matches = re.findall(r'(\d{2,3})/(\d{1,2})/(\d{1,2})', full_text)
        if not date_matches:
            header_dates = re.findall(r'(\d{2,3})/(\d{1,2})/(\d{1,2})', full_header)
            if len(header_dates) == 1:
                date_matches = header_dates
        latest_date = None
        if date_matches:
            parsed_dates = []
            for y, m, d in date_matches:
                try:
                    score = int(y) * 10000 + int(m) * 100 + int(d)
                    clean_date = f"{int(y)}/{int(m)}/{int(d)}"
                    parsed_dates.append((score, clean_date))
                except ValueError:
                    pass
            if parsed_dates:
                parsed_dates.sort(key=lambda x: x[0], reverse=True)
                latest_date = parsed_dates[0][1]

        parsed_data.append({
            "drug_name": drug_name,
            "cancer_type": c_type,
            "regulation": full_text,
            "latest_date": latest_date
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
