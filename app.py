import streamlit as st
import json
import os
import re
import converter  # Import the converter module

# 1. Page Config
st.set_page_config(
    page_title="癌症用藥給付規定查詢助手 (Cancer Drug Regulations Assistant)",
    page_icon="💊",
    layout="wide"
)

# 2. Inject Custom CSS for Premium Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=Outfit:wght@300;400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', 'Noto Sans TC', sans-serif;
        background-color: #fafafa;
    }
    
    /* Main App Header */
    .app-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 2.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3), 0 4px 6px -4px rgba(59, 130, 246, 0.3);
    }
    .app-header h1 {
        color: white !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    .app-header p {
        font-size: 1.1rem !important;
        opacity: 0.9 !important;
        margin: 0 !important;
    }
    
    /* Section style */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 1rem;
        border-left: 5px solid #3b82f6;
        padding-left: 10px;
    }
    
    /* Custom style for expanders */
    div[data-testid="stExpander"] {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.75rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 1rem !important;
        overflow: hidden !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stExpander"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08) !important;
        border-color: #cbd5e1 !important;
    }
    div[data-testid="stExpander"] details summary {
        background: #f8fafc !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        color: #1e293b !important;
        font-size: 1.1rem !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        color: #3b82f6 !important;
    }
    
    /* Latest updates card list */
    .update-card {
        background: #ffffff;
        border: 1px solid #f1f5f9;
        border-left: 4px solid #f59e0b;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Loads the NHI data from the JSON file."""
    file_path = 'nhi_data.json'
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_concise_regulation(regulation_text, latest_date):
    if not regulation_text:
        return ""
    paragraphs = [p.strip() for p in regulation_text.split('\n\n') if p.strip()]
    matching_paras = [p for p in paragraphs if latest_date in p]
    if matching_paras:
        return "\n\n".join(matching_paras)
    return regulation_text

def main():
    # Sidebar
    st.sidebar.markdown("""
    <div style="background: white; padding: 1.5rem; border-radius: 0.75rem; border: 1px solid #e2e8f0; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
        <h3 style="margin-top: 0; color: #1e3a8a;">🔧 Settings & Links</h3>
        <p style="margin-bottom: 0.5rem; font-size: 0.95rem;">相關連結與工具：</p>
        <a href="https://www.nhi.gov.tw/ch/cp-7593-ad2a9-3397-1.html" target="_blank" style="text-decoration: none; color: #3b82f6; font-weight: 600;">🔗 健保署給付規定下載頁面</a>
    </div>
    """, unsafe_allow_html=True)

    # Header section with custom HTML
    st.markdown("""
    <div class="app-header">
        <h1>🏥 癌症用藥給付規定查詢助手</h1>
        <p>Cancer Drug Payment Regulations Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    data = load_data()
    
    if data is None:
        st.error("Error: `nhi_data.json` not found. Please ensure the data file is in the same directory.")
        st.stop()

    # -- What's New section --
    # Extract entries with latest_date
    updates = []
    for item in data:
        if item.get('latest_date'):
            dates_parts = item['latest_date'].split('/')
            if len(dates_parts) == 3:
                try:
                    score = int(dates_parts[0]) * 10000 + int(dates_parts[1]) * 100 + int(dates_parts[2])
                    updates.append((score, item['latest_date'], item['drug_name'], item['cancer_type'], item.get('regulation', '')))
                except ValueError:
                    pass
    
    # Sort updates by score descending
    updates.sort(key=lambda x: x[0], reverse=True)
    
    # Filter to only keep the absolute latest batch of updates
    if updates:
        max_score = updates[0][0]
        latest_updates = [u for u in updates if u[0] == max_score]
    else:
        latest_updates = []
    
    # Get unique updates (by drug and cancer) for the latest batch
    top_updates = []
    seen = set()
    for upd in latest_updates:
        identifier = f"{upd[2]} - {upd[3]}"
        if identifier not in seen:
            seen.add(identifier)
            top_updates.append(upd)
                
    latest_update_date = None
    if top_updates:
        latest_update_date = top_updates[0][1]
        
    header_title = "📢 最新給付規定 (What's New)"
    if latest_update_date:
        header_title += f" [ 更新日期: {latest_update_date} ]"
        
    with st.expander(header_title, expanded=False):
        if top_updates:
            for upd in top_updates:
                drug_name = upd[2]
                cancer_type = upd[3]
                raw_regulation = upd[4]
                
                # Extract concise regulation
                concise_reg = get_concise_regulation(raw_regulation, latest_update_date)
                
                # Show drug name and concise regulation text directly
                st.markdown(f"**💊 {drug_name} ({cancer_type})**")
                if concise_reg.strip():
                    st.markdown(concise_reg)
                else:
                    st.markdown("<p style='color: #64748b; font-style: italic; margin: 0;'>無特定修正條文。</p>", unsafe_allow_html=True)
                st.markdown("<div style='margin-top: 0.5rem; margin-bottom: 1rem; border-bottom: 1px dashed #e2e8f0;'></div>", unsafe_allow_html=True)
        else:
            st.info("尚無更新資訊")
            
    st.markdown("<br/>", unsafe_allow_html=True)
    st.divider()

    # -- Drug Selection section --
    st.markdown('<div class="section-title">🔍 藥物搜尋與選擇</div>', unsafe_allow_html=True)
    
    # Extract unique drug names
    all_drugs = sorted(list(set(item['drug_name'] for item in data)))
    
    # Two columns for search and selectbox side-by-side
    col1, col2 = st.columns([1, 2])
    with col1:
        search_term = st.text_input("輸入關鍵字搜尋藥名", placeholder="例：Docetaxel...", label_visibility="collapsed")
    with col2:
        if search_term:
            filtered_drugs = [drug for drug in all_drugs if search_term.lower() in drug.lower()]
        else:
            filtered_drugs = all_drugs

        if not filtered_drugs:
            st.warning("查無符合的藥物 (No matching drugs found).")
            selected_drug = None
        else:
            selected_drug = st.selectbox(
                "選擇藥物名稱", 
                filtered_drugs, 
                label_visibility="collapsed"
            )

    # -- Display Regulations section --
    if selected_drug:
        st.divider()
        st.markdown(f'<div class="section-title">📋 {selected_drug} - 給付規定詳情</div>', unsafe_allow_html=True)
        
        # Get all matching regulations for this drug
        matching_items = [item for item in data if item['drug_name'] == selected_drug]
        
        # Parse all entries into level 1 rules
        all_rules = []
        for entry in matching_items:
            regulation = entry.get('regulation', '')
            cancer_type = entry.get('cancer_type', '')
            latest_date = entry.get('latest_date', None)
            
            paragraphs = [p.strip() for p in regulation.split('\n\n') if p.strip()]
            
            # Check if any paragraph starts with a number. If none, treat the whole thing as one rule.
            has_numbered_rule = any(re.match(r'^\**\d+\.', p) for p in paragraphs)
            
            if not has_numbered_rule:
                all_rules.append({
                    'number': 999,
                    'number_str': '',
                    'content_lines': paragraphs,
                    'cancer_type': cancer_type,
                    'latest_date': latest_date
                })
                continue
                
            current_rule = None
            for p in paragraphs:
                match = re.match(r'^\**(\d+)\.', p)
                if match:
                    num = int(match.group(1))
                    num_str = f"{num}."
                    if current_rule:
                        all_rules.append(current_rule)
                    current_rule = {
                        'number': num,
                        'number_str': num_str,
                        'content_lines': [p],
                        'cancer_type': cancer_type,
                        'latest_date': latest_date
                    }
                else:
                    if current_rule is None:
                        current_rule = {
                            'number': 0,
                            'number_str': '',
                            'content_lines': [p],
                            'cancer_type': cancer_type,
                            'latest_date': latest_date
                        }
                    else:
                        current_rule['content_lines'].append(p)
            if current_rule:
                all_rules.append(current_rule)
        
        # Sort all rules by their level 1 number
        all_rules.sort(key=lambda x: x['number'])
        
        # Show all rules directly on the page, partitioned by level 1 items
        for rule in all_rules:
            num_str = rule['number_str']
            cancer_type = rule['cancer_type']
            latest_date = rule['latest_date']
            
            # Format title nicely with item number, cancer type, and date tags
            expander_title = f"📝 項目 {num_str}" if num_str else "📝 一般規定 (General)"
            expander_title += f" [ 🎗️ {cancer_type} ]"
            if latest_date:
                expander_title += f" (最後更新日期: {latest_date})"
                
            content_text = "\n\n".join(rule['content_lines'])
            
            with st.expander(expander_title, expanded=False):
                if content_text.strip():
                    st.markdown(content_text)
                else:
                    st.markdown("<p style='color: #64748b; font-style: italic; margin: 0;'>本項別尚無特定給付條文內容。</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
