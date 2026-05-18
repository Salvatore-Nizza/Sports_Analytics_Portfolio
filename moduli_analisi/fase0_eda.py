import streamlit as st
import pandas as pd
import plotly.express as px

def create_eda_profile(df, table_name):
    st.subheader("🔍 Exploratory Data Analysis (EDA)")
    st.caption(f"Currently analyzing SQL Table: `{table_name}`")
    
    # 1. HIGH-LEVEL METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows (Records)", df.shape[0])
    col2.metric("Total Columns (Features)", df.shape[1])
    missing_total = df.isna().sum().sum()
    col3.metric("Total Missing Values", missing_total)
    
    st.markdown("---")
    
    # 2. DATA PREVIEW
    st.markdown("#### 📄 Data Preview (First 100 Rows)")
    st.dataframe(df.head(100), use_container_width=True)
    
    st.markdown("---")
    
    # 3. STRUCTURAL & STATISTICAL SUMMARY
    col_struct, col_stats = st.columns(2)
    
    with col_struct:
        st.markdown("#### 🛠️ Data Types & Missing Info")
        # Create a summary DataFrame for missing values and types
        summary_df = pd.DataFrame({
            'Data Type': df.dtypes.astype(str),
            'Missing Values': df.isna().sum(),
            '% Missing': (df.isna().sum() / len(df) * 100).round(2)
        })
        st.dataframe(summary_df, use_container_width=True)
        
    with col_stats:
        st.markdown("#### 📊 Statistical Summary")
        # Filter only numerical columns for the describe() function
        num_df = df.select_dtypes(include=['float64', 'int64'])
        if not num_df.empty:
            st.dataframe(num_df.describe().T, use_container_width=True)
        else:
            st.info("No numerical columns available for statistical summary.")
            
    st.markdown("---")
    
    # 4. CORRELATION MATRIX (HEATMAP)
    st.markdown("#### 🌡️ Feature Correlation Matrix")
    st.write("Displays the linear relationship between numerical features. Values near 1 or -1 indicate strong correlation.")
    
    if not num_df.empty and len(num_df.columns) > 1:
        # Calculate correlation matrix
        corr_matrix = num_df.corr().round(2)
        
        # Create an interactive heatmap using Plotly
        fig = px.imshow(
            corr_matrix, 
            text_auto=True, 
            aspect="auto", 
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1
        )
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Not enough numerical features to generate a correlation matrix.")