import docx
import re
import csv
import os
import sys

# Set output encoding to UTF-8 for console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Existing cancer mappings from converter.py
CANCER_MAPPING = {
    # 肺癌大一統
    '非鱗狀非小細胞肺癌': '肺癌',
    '非小細胞肺癌': '肺癌',
    '小細胞肺癌': '肺癌',
    '鱗狀細胞肺癌': '肺癌',
    '鱗狀上皮細胞癌': '肺癌',
    '肺癌': '肺癌',
    'NSCLC': '肺癌',
    '肺腺癌': '肺癌',
    # 其他既有癌別
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

def analyze_document(file_path):
    if not os.path.exists(file_path):
        print(f"錯誤：找不到檔案 '{file_path}'")
        return []

    try:
        doc = docx.Document(file_path)
    except Exception as e:
        print(f"讀取 DOCX 檔案失敗: {e}")
        return []

    drug_pattern = re.compile(r'^9\.\d+')
    level_1_pattern = re.compile(r'^\d+\.')
    
    # Regex to find potential cancer keywords (Chinese words ending in 癌, 瘤, 白血病, 骨髓瘤, 肉瘤)
    # Allows 2 to 10 Chinese characters before the keyword suffix
    cancer_regex = re.compile(r'[\u4e00-\u9fa5]{2,10}(?:癌|瘤|白血病|骨髓瘤|肉瘤)')

    drugs = []
    current_drug = None

    # Step 1: Segment docx paragraphs into drugs
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        if drug_pattern.match(text):
            if current_drug:
                drugs.append(current_drug)
            current_drug = {
                'header': text,
                'paragraphs': []
            }
        else:
            if current_drug:
                current_drug['paragraphs'].append(text)
                
    if current_drug:
        drugs.append(current_drug)

    analysis_results = []

    # Step 2: Extract level-1 rules and analyze them
    for drug in drugs:
        header = drug['header']
        
        # Split rules by level-1 hierarchy (e.g., "1.", "2.")
        rules = []
        current_rule = None
        
        for text in drug['paragraphs']:
            if level_1_pattern.match(text):
                if current_rule:
                    rules.append(current_rule)
                current_rule = {
                    'num_str': text.split('.')[0] + '.',
                    'header_text': text,
                    'all_text_list': [text]
                }
            else:
                if current_rule is None:
                    # Paragraphs before the first "1." rule
                    current_rule = {
                        'num_str': '一般',
                        'header_text': '(無標題)',
                        'all_text_list': [text]
                    }
                else:
                    current_rule['all_text_list'].append(text)
        
        if current_rule:
            rules.append(current_rule)

        # Step 3: Analyze each rule block
        for rule in rules:
            full_rule_text = "\n".join(rule['all_text_list'])
            
            # Find existing cancer matches
            matched_cancers = set()
            for keyword, standard_type in CANCER_MAPPING.items():
                if keyword in full_rule_text:
                    matched_cancers.add(standard_type)
            
            # Find potential new cancer keywords using regex
            potential_cancers = set(cancer_regex.findall(full_rule_text))
            # Clean up potential cancers (exclude common non-cancer words if any, and filter out very generic ones)
            # Remove any match that is already covered by existing CANCER_MAPPING keys to avoid duplication
            potential_cancers = {pc for pc in potential_cancers if pc not in CANCER_MAPPING}

            analysis_results.append({
                'Drug': header,
                'Rule_Num': rule['num_str'],
                'Rule_Header': rule['header_text'][:150], # Truncate for CSV readability
                'Matched_Cancers': ", ".join(sorted(list(matched_cancers))) if matched_cancers else "無符合",
                'Potential_New_Cancers': ", ".join(sorted(list(potential_cancers))) if potential_cancers else "無",
                'Full_Text_Length': len(full_rule_text)
            })
            
    return analysis_results

def main():
    input_file = 'regulations.docx'
    output_file = 'regulations_analysis.csv'
    
    print(f"正在分析 {input_file} 中的條文第一階層...")
    results = analyze_document(input_file)
    print(f"分析完成！共提取出 {len(results)} 個條文區塊。")

    # Write to CSV using UTF-8-sig (with BOM) so Excel opens it correctly on Windows
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Drug', 'Rule_Num', 'Rule_Header', 'Matched_Cancers', 'Potential_New_Cancers', 'Full_Text_Length']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in results:
            writer.writerow(row)
            
    print(f"分析結果已儲存至：{output_file}")
    print("您可以使用 Excel 直接開啟此檔案查看並進行癌別分類規劃。")

if __name__ == "__main__":
    main()
