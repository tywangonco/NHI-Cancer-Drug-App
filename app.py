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
    # Sidebar: File Upload
    st.sidebar.title("🔧 Settings")
    st.sidebar.markdown("[🔗 健保署給付規定下載頁面](https://www.nhi.gov.tw/ch/cp-7593-ad2a9-3397-1.html)")
    uploaded_file = st.sidebar.file_uploader("📂 上傳最新的給付規定 (DOCX)", type=['docx'])
    
    if uploaded_file is not None:
        temp_path = "temp_regulations.docx"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Processing file..."):
            # Update Database
            raw_data = converter.parse_docx(temp_path)
            final_data = converter.classify_and_format(raw_data)
            
            with open('nhi_data.json', 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            # Clean up temp file
            os.remove(temp_path)
            
            # Clear cache and reload
            st.cache_data.clear()
            st.sidebar.success("資料庫已更新！ (Database updated!)")
            st.rerun()

    st.title("🏥 Cancer Drug Payment Regulations")
    st.markdown("Select a drug and cancer type to view the specific NHI payment regulations.")

    # Load data
    data = load_data()
    
    if data is None:
        st.error("Error: `nhi_data.json` not found. Please ensure the data file is in the same directory.")
        st.stop()

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
