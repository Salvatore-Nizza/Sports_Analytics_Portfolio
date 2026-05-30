import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats

def create_eda_profile(df, table_name):
    st.subheader("🔍 Exploratory Data Analysis (EDA)")
    st.caption(f"Currently analyzing SQL Table: `{table_name}`")
    
    # ---------------------------------------------------------
    # 1. HIGH-LEVEL METRICS & PREVIEW
    # ---------------------------------------------------------
    col_title, col_rows, col_cols = st.columns([2, 1, 1])
    with col_title:
        st.markdown("#### 📄 Data Preview & Structure")
    with col_rows:
        st.metric("Total Rows", df.shape[0])
    with col_cols:
        st.metric("Total Columns", df.shape[1])
        
    tab_data, tab_info = st.tabs(["Raw Data", "Column Data Types & Missing Values"])
    
    with tab_data:
        st.dataframe(df.head(50), use_container_width=True)
        
    with tab_info:
        info_df = pd.DataFrame({
            'Data Type': df.dtypes.astype(str),
            'Missing Values (NaN)': df.isnull().sum(),
            '% Missing': (df.isnull().sum() / len(df) * 100).round(2).astype(str) + '%'
        })
        st.dataframe(info_df, use_container_width=True)
        
    st.markdown("---")
    
    # ---------------------------------------------------------
    # 2. CATEGORICAL ENCODING & LEGEND
    # ---------------------------------------------------------
    st.markdown("#### 🔠 Categorical Variables Encoding & Imputation")
    st.write("Machine Learning models require numerical inputs without missing values. Select a categorical variable to view its encoding mapping and imputation strategy.")
    
    cat_cols = df.select_dtypes(include=['object', 'bool', 'category']).columns.tolist()
    
    if len(cat_cols) > 0:
        df_encoded = df.copy()
        mapping_legend = {}
        
        # --- SMART IMPUTATION & ENCODING LOOP ---
        for col in cat_cols:
            # 1. Smart Boolean Imputation: If a column contains True/False or 1/0 logic with NaNs
            # We assume NaNs mean False (event didn't happen) and convert to 1/0.
            unique_vals = [str(x).lower() for x in df[col].dropna().unique()]
            if 'true' in unique_vals or 'false' in unique_vals:
                # Fill blanks with False
                df_encoded[col] = df_encoded[col].fillna(False)
                # Ensure the column is boolean, then convert to integer (True=1, False=0)
                # We use mapping to be perfectly safe against weird string formats like "True" vs True
                df_encoded[col] = df_encoded[col].map({True: 1, False: 0, 'True': 1, 'False': 0, 1: 1, 0: 0, '1': 1, '0': 0}).fillna(0).astype(int)
                
                # Manually set the legend for these boolean columns
                mapping_legend[col] = {"True": 1, "False": 0}
                
            else:
                # 2. Standard Categorical Imputation: Fill blanks with 'Unknown'
                df_encoded[col] = df_encoded[col].fillna("Unknown")
                
                # Standard Label Encoding
                le = LabelEncoder()
                df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
                mapping_legend[col] = {str(class_label): int(encoded_val) for class_label, encoded_val in zip(le.classes_, le.transform(le.classes_))}
            
        # --- INTERACTIVE VIEWER ---
        selected_cat = st.selectbox("Select a categorical variable to inspect:", cat_cols)
        
        col_map, col_sample = st.columns(2)
        with col_map:
            st.write(f"**Encoding Map for `{selected_cat}`:**")
            st.json(mapping_legend[selected_cat])
            
        with col_sample:
            st.write("**Data Comparison (First 15 rows):**")
            comparison_df = pd.DataFrame({
                "Original (Raw)": df[selected_cat].astype(str).head(15),
                "Encoded (Clean)": df_encoded[selected_cat].head(15)
            })
            st.dataframe(comparison_df, use_container_width=True)
            
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
    # --- A. Distribution (Distplot) & Countplot ---
    with tab_dist:
        st.write(f"**Distribution and Value Counts of `{target_col}`**")
        
        # 1. Detect if the selected variable is categorical using the official list
        is_categorical = target_col in cat_cols
        
        # 2. Show notification and switch to encoded data if needed
        if is_categorical:
            st.info("ℹ️ Categorical variable detected. Displaying charts using its numerically encoded version.")
            plot_df = df_encoded
        else:
            plot_df = df

        col_dist, col_count = st.columns(2)
        
        with col_dist:
            # Distribution Plot (Histogram)
            fig_dist = px.histogram(
                plot_df, 
                x=target_col, 
                nbins=50 if not is_categorical else None, # Let Plotly handle bins naturally for categories
                color_discrete_sequence=['#00B4D8'], 
                title="Distribution Plot"
            )
            
            # Force linear axis ONLY for continuous numerical data
            if not is_categorical:
                fig_dist.update_layout(xaxis_type='linear')
                
            fig_dist.update_layout(bargap=0.05)
            fig_dist.update_traces(marker_line_width=0)
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with col_count:
            # Group decimals for highly continuous numeric data, otherwise do standard counts
            if pd.api.types.is_numeric_dtype(plot_df[target_col]) and plot_df[target_col].nunique() > 30 and not is_categorical:
                counts = plot_df[target_col].round(2).value_counts().reset_index()
            else:
                counts = plot_df[target_col].value_counts().reset_index()
                
            counts.columns = [target_col, 'Count']
            
            # Count Plot (Bar chart of frequencies)
            fig_count = px.bar(
                counts, 
                x=target_col, 
                y='Count', 
                color_discrete_sequence=['#E03A3E'], 
                title="Count Plot (Frequency)"
            )
            
            # Force linear axis ONLY for continuous numerical data
            if not is_categorical:
                fig_count.update_layout(xaxis_type='linear')
                
            fig_count.update_layout(bargap=0.05)
            fig_count.update_traces(marker_line_width=0)
            
            st.plotly_chart(fig_count, use_container_width=True)
        
    # --- B. Grouped Statistics ---
    with tab_group:
        st.write(f"**Dataset Aggregation based on `{target_col}`**")
        agg_metrics = st.multiselect("Select Statistics:", ["mean", "median", "min", "max", "std"], default=["mean", "median"])
        num_cols = df.select_dtypes(include=np.number).columns.drop(target_col, errors='ignore')
        
        if len(num_cols) > 0 and len(agg_metrics) > 0:
            grouped_df = df.groupby(target_col)[num_cols].agg(agg_metrics)
            st.dataframe(grouped_df, use_container_width=True)
        elif len(agg_metrics) == 0:
            pass 
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
            
            df_plot = df.copy()
            df_plot['Outlier'] = outliers_mask.map({True: 'Outlier', False: 'Normal'})
            
            if outlier_action == "Highlight Only":
                # NATIVE BOXPLOT + CUSTOM OVERLAY STRATEGY
                fig_out = go.Figure()

                # Layer 1: Native Standard Boxplot
                fig_out.add_trace(go.Box(
                    y=df_plot[outlier_feature],
                    name="General Distribution",
                    boxpoints='outliers', 
                    marker_color='#00B4D8',
                    line_color='#0077B6'
                ))

                # Filter custom calculated outliers
                outliers_df = df_plot[df_plot['Outlier'] == 'Outlier']

                # Layer 2: Overlay custom outliers in red
                if not outliers_df.empty:
                    fig_out.add_trace(go.Scatter(
                        x=["General Distribution"] * len(outliers_df), 
                        y=outliers_df[outlier_feature],
                        mode='markers',
                        marker=dict(color='red', size=8, line=dict(width=1, color='darkred')),
                        name='Custom Outliers'
                    ))

                fig_out.update_layout(
                    title=f"Boxplot Highlighting Outliers (Standard Whiskers): {outlier_feature}",
                    yaxis_title=outlier_feature,
                    showlegend=True,
                    template="plotly_dark"
                )
                
                st.plotly_chart(fig_out, use_container_width=True)
                
            elif outlier_action == "Remove Outliers (Clean Dataset)":
                df_clean = df_plot[~outliers_mask]
                st.success(f"✅ Outliers removed. New dataset shape: {df_clean.shape}")
                
                fig_compare = px.box(
                    df_clean, 
                    y=outlier_feature, 
                    color='Outlier',
                    color_discrete_map={"Normal": "#00B4D8"},
                    title=f"Cleaned Boxplot for {outlier_feature} (Outliers Removed)"
                )
                fig_compare.update_layout(legend_title_text='Outlier')
                st.plotly_chart(fig_compare, use_container_width=True)
                
        else:
            st.success(f"✅ No outliers detected using {outlier_method}.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 5. FEATURE SELECTION
    # ---------------------------------------------------------
    st.markdown("#### 🧲 Feature Selection")
    st.write("Evaluate the importance of variables relative to your **Target** to select only the most significant data and avoid unnecessary analysis.")

    # 1. Copy encoded data and fill NaNs with 0
    df_fs = df_encoded.copy()
    df_fs = df_fs.fillna(0)
    
    # 2. Strict filtering: keep ONLY numerical columns
    df_fs = df_fs.select_dtypes(include=[np.number])

    # 3. Smart Diagnostics
    if target_col not in df_fs.columns:
        st.warning(f"⚠️ Safety Lock: Your Target '{target_col}' does not appear to be numerical or was filtered out. Please select a valid Target in Section 3.")
    elif df_fs.shape[0] == 0:
        st.warning("⚠️ Safety Lock: The dataset has 0 rows.")
    elif df_fs.shape[1] < 2:
        st.warning(f"⚠️ Safety Lock: There are only {df_fs.shape[1]} numerical columns, which is insufficient for feature comparison.")
    else:
        # Split Features (X) and Target (y)
        X = df_fs.drop(columns=[target_col])
        y = df_fs[target_col]

        col_fs_method, col_fs_params = st.columns([2, 1])
        with col_fs_method:
            fs_method = st.selectbox(
                "Feature Selection Method:",
                ["None",
                 "Univariate Selection (SelectKBest)",
                 "Recursive Feature Elimination (RFE)",
                 "Model-Based Selection (Lasso)",
                 "Tree-Based Selection (Random Forest)",
                 "Feature Importance (Extra Trees)"]
            )

        if fs_method != "None":
            st.markdown("---")
            
            try:
                # -------------------------------------------------
                # 1. UNIVARIATE SELECTION
                # -------------------------------------------------
                if fs_method == "Univariate Selection (SelectKBest)":
                    with col_fs_params:
                        k_val = st.number_input("Number of features (k):", min_value=1, max_value=len(X.columns), value=min(5, len(X.columns)))
                    
                    from sklearn.feature_selection import SelectKBest, f_classif
                    selector = SelectKBest(score_func=f_classif, k=k_val)
                    selector.fit(X, y)
                    
                    scores_df = pd.DataFrame({'Feature': X.columns, 'Score': selector.scores_})
                    scores_df = scores_df.dropna().sort_values(by='Score', ascending=False).head(k_val)
                    
                    fig_uni = px.bar(scores_df, x='Score', y='Feature', orientation='h', 
                                     title=f"Top {k_val} Features (SelectKBest)", color_discrete_sequence=['#00B4D8'])
                    fig_uni.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_uni, use_container_width=True)

                # -------------------------------------------------
                # 2. RECURSIVE FEATURE ELIMINATION (RFE)
                # -------------------------------------------------
                elif fs_method == "Recursive Feature Elimination (RFE)":
                    with col_fs_params:
                        k_val = st.number_input("Features to keep:", min_value=1, max_value=len(X.columns), value=min(3, len(X.columns)))
                    
                    from sklearn.feature_selection import RFE
                    from sklearn.linear_model import LogisticRegression
                    
                    with st.spinner("Calculating RFE..."):
                        estimator = LogisticRegression(max_iter=2000)
                        selector = RFE(estimator, n_features_to_select=k_val)
                        selector.fit(X, y)
                        
                        selected_features = X.columns[selector.support_]
                        st.success(f"✅ RFE isolated the top **{k_val}** features:")
                        st.write(list(selected_features))

                # -------------------------------------------------
                # 3. MODEL-BASED (LASSO)
                # -------------------------------------------------
                elif fs_method == "Model-Based Selection (Lasso)":
                    from sklearn.feature_selection import SelectFromModel
                    from sklearn.linear_model import Lasso
                    
                    with st.spinner("Training Lasso model..."):
                        estimator = Lasso(alpha=0.1)
                        selector = SelectFromModel(estimator)
                        selector.fit(X, y)
                        
                        selected_features = X.columns[selector.get_support()]
                        if len(selected_features) > 0:
                            st.success(f"✅ The Lasso model kept **{len(selected_features)}** features (others were zeroed out):")
                            st.write(list(selected_features))
                        else:
                            st.warning("The Lasso model zeroed out all coefficients. Try a different method.")

                # -------------------------------------------------
                # 4. TREE-BASED SELECTION (RANDOM FOREST)
                # -------------------------------------------------
                elif fs_method == "Tree-Based Selection (Random Forest)":
                    from sklearn.feature_selection import SelectFromModel
                    from sklearn.ensemble import RandomForestClassifier
                    
                    with st.spinner("Training Random Forest..."):
                        estimator = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
                        selector = SelectFromModel(estimator)
                        selector.fit(X, y)
                        
                        selected_features = X.columns[selector.get_support()]
                        st.success(f"✅ Random Forest suggests these **{len(selected_features)}** features:")
                        st.write(list(selected_features))

                # -------------------------------------------------
                # 5. FEATURE IMPORTANCE (EXTRA TREES)
                # -------------------------------------------------
                elif fs_method == "Feature Importance (Extra Trees)":
                    from sklearn.ensemble import ExtraTreesClassifier
                    
                    with st.spinner("Calculating importances..."):
                        model = ExtraTreesClassifier(n_estimators=50, random_state=42)
                        model.fit(X, y)
                        
                        importances = pd.DataFrame({'Feature': X.columns, 'Importance': model.feature_importances_})
                        importances = importances.sort_values(by='Importance', ascending=False).head(10)
                        
                        fig_imp = px.bar(importances, x='Importance', y='Feature', orientation='h', 
                                         title="Top 10 Feature Importances (ExtraTrees)", color_discrete_sequence=['#E03A3E'])
                        fig_imp.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_imp, use_container_width=True)
                        
            except Exception as e:
                st.error(f"⚠️ **Statistical Error:** The method failed. Technical details: `{str(e)}`")
                st.info("💡 **Why did this happen?** Many of these methods (e.g., Logistic Regression, f_classif) are designed for **Classification** problems (e.g., Target = Win/Loss). If your Target variable is continuous (e.g., Distance Covered), the algorithm may fail to process the data.")