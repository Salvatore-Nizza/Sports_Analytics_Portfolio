import streamlit as st
import pandas as pd
import plotly.express as px

def create_player_profile(df, data_source):
    st.subheader("👤 Player Scouting Profile")
    
    # 1. COMPATIBILITY CHECK
    if data_source != "Statsbomb":
        st.warning("⚠️ Player profiling requires Event Data. Please select a 'Statsbomb' table from the sidebar.")
        return
        
    if 'player' not in df.columns or 'type' not in df.columns:
        st.error("Error: Missing 'player' or 'type' columns in this dataset.")
        return

    # 2. PLAYER SELECTION
    available_players = sorted(df['player'].dropna().unique())
    selected_player = st.selectbox("🔍 Search and Select a Player:", available_players)
    
    st.markdown("---")
    
    # Filter dataset for the selected player
    player_df = df[df['player'] == selected_player]
    
    # 3. BASE METRICS CALCULATION
    total_events = len(player_df)
    passes = len(player_df[player_df['type'] == 'Pass'])
    shots = len(player_df[player_df['type'] == 'Shot'])
    dribbles = len(player_df[player_df['type'] == 'Dribble'])
    tackles = len(player_df[player_df['type'] == 'Tackle'])
    
    # Dashboard Metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("⚡ Total Actions", total_events)
    col2.metric("👟 Passes", passes)
    col3.metric("🎯 Shots", shots)
    col4.metric("🏃‍♂️ Dribbles", dribbles)
    col5.metric("🛡️ Tackles", tackles)
    
    st.markdown("---")
    
    # 4. SCOUTING RADAR CHART
    st.markdown("#### 🕸️ Playing Style Radar")
    
    # Gathering advanced metrics for the Radar Chart
    interceptions = len(player_df[player_df['type'] == 'Interception'])
    clearances = len(player_df[player_df['type'] == 'Clearance'])
    fouls_won = len(player_df[player_df['type'] == 'Foul Won'])
    aerials = len(player_df[player_df['type'] == 'Duel']) # Assuming duels for broadness
    
    # Create the DataFrame for Plotly
    radar_data = pd.DataFrame(dict(
        Volume=[passes, shots, dribbles, tackles, interceptions, clearances, fouls_won],
        Metric=['Passes', 'Shots', 'Dribbles', 'Tackles', 'Interceptions', 'Clearances', 'Fouls Won']
    ))
    
    # Plotly Radar Chart
    fig = px.line_polar(
        radar_data, 
        r='Volume', 
        theta='Metric', 
        line_close=True,
        markers=True,
        title=f"Statistical Footprint: {selected_player}"
    )
    
    fig.update_traces(fill='toself', line_color='#00B4D8') 
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showticklabels=True),
            angularaxis=dict(linewidth=1, showline=True)
        ),
        margin=dict(l=40, r=40, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Next Steps Placeholder (To be built from your PDF courses!)
    st.caption("🔜 *Coming Soon: Pitch Heatmap & xG Data (Expected Goals) based on advanced course modules.*")