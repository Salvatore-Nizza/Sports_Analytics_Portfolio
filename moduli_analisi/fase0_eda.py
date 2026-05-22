import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats
import plotly.graph_objects as go

def create_eda_profile(df, table_name):
    st.subheader("🔍 Exploratory Data Analysis (EDA)")
    st.caption(f"Currently analyzing SQL Table: `{table_name}`")
    
    # ---------------------------------------------------------
    # 1. HIGH-LEVEL METRICS & PREVIEW (COMPACT LAYOUT)
    # ---------------------------------------------------------
    col_title, col_rows, col_cols = st.columns([2, 1, 1])
    with col_title:
        st.markdown("#### 📄 Data Preview")
    with col_rows:
        st.metric("Total Rows", df.shape[0])
    with col_cols:
        st.metric("Total Columns", df.shape[1])
        
    st.dataframe(df.head(50), use_container_width=True)
    st.markdown("---")
    
    # ---------------------------------------------------------
    # 2. CATEGORICAL ENCODING & LEGEND
    # ---------------------------------------------------------
    st.markdown("#### 🔠 Categorical Variables Encoding")
    st.write("Machine Learning models require numerical inputs. Here is the encoded version of your text-based categorical variables.")
    
    cat_cols = df.select_dtypes(include=['object', 'bool', 'category']).columns.tolist()
    
    if len(cat_cols) > 0:
        df_encoded = df.copy()
        mapping_legend = {}
        
        # Encoding categoricals and building the legend mapping
        for col in cat_cols:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            # Create a dictionary pairing the original string with its new integer value
            mapping_legend[col] = {str(class_label): int(encoded_val) for class_label, encoded_val in zip(le.classes_, le.transform(le.classes_))}
            
        with st.expander("Show Encoded Categorical Dataset & Legend"):
            st.write("**Encoding Legend (Mapping):**")
            st.json(mapping_legend) # Displays the legend beautifully
            st.dataframe(df_encoded[cat_cols].head(100), use_container_width=True)
    else:
        st.info("No categorical variables found in this dataset.")
        df_encoded = df.copy()

    st.markdown("---")

    # ---------------------------------------------------------
    # 3. TARGET VARIABLE ANALYSIS
    # ---------------------------------------------------------
    st.markdown("#### 🎯 Target Variable Analysis")
    target_col = st.selectbox("Select your Target Variable:", df.columns)
    
    tab_dist, tab_group, tab_pair = st.tabs(["📊 Distribution & Counts", "🧮 Grouped Stats", "🔗 Pairplot (Scatter Matrix)"])
    
    # --- A. Distribution (Distplot) & Countplot ---
    with tab_dist:
        st.write(f"**Distribution and Value Counts of `{target_col}`**")
        col_dist, col_count = st.columns(2)
        
        with col_dist:
            # Distplot (Histogram with marginal boxplot)
            fig_dist = px.histogram(df, x=target_col, marginal="box", color_discrete_sequence=['#00B4D8'], title="Distribution Plot")
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with col_count:
            # Countplot (Bar chart of frequencies)
            counts = df[target_col].value_counts().reset_index()
            counts.columns = [target_col, 'Count']
            fig_count = px.bar(counts, x=target_col, y='Count', color_discrete_sequence=['#E03A3E'], title="Count Plot")
            st.plotly_chart(fig_count, use_container_width=True)
        
    # --- B. Grouped Statistics ---
    with tab_group:
        st.write(f"**Dataset Aggregation based on `{target_col}`**")
        agg_metrics = st.multiselect("Select Statistics:", ["mean", "median", "min", "max", "std"], default=["mean", "median"])
        num_cols = df.select_dtypes(include=np.number).columns.drop(target_col, errors='ignore')
        
        # Hide the dataframe completely if no metric is selected
        if len(num_cols) > 0 and len(agg_metrics) > 0:
            grouped_df = df.groupby(target_col)[num_cols].agg(agg_metrics)
            st.dataframe(grouped_df, use_container_width=True)
        elif len(agg_metrics) == 0:
            pass # Does not show anything, as requested
        else:
            st.warning("Please select at least one numeric feature.")
            
    # --- C. Pairplot / Scatter Matrix ---
    with tab_pair:
        st.write("**Feature Correlation relative to Target**")
        st.caption("Select features. The target variable is highlighted. Diagonal self-correlation is removed.")
        num_cols_list = df.select_dtypes(include=np.number).columns.tolist()
        
        pair_features = st.multiselect("Select features for Pairplot:", num_cols_list, default=num_cols_list[:min(4, len(num_cols_list))])
        
        if len(pair_features) > 1:
            fig_pair = px.scatter_matrix(df, dimensions=pair_features, color=target_col, opacity=0.7)
            # Remove self-correlation on the diagonal
            fig_pair.update_traces(diagonal_visible=False)
            fig_pair.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pair, use_container_width=True)
        else:
            st.info("Select at least 2 features to generate a Pairplot.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. OUTLIER DETECTION & TREATMENT (BOXPLOTS)
    # ---------------------------------------------------------
    st.markdown("#### 🚨 Outlier Detection & Treatment")
    
    num_cols_only = df.select_dtypes(include=np.number).columns.tolist()
    outlier_feature = st.selectbox("Select numerical feature to analyze for outliers:", num_cols_only)
    
    col_method, col_action = st.columns(2)
    with col_method:
        outlier_method = st.selectbox(
            "Statistical Method:", 
            ["None", "Z-Score (Standard Deviation)", "Tukey's Fences (IQR)", "Local Outlier Factor (LOF)"]
        )
    with col_action:
        outlier_action = st.radio("Action:", ["Highlight Only", "Remove Outliers (Clean Dataset)"])

    if outlier_method != "None" and outlier_feature:
        outliers_mask = pd.Series(False, index=df.index)
        temp_data = df[outlier_feature].dropna()
        
        # 1. Z-SCORE METHOD
        if outlier_method == "Z-Score (Standard Deviation)":
            z_scores = np.abs(stats.zscore(temp_data))
            outliers_mask.loc[temp_data.index] = z_scores > 3
            
        # 2. TUKEY'S FENCES (IQR)
        elif outlier_method == "Tukey's Fences (IQR)":
            Q1 = temp_data.quantile(0.25)
            Q3 = temp_data.quantile(0.75)
            IQR = Q3 - Q1
            outliers_mask.loc[temp_data.index] = (temp_data < (Q1 - 1.5 * IQR)) | (temp_data > (Q3 + 1.5 * IQR))
            
        # 3. LOCAL OUTLIER FACTOR (LOF)
        elif outlier_method == "Local Outlier Factor (LOF)":
            lof = LocalOutlierFactor(n_neighbors=20, contamination='auto')
            preds = lof.fit_predict(temp_data.values.reshape(-1, 1))
            outliers_mask.loc[temp_data.index] = preds == -1
            
        total_outliers = outliers_mask.sum()
        
        if total_outliers > 0:
            st.error(f"⚠️ Detected **{total_outliers}** outliers using {outlier_method}.")
            
            # Map the mask to specific labels for the legend
            df_plot = df.copy()
            df_plot['Outlier'] = outliers_mask.map({True: 'Outlier', False: 'Normal'})
            
            if outlier_action == "Highlight Only":
                # --- NUOVA STRATEGIA: BOXPLOT NATIVO STANDARD + SOVRAPPOSIZIONE CUSTOM ---
                fig_out = go.Figure()

                # Livello 1: Boxplot NATIVO STANDARD
                # Mostra solo i baffi nativi e i punti nativi (standard di Tukey), senza i punti della scatola
                fig_out.add_trace(go.Box(
                    y=df_plot[outlier_feature],
                    name="Distribuzione Generale",
                    boxpoints='outliers', # Fondamentale: mostra solo gli outlier nativi outside standard whiskers
                    # marker_color: colore della scatola e median
                    marker_color='#00B4D8',
                    line_color='#0077B6'
                ))

                # Filtriamo i tuoi specifici outlier calcolati
                outliers_df = df_plot[df_plot['Outlier'] == 'Outlier']

                # Livello 2: Sovrapponiamo i TUOI OUTLIER SPECIFICI (colorati in rosso)
                if not outliers_df.empty:
                    fig_out.add_trace(go.Scatter(
                        x=["Distribuzione Generale"] * len(outliers_df), # Stessa X per allineamento
                        y=outliers_df[outlier_feature],
                        mode='markers',
                        marker=dict(color='red', size=8, line=dict(width=1, color='darkred')),
                        name='I tuoi Outliers'
                    ))

                # Miglioriamo il layout generale
                fig_out.update_layout(
                    title=f"Boxplot con Outliers Sovrapposti (Baffi Standard): {outlier_feature}",
                    yaxis_title=outlier_feature,
                    showlegend=True,
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig_out, use_container_width=True)
                
        else:
            st.success(f"✅ No outliers detected using {outlier_method}.")