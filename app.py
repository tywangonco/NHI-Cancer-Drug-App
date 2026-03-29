import streamlit as st

st.set_page_config(
    page_title="癌症用藥助手",
    page_icon="💊",
)

import json
import os
import converter  # Import the converter module

# Set page config
st.set_page_config(page_title="Cancer Drug Assistant", layout="wide")

@st.cache_data
def load_data():
    """Loads the NHI data from the JSON file."""
    file_path = 'nhi_data.json'
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Sidebar
    st.sidebar.title("🔧 Settings")
    st.sidebar.markdown("[🔗 健保署給付規定下載頁面](https://www.nhi.gov.tw/ch/cp-7593-ad2a9-3397-1.html)")

    st.title("🏥 Cancer Drug Payment Regulations")
    st.markdown("Select a drug and cancer type to view the specific NHI payment regulations.")

    # Load data
    data = load_data()
    
    if data is None:
        st.error("Error: `nhi_data.json` not found. Please ensure the data file is in the same directory.")
        st.stop()

    st.header("📢 What's New (最新給付規定)")
    # Extract entries with latest_date
    updates = []
    for item in data:
        if item.get('latest_date'):
            dates_parts = item['latest_date'].split('/')
            if len(dates_parts) == 3:
                try:
                    score = int(dates_parts[0]) * 10000 + int(dates_parts[1]) * 100 + int(dates_parts[2])
                    updates.append((score, item['latest_date'], item['drug_name'], item['cancer_type']))
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
                
    if top_updates:
        for upd in top_updates:
            st.markdown(f"- **{upd[1]}**: {upd[2]} ({upd[3]})")
    else:
        st.info("尚無更新資訊")
        
    st.divider()

    # 1. Select Drug Name
    # Extract unique drug names
    all_drugs = sorted(list(set(item['drug_name'] for item in data)))
    
    # Search filter
    search_term = st.text_input("🔍 搜尋藥名或關鍵字", placeholder="輸入藥名關鍵字...")
    
    if search_term:
        filtered_drugs = [drug for drug in all_drugs if search_term.lower() in drug.lower()]
    else:
        filtered_drugs = all_drugs

    if not filtered_drugs:
        st.warning("查無符合的藥物 (No matching drugs found).")
        selected_drug = None
    else:
        selected_drug = st.selectbox("💊 Select Drug Name", filtered_drugs)

    # 2. Select Cancer Type
    selected_cancer = None
    if selected_drug:
        # Filter cancer types based on selected drug
        available_cancers = sorted(list(set(
            item['cancer_type'] for item in data if item['drug_name'] == selected_drug
        )))
        selected_cancer = st.selectbox("🎗️ Select Cancer Type", available_cancers)

    # 3. Display Regulation
    if selected_drug and selected_cancer:
        st.divider()
        st.subheader(f"📋 Regulation for {selected_drug} - {selected_cancer}")
        
        # Find the matching regulation
        # (In a real app, might want to handle multiple matches, but here we assume unique pairs)
        regulation_text = next(
            (item['regulation'] for item in data 
             if item['drug_name'] == selected_drug and item['cancer_type'] == selected_cancer), 
            "No regulation found for this combination."
        )
        
        st.info(regulation_text)

if __name__ == "__main__":
    main()
