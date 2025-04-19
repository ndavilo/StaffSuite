import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(__file__))
import face_utils
from styles import LAGOS_STYLE, get_header_style, get_topbar_style, image_to_base64
import check_requirements

# MUST be the first Streamlit command
st.set_page_config(
    page_title='EFCC StaffSuite',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Apply custom styling
st.markdown(LAGOS_STYLE, unsafe_allow_html=True)
st.markdown(get_header_style(), unsafe_allow_html=True)
st.markdown(get_topbar_style(), unsafe_allow_html=True)

# Create the top bar
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-content">
        <div class="top-bar-logo">
            <img src="data:image/png;base64,{image_to_base64("EFCC1.png")}" width="40" style="filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));">
        </div>
        <div class="top-bar-title">EFCC StaffSuite</div>
    </div>
</div>
<div class="main-content">
""", unsafe_allow_html=True)

def display_header():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="logo-container">
        <img src="data:image/png;base64,{image_to_base64('EFCC1.png')}" 
             width="180" 
             style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <p class="header-title">
            ECONOMIC AND FINANCIAL CRIMES COMMISSION
        </p>
        <p class="header-subtitle" style="margin-bottom: 0.5rem;">
            Department of Information and Communication Technology
        </p>
        <p class="header-subtitle">
            Lagos Zonal Directorate 2 [Okotie-Eboh Office]
        </p>
    </div>
    <div style="margin: 2rem 0;">
        <h2 class="app-title" style="margin-bottom: 0.5rem;">EFCC StaffSuite</h2>
        <p class="app-slogan">
            Efficient Workforce Tracking at Your Fingertips
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_network_alert():
    """Displays a clean network access required message"""
    st.error("""
    **Network Access Required**  
    You must be connected to the EFCC office network to use this application.
    
    **To resolve:**  
    1. Connect to EFCC WiFi or wired network  
    2. Ensure your device is authorized  
    3. Refresh this page  
    
    For assistance, contact ICT Support at extension 5050
    """)

def load_data_from_redis():
    name = 'attendance:logs'
    logs = face_utils.load_logs(name=name)
    cleaned_logs = []
    for log in logs:
        if isinstance(log, bytes):
            log = log.decode('utf-8')
        log = log.strip("b'")
        parts = log.split('@')
        if len(parts) == 4:
            file_name_role, role, timestamp, Clock_In_Out = parts
            file_no, name = file_name_role.split('.', 1)
            cleaned_logs.append({
                'File No.': file_no,
                'Name': name,
                'Role': role,
                'Timestamp': timestamp,
                'Clock_In_Out': Clock_In_Out
            })

    if not cleaned_logs:
        return pd.DataFrame()

    df = pd.DataFrame(cleaned_logs)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Date'] = df['Timestamp'].dt.date
    df['Time'] = df['Timestamp'].dt.time
    df['Hour'] = df['Timestamp'].dt.hour
    df['Day'] = df['Timestamp'].dt.day_name()
    return df

def main():
    # Always show the header
    display_header()

    # Check network access after showing header
    access_granted, _ = check_requirements.ip_address_range_verification()
    if not access_granted:
        show_network_alert()
        st.stop()

    # Rest of the application for authorized users
    with st.spinner('Loading attendance data from Redis...'):
        df = load_data_from_redis()

    if df.empty:
        st.warning("No attendance data found in Redis database")
        st.stop()

    st.subheader('Attendance Visualization Dashboard')

    # Sidebar filters
    st.sidebar.header('Filter Options')
    selected_roles = st.sidebar.multiselect(
        'Select Roles', 
        options=df['Role'].unique(), 
        default=df['Role'].unique(),
        help="Filter by staff roles"
    )
    
    date_range = st.sidebar.date_input(
        'Select Date Range',
        value=[df['Date'].min(), df['Date'].max()],
        min_value=df['Date'].min(),
        max_value=df['Date'].max(),
        help="Select date range for analysis"
    )

    # Filter data
    filtered_df = df[(df['Role'].isin(selected_roles)) & (df['Date'] >= date_range[0]) & (df['Date'] <= date_range[1])]
    
    st.write(f"Displaying data from {date_range[0]} to {date_range[1]}")

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(filtered_df))
    with col2:
        st.metric("Unique Employees", filtered_df['Name'].nunique())
    with col3:
        st.metric("Date Range", f"{filtered_df['Date'].min()} to {filtered_df['Date'].max()}")

    # Tabs for different views
    tab1, tab3 = st.tabs(["Daily Activity", "Hourly Trends"])

    with tab1:
        st.subheader("Daily Attendance Activity")
        if not filtered_df.empty:
            daily_counts = filtered_df.groupby(['Date', 'Clock_In_Out']).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(10, 6))
            daily_counts.plot(kind='bar', stacked=True, ax=ax)
            plt.title('Daily Clock-Ins and Clock-Outs')
            plt.xlabel('Date')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            st.pyplot(fig)

            st.subheader("Activity by Day of Week")
            day_counts = filtered_df.groupby(['Day', 'Clock_In_Out']).size().unstack(fill_value=0)
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = day_counts.reindex(day_order)
            fig, ax = plt.subplots(figsize=(10, 4))
            day_counts.plot(kind='bar', stacked=True, ax=ax)
            plt.title('Activity by Day of Week')
            plt.xlabel('Day')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.warning("No data available for selected filters")

    with tab3:
        st.subheader("Hourly Activity Trends")
        if not filtered_df.empty:
            hourly_dist = filtered_df.groupby(['Hour', 'Clock_In_Out']).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(10, 4))
            hourly_dist.plot(kind='area', stacked=True, ax=ax)
            plt.title('Hourly Activity Distribution')
            plt.xlabel('Hour of Day')
            plt.ylabel('Count')
            plt.xticks(range(24))
            st.pyplot(fig)

            st.subheader("Role-Specific Hourly Patterns")
            role_hourly = filtered_df.groupby(['Role', 'Hour']).size().unstack(fill_value=0)
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(role_hourly, cmap='YlOrRd', ax=ax)
            plt.title('Role Activity by Hour (Darker = More Activity)')
            plt.xlabel('Hour of Day')
            plt.ylabel('Role')
            st.pyplot(fig)
        else:
            st.warning("No data available for selected filters")

    # Refresh button with improved styling
    st.button('Refresh Data', 
              help="Click to load the latest attendance data",
              use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()