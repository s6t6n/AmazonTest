import streamlit as st
import pandas as pd
import io

# 1. Configuration & Amazon FR Mappings
VALID_POSITIONS = {"Front": "Avant", "Rear": "Arrière", "Front and Rear": "Avant et arrière"}

def validate_data(df):
    logs = []
    is_valid = True
    
    for idx, row in df.iterrows():
        # EAN Check
        ean = str(row.get('EAN', ''))
        if len(ean) != 13:
            logs.append(f"❌ Row {idx+1}: Invalid EAN '{ean}' (Must be 13 digits)")
            is_valid = False
            
        # Position Check
        pos = row.get('Position', '')
        if pos not in VALID_POSITIONS:
            logs.append(f"⚠️ Row {idx+1}: Position '{pos}' not recognized. Defaulting to 'Avant'.")
            
    return is_valid, logs

st.set_page_config(page_title="Amazon FR Brake Injector", layout="wide")
st.title("🚗 Amazon France : Injecteur de Freins")

# UI Sidebar
st.sidebar.header("Source de Données")
uploaded_file = st.sidebar.file_uploader("Upload Database Export (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.write("### Preview of your Data", df.head(5))
    
    if st.button("🛠️ Process & Validate for Amazon.fr"):
        st.divider()
        st.subheader("📋 Processing Logs")
        
        # Start Log Console
        log_container = st.empty()
        with st.status("Validating data for Amazon France standards...") as status:
            success, error_logs = validate_data(df)
            for log in error_logs:
                st.write(log)
            
            if not success:
                status.update(label="Validation Failed. Please fix errors.", state="error")
            else:
                status.update(label="Validation Successful!", state="complete")
                
                # --- FILE 1: LISTING FILE (The Product Page) ---
                listing_df = pd.DataFrame({
                    "feed_product_type": "auto-part",
                    "item_sku": df['SKU'],
                    "external_product_id": df['EAN'],
                    "external_product_id_type": "EAN",
                    "item_name": df['Title_FR'],
                    "brand_name": df['Brand'],
                    "standard_price": df['Price'],
                    "quantity": df['Qty'],
                    "main_image_url": df['Image_URL'],
                    "position_placement": df['Position'].map(VALID_POSITIONS).fillna("Avant"),
                    "bullet_point1": "Qualité OE garantie",
                    "item_weight": df['Weight'],
                    "item_weight_unit_of_measure": "GR"
                })

                # --- FILE 2: FITMENT FILE (K-Types) ---
                # This assumes 'KTypes' column is comma-separated like "123,456,789"
                fitment_data = []
                for _, row in df.iterrows():
                    kts = str(row['KTypes']).split(',')
                    for k in kts:
                        fitment_data.append({"SKU": row['SKU'], "K-Type": k.strip()})
                fitment_df = pd.DataFrame(fitment_data)

                st.success(f"Successfully processed {len(df)} products and {len(fitment_df)} vehicle links!")

                # Download Buttons
                col1, col2 = st.columns(2)
                
                # Buffer for Excel
                buf1 = io.BytesIO()
                with pd.ExcelWriter(buf1, engine='xlsxwriter') as writer:
                    listing_df.to_excel(writer, index=False, sheet_name='Template')
                
                buf2 = io.BytesIO()
                with pd.ExcelWriter(buf2, engine='xlsxwriter') as writer:
                    fitment_df.to_excel(writer, index=False, sheet_name='Fitment')

                col1.download_button("📥 Download Listing File", buf1.getvalue(), "Amazon_FR_Brakes.xlsx", "application/vnd.ms-excel")
                col2.download_button("📥 Download Fitment File", buf2.getvalue(), "Amazon_FR_Fitment.xlsx", "application/vnd.ms-excel")