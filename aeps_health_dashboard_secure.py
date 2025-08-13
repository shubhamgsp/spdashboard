import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

# Google Cloud imports
from google.oauth2 import service_account
from google.cloud import bigquery
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Brand Plotly template and palette
BRAND_COLORWAY = ['#E31E24', '#1F3C88', '#00A36C', '#FF6B00', '#0EA5E9', '#9333EA', '#6B7280']
try:
    import plotly.io as pio
    pio.templates["spice_light"] = go.layout.Template(layout=go.Layout(
        colorway=BRAND_COLORWAY,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1F2937", family="Inter, Segoe UI, Roboto, Helvetica, Arial")
    ))
    px.defaults.template = "plotly_white"
    px.defaults.color_discrete_sequence = BRAND_COLORWAY
    pio.templates.default = "spice_light"
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="AEPS Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication function
def check_authentication():
    """Simple authentication for organizational access"""
    
    # Check if already authenticated
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>🏥 AEPS Health Dashboard</h1>
            <p>Please authenticate to access the dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input("Enter Dashboard Password", type="password")
            if st.button("Login"):
                # Get password from environment variable or Streamlit secrets
                def get_auth_password():
                    # First try environment variables
                    env_password = os.getenv('DASHBOARD_PASSWORD')
                    if env_password:
                        return env_password
                    
                    # Then try Streamlit secrets
                    try:
                        if hasattr(st, 'secrets') and 'auth' in st.secrets:
                            return st.secrets['auth'].get('DASHBOARD_PASSWORD', 'spicemoney2024')
                        elif hasattr(st, 'secrets') and 'DASHBOARD_PASSWORD' in st.secrets:
                            return st.secrets['DASHBOARD_PASSWORD']
                    except Exception:
                        pass
                    
                    return 'spicemoney2024'  # fallback default
                
                correct_password = get_auth_password()
                if password == correct_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
            st.stop()

# Check authentication first
check_authentication()

# Custom CSS for better styling
st.markdown("""
<style>
  :root {
    --primary:#E31E24; /* Spice red */
    --secondary:#1F3C88; /* Navy */
    --accent:#00A36C; /* Green */
    --muted:#6B7280;
    --bg:#F8FAFC; /* Light background */
    --panel:#FFFFFF; /* Cards */
    --text:#111827; /* Dark text */
    --border:#E5E7EB;
  }
  .stApp { background: var(--bg); color: var(--text); }
  .main-header { font-size: 2.2rem; font-weight: 700; color: var(--secondary); margin: .5rem 0 1.25rem; }
  .section-title { font-size: 1.1rem; font-weight: 700; color: var(--secondary); margin: .25rem 0 .6rem; }
  .metric-card, .stMetric { background: var(--panel); padding: 12px 14px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(31,60,136,0.06); }
  .metric-card h3 { margin: 0 0 4px; font-size: .9rem; color: var(--muted); }
  .metric-value { font-size: 1.55rem; font-weight: 700; color: var(--text); }
  .anomaly-alert { background:#FFF5F5; color:#B42318; padding:.65rem .85rem; border-radius:10px; border:1px solid #FEE2E2; }
  .success-alert { background:#ECFDF5; color:#065F46; padding:.65rem .85rem; border-radius:10px; border:1px solid #A7F3D0; }
  .info-alert { background:#EFF6FF; color:#1E3A8A; padding:.65rem .85rem; border-radius:10px; border:1px solid #DBEAFE; }
  .stMetric > div > div { color: var(--text); }
  .stDownloadButton button, .stButton button { background: var(--primary)!important; color:#fff!important; border:none!important; border-radius:10px!important; box-shadow: 0 2px 8px rgba(227,30,36,0.2)!important; }
  .help-button button { background: var(--secondary)!important; color:#fff!important; }
  .logout-button button { background: #dc2626!important; color:#fff!important; }
  .stSelectbox, .stMultiSelect, .stNumberInput, .stDateInput, .stSlider { color: var(--text); }
  .stTabs [data-baseweb="tab"] { color: var(--secondary); }
</style>
""", unsafe_allow_html=True)

# Help and Logout buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown('<div class="help-button">', unsafe_allow_html=True)
    if st.button("ℹ️ Help", help="Click to view the user guide"):
        st.session_state.show_help = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="logout-button">', unsafe_allow_html=True)
    if st.button("🚪 Logout", help="Click to logout from the dashboard"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🏥 AEPS Health Dashboard</h1>', unsafe_allow_html=True)

# Help Modal
if st.session_state.get('show_help', False):
    @st.dialog("📚 AEPS Health Dashboard - User Guide", width="large")
    def show_user_guide():
        try:
            # Read the user guide content
            import os
            # Try different possible paths for the user guide
            possible_paths = [
                'USER_GUIDE.md',  # Same directory as the script
                'aeps_health_project/USER_GUIDE.md',  # Relative from project root
                os.path.join(os.path.dirname(__file__), 'USER_GUIDE.md'),  # Same directory as script file
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'USER_GUIDE.md')  # Absolute path same directory
            ]
            
            user_guide_content = None
            used_path = None
            
            for path in possible_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        user_guide_content = f.read()
                        used_path = path
                        break
                except FileNotFoundError:
                    continue
            
            if user_guide_content is None:
                raise FileNotFoundError("USER_GUIDE.md not found in any expected location")
            
            # Add some intro text
            st.info("💡 This guide will help you understand and effectively use the AEPS Health Dashboard. Scroll down to explore all features and best practices.")
            
            # Display the content with markdown in a scrollable container
            st.markdown("""
            <style>
            .user-guide-content {
                max-height: 70vh;
                overflow-y: auto;
                padding: 1rem;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display the content with markdown
            with st.container():
                st.markdown(user_guide_content)
            
            # Close button
            if st.button("✖️ Close Guide", key="close_guide", help="Close the user guide"):
                st.session_state.show_help = False
                st.rerun()
                
        except FileNotFoundError as e:
            st.error("❌ User guide file not found. Please ensure USER_GUIDE.md exists in one of the expected locations.")
            st.info("📁 Searched in these locations:")
            # Show the paths that were tried
            import os
            possible_paths = [
                'USER_GUIDE.md',
                'aeps_health_project/USER_GUIDE.md',
                os.path.join(os.path.dirname(__file__), 'USER_GUIDE.md'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'USER_GUIDE.md')
            ]
            for path in possible_paths:
                st.text(f"• {path}")
            
            # Show current working directory
            st.info(f"📂 Current working directory: `{os.getcwd()}`")
            
            if st.button("✖️ Close", key="close_error"):
                st.session_state.show_help = False
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading user guide: {str(e)}")
            if st.button("✖️ Close", key="close_exception"):
                st.session_state.show_help = False
                st.rerun()
    
    show_user_guide()

# Sidebar configuration
st.sidebar.header("⚙️ Dashboard Settings")

# Page selection
page = st.sidebar.selectbox(
    "Select Page",
    ["🏥 Health Overview", "🗺️ State-wise Metrics", "🏦 Bank-wise Health"],
    index=0
)

# Date selection
selected_date = st.sidebar.date_input(
    "Select Date",
    value=datetime.now().date(),
    max_value=datetime.now().date()
)

# Time range selection (only for Health Overview)
if page == "🏥 Health Overview":
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
        index=0
    )
    
    # Hour range filter (0-23)
    hour_range = st.sidebar.slider(
        "Hour Range (0-23)",
        min_value=0,
        max_value=23,
        value=(0, 23)
    )
    
    # Aggregator traces to show
    aggregators_to_show = st.sidebar.multiselect(
        "Aggregators to display",
        options=["YBL", "NSDL", "YBLN"],
        default=["YBL", "NSDL", "YBLN"]
    )
    
    # Anomaly sensitivity (k·σ)
    anomaly_k = st.sidebar.slider(
        "Anomaly sensitivity (k·σ)",
        min_value=1.0,
        max_value=3.0,
        value=2.0,
        step=0.5
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=False)
    refresh_every_min = st.sidebar.number_input("Refresh every (minutes)", min_value=1, max_value=60, value=5)
    
    if auto_refresh:
        now_ts = datetime.now().timestamp()
        last = st.session_state.get("_last_refresh_ts", 0)
        if now_ts - last > refresh_every_min * 60:
            st.session_state["_last_refresh_ts"] = now_ts
            st.rerun()

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# BigQuery connection function
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bigquery_data(query_name, selected_date):
    """Fetch data from BigQuery for different health metrics"""
    
    try:
        # Set up BigQuery connection using environment variables
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/cloud-platform',
            "https://www.googleapis.com/auth/bigquery"
        ]
        
        # Create credentials from environment variables or Streamlit secrets
        def get_credential_value(key, default=None):
            """Get credential value from environment variables or Streamlit secrets"""
            # First try environment variables
            env_value = os.getenv(key)
            if env_value:
                return env_value
            
            # Then try Streamlit secrets
            try:
                if hasattr(st, 'secrets'):
                    if key in st.secrets.get('google_credentials', {}):
                        return st.secrets['google_credentials'][key]
                    elif key in st.secrets:
                        return st.secrets[key]
            except Exception:
                pass
            
            return default
        
        credentials_info = {
            "type": get_credential_value('GOOGLE_CREDENTIALS_TYPE', 'service_account'),
            "project_id": get_credential_value('GOOGLE_PROJECT_ID'),
            "private_key_id": get_credential_value('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": get_credential_value('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": get_credential_value('GOOGLE_CLIENT_EMAIL'),
            "client_id": get_credential_value('GOOGLE_CLIENT_ID'),
            "auth_uri": get_credential_value('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": get_credential_value('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": get_credential_value('GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": get_credential_value('GOOGLE_CLIENT_X509_CERT_URL'),
            "universe_domain": get_credential_value('GOOGLE_UNIVERSE_DOMAIN', 'googleapis.com')
        }
        
        # Check if required credentials are available
        required_fields = ['project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if not credentials_info.get(field)]
        
        if missing_fields:
            st.error(f"❌ Missing required BigQuery credentials: {', '.join(missing_fields)}")
            st.info("💡 Please check your .env file or Streamlit secrets configuration")
            return None
        
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, 
            scopes=scope
        )
        
        client = bigquery.Client(
            credentials=credentials, 
            project=credentials_info['project_id']
        )
        
                # Define queries based on query_name
        queries = {
            "transaction_success": """
            DECLARE today DATE DEFAULT DATE('{}');
            DECLARE last_7_days_start DATE DEFAULT DATE_SUB(today, INTERVAL 7 DAY);
            DECLARE last_7_days_end DATE DEFAULT DATE_SUB(today, INTERVAL 1 DAY);

            WITH insert_data AS (
              SELECT * 
              FROM spicemoney-dwh.ds_striim.T_AEPSR_TRANSACTION_RES
              WHERE DATE(op_time) BETWEEN last_7_days_start AND today
                AND op_name = 'INSERT'
            ),
            update_data AS (
              SELECT * EXCEPT(rn)
              FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY request_id ORDER BY op_time DESC) rn
                FROM spicemoney-dwh.ds_striim.T_AEPSR_TRANSACTION_RES
              WHERE DATE(op_time) BETWEEN last_7_days_start AND today
                AND op_name = 'UPDATE'
              )
              WHERE rn = 1
            ),
            aeps_res_data AS (
              SELECT 
                a.op_time, 
                b.op_name, 
                a.request_id, 
                a.rc, 
                b.SPICE_MESSAGE, 
                a.amount, 
                a.RESPONSE_MESSAGE
              FROM insert_data a
              JOIN update_data b ON a.request_id = b.request_id
            ),
            aeps_req_data AS (
              SELECT 
                op_time, 
                op_name, 
                request_id, 
                TRANS_AMT, 
                client_id, 
                master_trans_type, 
                trans_mode, 
                AGGREGATOR
              FROM spicemoney-dwh.ds_striim.T_AEPSR_TRANSACTION_REQ
              WHERE DATE(op_time) BETWEEN last_7_days_start AND today
            ),
            aeps_device_details AS (
              SELECT 
                REQUEST_ID, 
                DPID, 
                RDSID
              FROM ds_striim.T_AEPSR_TRANS_DEVICE_DETAILS
              WHERE DATE(op_time) BETWEEN last_7_days_start AND today
            ),
            combined_data AS (
              SELECT 
                DATETIME_TRUNC(t1.op_time, HOUR) AS hour,
                DATE(t1.op_time) AS date,
                t1.request_id,
                CAST(t1.trans_amt AS INT64) AS amount,
                CAST(t1.client_id AS STRING) AS agent_id,
                t2.rc,
                t2.spice_message,
                t1.master_trans_type,
                t1.aggregator,
                t3.RDSID,
                t3.DPID
              FROM aeps_req_data t1
              JOIN aeps_res_data t2 ON t1.request_id = t2.request_id
              JOIN aeps_device_details t3 ON t1.request_id = t3.request_id
              WHERE t1.master_trans_type = 'CW'
            ),
            hourly_metrics AS (
              SELECT 
                date,
                FORMAT_TIMESTAMP('%H:00', hour) AS hour,
                SUM(CASE WHEN LOWER(spice_message) = 'success' THEN amount END)/10000000 AS total_amount_cr,
                COUNT(*) AS total_txns,
                COUNTIF(LOWER(spice_message) = 'success') AS success_txns,
                COUNTIF(LOWER(spice_message) = 'success' AND LOWER(aggregator) = 'ybl') AS ybl_success,
                COUNTIF(LOWER(aggregator) = 'ybl') AS ybl_total,
                COUNTIF(LOWER(spice_message) = 'success' AND LOWER(aggregator) = 'nsdl') AS nsdl_success,
                COUNTIF(LOWER(aggregator) = 'nsdl') AS nsdl_total,
                COUNTIF(LOWER(spice_message) = 'success' AND LOWER(aggregator) = 'ybln') AS ybln_success,
                COUNTIF(LOWER(aggregator) = 'ybln') AS ybln_total
              FROM combined_data
              GROUP BY date, hour
            ),
            success_rates AS (
              SELECT 
                hour,
                total_amount_cr,
                total_txns,
                success_txns,
                CASE 
                  WHEN total_txns > 0 THEN ROUND((success_txns / total_txns) * 100, 2)
                  ELSE 0 
                END AS overall_success_rate,
                CASE 
                  WHEN ybl_total > 0 THEN ROUND((ybl_success / ybl_total) * 100, 2)
                  ELSE 0 
                END AS ybl_success_rate,
                CASE 
                  WHEN nsdl_total > 0 THEN ROUND((nsdl_success / nsdl_total) * 100, 2)
                  ELSE 0 
                END AS nsdl_success_rate,
                CASE 
                  WHEN ybln_total > 0 THEN ROUND((ybln_success / ybln_total) * 100, 2)
                  ELSE 0 
                END AS ybln_success_rate
              FROM hourly_metrics
              WHERE date = today
            ),
            historical_metrics AS (
              SELECT 
                hour,
                AVG(overall_success_rate) AS avg_success_rate,
                STDDEV_SAMP(overall_success_rate) AS stddev_success_rate,
                AVG(total_amount_cr) AS avg_amount_cr,
                STDDEV_SAMP(total_amount_cr) AS stddev_amount_cr
              FROM (
                SELECT 
                  hour,
                  CASE 
                    WHEN total_txns > 0 THEN ROUND((success_txns / total_txns) * 100, 2)
                    ELSE 0 
                  END AS overall_success_rate,
                  total_amount_cr
                FROM hourly_metrics
                WHERE date BETWEEN last_7_days_start AND last_7_days_end
              )
              GROUP BY hour
            )
            SELECT 
              s.hour,
              s.overall_success_rate,
              s.total_amount_cr,
              s.total_txns,
              s.success_txns,
              s.ybl_success_rate,
              s.nsdl_success_rate,
              s.ybln_success_rate,
              h.avg_success_rate,
              h.stddev_success_rate,
              h.avg_amount_cr,
              h.stddev_amount_cr,
              CASE 
                WHEN s.overall_success_rate < (h.avg_success_rate - 2 * h.stddev_success_rate) THEN 'low'
                WHEN s.overall_success_rate > (h.avg_success_rate + 2 * h.stddev_success_rate) THEN 'high'
                ELSE 'normal'
              END AS success_rate_anomaly,
              CASE 
                WHEN s.total_amount_cr < (h.avg_amount_cr - 2 * h.stddev_amount_cr) THEN 'low'
                WHEN s.total_amount_cr > (h.avg_amount_cr + 2 * h.stddev_amount_cr) THEN 'high'
                ELSE 'normal'
              END AS amount_cr_anomaly
            FROM success_rates s
            LEFT JOIN historical_metrics h ON s.hour = h.hour
            ORDER BY s.hour
            """.format(selected_date),
            
            "bio_authentication": """
            DECLARE today DATE DEFAULT DATE('{}');
            DECLARE yesterday DATE DEFAULT DATE_SUB(today, INTERVAL 1 DAY);
            DECLARE last_7_days_start DATE DEFAULT DATE_SUB(today, INTERVAL 7 DAY);
            DECLARE last_7_days_end DATE DEFAULT DATE_SUB(today, INTERVAL 1 DAY);

            WITH insert_data AS (
              SELECT * 
              FROM `spicemoney-dwh.ds_striim.T_AEPSR_BIO_AUTH_LOGGING_P` 
              WHERE DATE(OP_TIME) BETWEEN last_7_days_start AND today
                AND OP_NAME = 'INSERT'
            ),
            update_data AS (
              SELECT * 
              FROM `spicemoney-dwh.ds_striim.T_AEPSR_BIO_AUTH_LOGGING_P` 
              WHERE DATE(OP_TIME) BETWEEN last_7_days_start AND today
                AND OP_NAME = 'UPDATE'
            ),
            combined_data AS (
              SELECT  
                TIMESTAMP_TRUNC(b.op_time, HOUR) AS hour,
                date(b.op_time) AS date,
                a.client_id,
                a.AGGREGATOR,
                b.RC,
                b.RM,
                a.request_id
              FROM insert_data a
              JOIN update_data b ON a.request_id = b.request_id 
            ),
            hourly_metrics AS (
              SELECT 
                date,
                FORMAT_TIMESTAMP('%H:00', hour) AS hour,
                COUNT(CASE WHEN RC = '00' THEN client_id END) AS succ_att_ftr,
                COUNT(client_id) AS total_att_ftr,
                COUNT(DISTINCT CASE WHEN AGGREGATOR = 'NSDL' AND RC = '00' THEN client_id END) AS succ_att_ftr_nsdl,
                COUNT(DISTINCT CASE WHEN AGGREGATOR = 'NSDL' THEN client_id END) AS total_att_ftr_nsdl,
                COUNT(DISTINCT CASE WHEN AGGREGATOR IN ('YBL', 'YBLN') AND RC = '00' THEN client_id END) AS succ_att_ftr_ybl,
                COUNT(DISTINCT CASE WHEN AGGREGATOR IN ('YBL', 'YBLN') THEN client_id END) AS total_att_ftr_ybl,
                COUNT(CASE WHEN RC = '00' THEN client_id END) AS succ_att_tot_ftr,
                COUNT(DISTINCT CASE WHEN RC = '00' THEN client_id END) AS succ_att_sma_ftr
              FROM combined_data
              GROUP BY date, hour
            ),
            yesterday_data AS (
              SELECT 
                hour,
                date,
                total_att_ftr AS total_attempts,
                succ_att_ftr AS successful_attempts,
                ROUND(SAFE_DIVIDE(succ_att_ftr, total_att_ftr) * 100, 2) AS fa2_succ_rate,
                ROUND(SAFE_DIVIDE(succ_att_ftr_nsdl,total_att_ftr_nsdl) * 100, 2) AS fa2_succ_rate_nsdl,
                ROUND(SAFE_DIVIDE(succ_att_ftr_ybl, total_att_ftr_ybl) * 100, 2) AS fa2_succ_rate_ybl,
                ROUND(SAFE_DIVIDE(succ_att_tot_ftr, succ_att_sma_ftr), 2) AS fa2_per_user_rate
              FROM hourly_metrics
              WHERE date = today
            ),
            median_data AS (
              SELECT 
                hour,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(succ_att_ftr, total_att_ftr) * 100, 2)[OFFSET(1)], 2) AS median_fa2_succ_rate,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(succ_att_ftr_nsdl,total_att_ftr_nsdl) * 100, 2)[OFFSET(1)], 2) AS median_fa2_succ_rate_nsdl,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(succ_att_ftr_ybl, total_att_ftr_ybl) * 100, 2)[OFFSET(1)], 2) AS median_fa2_succ_rate_ybl,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(succ_att_tot_ftr, succ_att_sma_ftr), 2)[OFFSET(1)], 2) AS median_fa2_per_user_rate,
                STDDEV_SAMP(SAFE_DIVIDE(succ_att_tot_ftr, succ_att_sma_ftr)) AS stddev_per_user_rate,
                STDDEV_SAMP(SAFE_DIVIDE(succ_att_ftr, total_att_ftr)*100) AS stddev_succ_rate,
                STDDEV_SAMP(SAFE_DIVIDE(succ_att_ftr_nsdl, total_att_ftr_nsdl)*100) AS stddev_succ_rate_nsdl, 
                STDDEV_SAMP(SAFE_DIVIDE(succ_att_ftr_ybl, total_att_ftr_ybl)*100) AS stddev_succ_rate_ybl
              FROM hourly_metrics
              WHERE date BETWEEN last_7_days_start AND last_7_days_end
              GROUP BY hour
            )
                          SELECT 
                date,
                COALESCE(y.hour, m.hour) AS hour,
                y.fa2_succ_rate AS fa2_rate_yesterday,
                m.median_fa2_succ_rate,
                y.fa2_succ_rate_nsdl AS nsdl_rate_yesterday,
                m.median_fa2_succ_rate_nsdl,
                y.fa2_succ_rate_ybl AS ybl_rate_yesterday,
                m.median_fa2_succ_rate_ybl,
                y.fa2_per_user_rate AS per_user_rate_yesterday,
                m.median_fa2_per_user_rate,
                y.total_attempts,
                y.successful_attempts,
                CASE 
                WHEN y.fa2_succ_rate < m.median_fa2_succ_rate - stddev_succ_rate THEN 'Lower Anomaly ↓'
                WHEN y.fa2_succ_rate > m.median_fa2_succ_rate + stddev_succ_rate THEN 'Upper Anomaly ↑'
                ELSE 'normal'
                END AS fa2_succ_flag
            FROM median_data m
            FULL OUTER JOIN yesterday_data y ON m.hour = y.hour
            ORDER BY hour
            """.format(selected_date),
            
            "state_metrics": """
            WITH yesterday_data AS (
              SELECT 
                v.final_state,
                SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS yesterday_gtv,
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS yesterday_transactions,
                SAFE_DIVIDE(
                  COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                  COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
                ) * 100 AS yesterday_success_rate
              FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
              JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
              JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
              WHERE DATE(a.log_date_time) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
                AND DATE(b.log_date_time) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
                AND v.final_state IS NOT NULL
              GROUP BY v.final_state
            ),
            historical_90d AS (
              SELECT 
                v.final_state,
                DATE(a.log_date_time) AS date,
                SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS daily_gtv,
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS daily_transactions,
                SAFE_DIVIDE(
                  COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                  COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
                ) * 100 AS daily_success_rate
              FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
              JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
              JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
              WHERE DATE(a.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND DATE(b.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND v.final_state IS NOT NULL
              GROUP BY v.final_state, DATE(a.log_date_time)
            ),
            historical_stats AS (
              SELECT 
                final_state,
                APPROX_QUANTILES(daily_gtv, 2)[OFFSET(1)] AS median_90d_gtv,
                APPROX_QUANTILES(daily_success_rate, 2)[OFFSET(1)] AS median_90d_success_rate,
                STDDEV_SAMP(daily_gtv) AS stddev_90d_gtv,
                STDDEV_SAMP(daily_success_rate) AS stddev_90d_success_rate
              FROM historical_90d
              GROUP BY final_state
            ),
            weekday_data AS (
              SELECT 
                v.final_state,
                EXTRACT(DAYOFWEEK FROM DATE(a.log_date_time)) AS day_of_week,
                SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS daily_gtv,
                SAFE_DIVIDE(
                  COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                  COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
                ) * 100 AS daily_success_rate
              FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
              JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
              JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
              WHERE DATE(a.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND DATE(b.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND v.final_state IS NOT NULL
              GROUP BY v.final_state, EXTRACT(DAYOFWEEK FROM DATE(a.log_date_time))
            ),
            weekday_median AS (
              SELECT 
                final_state,
                APPROX_QUANTILES(daily_gtv, 2)[OFFSET(1)] AS median_gtv,
                APPROX_QUANTILES(daily_success_rate, 2)[OFFSET(1)] AS median_success_rate
              FROM weekday_data
              WHERE day_of_week = EXTRACT(DAYOFWEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
              GROUP BY final_state
            ),
            day_of_month_data AS (
              SELECT 
                v.final_state,
                EXTRACT(DAY FROM DATE(a.log_date_time)) AS day_of_month,
                SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS daily_gtv,
                SAFE_DIVIDE(
                  COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                  COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
                ) * 100 AS daily_success_rate
              FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
              JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
              JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
              WHERE DATE(a.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND DATE(b.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
                AND v.final_state IS NOT NULL
              GROUP BY v.final_state, EXTRACT(DAY FROM DATE(a.log_date_time))
            ),
            day_of_month_median AS (
              SELECT 
                final_state,
                APPROX_QUANTILES(daily_gtv, 2)[OFFSET(1)] AS median_gtv,
                APPROX_QUANTILES(daily_success_rate, 2)[OFFSET(1)] AS median_success_rate
              FROM day_of_month_data
              WHERE day_of_month = EXTRACT(DAY FROM DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
              GROUP BY final_state
            )
            SELECT 
              y.final_state,
              y.yesterday_gtv,
              y.yesterday_transactions,
              y.yesterday_success_rate,
              h.median_90d_gtv,
              h.median_90d_success_rate,
              h.stddev_90d_gtv,
              h.stddev_90d_success_rate,
              w.median_gtv AS same_weekday_median_gtv,
              w.median_success_rate AS same_weekday_median_success_rate,
              d.median_gtv AS same_day_month_median_gtv,
              d.median_success_rate AS same_day_month_median_success_rate,
              SAFE_DIVIDE(y.yesterday_gtv, h.median_90d_gtv) AS gtv_vs_median_ratio,
              SAFE_DIVIDE(y.yesterday_success_rate, h.median_90d_success_rate) AS success_vs_median_ratio
            FROM yesterday_data y
            LEFT JOIN historical_stats h ON y.final_state = h.final_state
            LEFT JOIN weekday_median w ON y.final_state = w.final_state
            LEFT JOIN day_of_month_median d ON y.final_state = d.final_state
            ORDER BY y.yesterday_gtv DESC
            """,
            
            "state_10d_trend": """
            SELECT 
              DATE(a.log_date_time) AS date,
              v.final_state,
              SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
              COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transactions,
              SAFE_DIVIDE(
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
              ) * 100 AS success_rate
            FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
            JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
            JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
            WHERE DATE(a.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
              AND DATE(b.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 10 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
              AND v.final_state IS NOT NULL
            GROUP BY DATE(a.log_date_time), v.final_state
            ORDER BY date DESC, gtv DESC
            """,
            
            "state_30d_trend": """
            SELECT 
              DATE(a.log_date_time) AS date,
              v.final_state,
              SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
              COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transactions,
              SAFE_DIVIDE(
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
              ) * 100 AS success_rate
            FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
            JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
            JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
            WHERE DATE(a.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
              AND DATE(b.log_date_time) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
              AND v.final_state IS NOT NULL
            GROUP BY DATE(a.log_date_time), v.final_state
            ORDER BY date DESC, gtv DESC
            """,
            
            "bank_health": """
            WITH date_range AS (
              SELECT
                DATE('{START_DATE}') AS start_date,
                DATE('{END_DATE}') AS end_date
            ),
            daily_bank_metrics AS (
              SELECT
                v.final_state,
                DATE(a.log_date_time) AS date,
                a.cust_bank_name,
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transaction_count,
                SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END) AS success_count,
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS total_count
              FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
              JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
              JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
              CROSS JOIN
                date_range dr
              WHERE
                DATE(a.log_date_time) BETWEEN dr.start_date AND dr.end_date
                AND DATE(b.log_date_time) BETWEEN dr.start_date AND dr.end_date
                AND a.cust_bank_name IS NOT NULL
                AND v.final_state IS NOT NULL
              GROUP BY
                v.final_state, DATE(a.log_date_time), a.cust_bank_name
            ),
            bank_performance AS (
              SELECT final_state, cust_bank_name,
                 SUM(gtv) AS total_gtv,
                 SUM(transaction_count) AS total_transactions,
                 SAFE_DIVIDE(SUM(success_count), SUM(total_count)) * 100 AS success_rate,
                 COUNT(DISTINCT date) AS active_days
              FROM daily_bank_metrics
              GROUP BY final_state, cust_bank_name
            ),
            ranked_banks AS (
              SELECT final_state, cust_bank_name, total_gtv, total_transactions, success_rate, active_days,
                     RANK() OVER (PARTITION BY final_state ORDER BY total_gtv DESC) AS rank
              FROM bank_performance
              WHERE total_gtv > 0
            ),
            top_banks AS (
              SELECT final_state, cust_bank_name, total_gtv, total_transactions, success_rate, active_days
              FROM ranked_banks WHERE rank <= 5
            )
            SELECT d.final_state, d.date, d.cust_bank_name, d.transaction_count, d.gtv,
                   SAFE_DIVIDE(d.success_count, d.total_count) * 100 AS trans_percentage,
                   t.total_gtv AS bank_total_gtv, t.total_transactions AS bank_total_transactions,
                   t.success_rate AS bank_success_rate, t.active_days
            FROM daily_bank_metrics d
            JOIN top_banks t ON d.cust_bank_name = t.cust_bank_name AND d.final_state = t.final_state
            ORDER BY d.date DESC, d.final_state, d.gtv DESC
            """,
            
            "bank_yesterday": """
            WITH y AS (
              SELECT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS the_day
            )
            SELECT 
              a.cust_bank_name,
              COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transaction_count,
              SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
              SAFE_DIVIDE(
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
              ) * 100 AS trans_percentage
            FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
            JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
            CROSS JOIN y
            WHERE DATE(a.log_date_time) = y.the_day AND DATE(b.log_date_time) = y.the_day
              AND a.cust_bank_name IS NOT NULL
            GROUP BY a.cust_bank_name
            ORDER BY gtv DESC
            LIMIT 25
            """,
            
            "bank_yesterday_by_state": """
            WITH y AS (SELECT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS the_day)
            SELECT 
              v.final_state,
              a.cust_bank_name,
              COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transaction_count,
              COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END) AS success_count,
              COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS total_count,
              SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
              SAFE_DIVIDE(
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
              ) * 100 AS trans_percentage
            FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
            JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
            JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
            CROSS JOIN y
            WHERE DATE(a.log_date_time) = y.the_day AND DATE(b.log_date_time) = y.the_day
              AND a.cust_bank_name IS NOT NULL AND v.final_state IS NOT NULL
            GROUP BY v.final_state, a.cust_bank_name
            ORDER BY gtv DESC
            """,
            
            "bank_state_90d_trend": """
            WITH dr AS (
              SELECT DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AS start_date,
                     DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) AS end_date
            )
            SELECT 
              DATE(a.log_date_time) AS date,
              v.final_state,
              SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
              SAFE_DIVIDE(
                COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END),
                COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END)
              ) * 100 AS trans_percentage
            FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
            JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
            JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
            CROSS JOIN dr
            WHERE DATE(a.log_date_time) BETWEEN dr.start_date AND dr.end_date
              AND DATE(b.log_date_time) BETWEEN dr.start_date AND dr.end_date
              AND v.final_state IS NOT NULL
            GROUP BY date, v.final_state
            ORDER BY date DESC
            """
        }
        
        # Execute the appropriate query
        query = queries.get(query_name)
        if not query:
            st.error(f"Unknown query: {query_name}")
            return None
        
        # Execute query
        with st.spinner(f"🔄 Fetching {query_name} data..."):
            df = client.query(query).result().to_dataframe()
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error connecting to BigQuery: {str(e)}")
        return None

# Load data
col1, col2, col3 = st.columns(3)

with col1:
    transaction_data = get_bigquery_data("transaction_success", selected_date)

with col2:
    bio_auth_data = get_bigquery_data("bio_authentication", selected_date)

with col3:
    if page == "🏥 Health Overview":
        st.info("📊 Loading device performance and error analysis data...")
    else:
        st.info("🗺️ Loading state-wise metrics data...")

# Page routing
if page == "🏥 Health Overview":
    # Health Overview Page
    if transaction_data is not None and bio_auth_data is not None:
        
        # Comprehensive Summary Section
        st.markdown("---")
        st.subheader("📊 AEPS Health Dashboard - Executive Summary")
        
        # Calculate comprehensive metrics
        if not transaction_data.empty:
            avg_transaction_success = transaction_data['overall_success_rate'].mean()
            transaction_health_score = min(100, max(0, avg_transaction_success))
            
            # Calculate GTV metrics
            total_gtv = transaction_data['total_amount_cr'].sum() if 'total_amount_cr' in transaction_data.columns else 0
            avg_gtv_per_hour = transaction_data['total_amount_cr'].mean() if 'total_amount_cr' in transaction_data.columns else 0
            total_transactions = transaction_data['total_txns'].sum() if 'total_txns' in transaction_data.columns else 0
            success_transactions = transaction_data['success_txns'].sum() if 'success_txns' in transaction_data.columns else 0
            
            # Get last completed hour
            last_hour = transaction_data['hour'].iloc[-1] if not transaction_data.empty else "N/A"
            
            # Calculate aggregator performance
            if all(col in transaction_data.columns for col in ['ybl_success_rate', 'nsdl_success_rate', 'ybln_success_rate']):
                avg_ybl_rate = transaction_data['ybl_success_rate'].mean()
                avg_nsdl_rate = transaction_data['nsdl_success_rate'].mean()
                avg_ybln_rate = transaction_data['ybln_success_rate'].mean()
            else:
                avg_ybl_rate = avg_nsdl_rate = avg_ybln_rate = 0
        else:
            transaction_health_score = total_gtv = avg_gtv_per_hour = total_transactions = success_transactions = 0
            last_hour = "N/A"
            avg_ybl_rate = avg_nsdl_rate = avg_ybln_rate = 0
        
        if not bio_auth_data.empty:
            avg_bio_success = bio_auth_data['fa2_rate_yesterday'].mean()
            bio_health_score = min(100, max(0, avg_bio_success))
            total_bio_attempts = bio_auth_data['total_attempts'].sum() if 'total_attempts' in bio_auth_data.columns else 0
            successful_bio_attempts = bio_auth_data['successful_attempts'].sum() if 'successful_attempts' in bio_auth_data.columns else 0
        else:
            bio_health_score = total_bio_attempts = successful_bio_attempts = 0
        
        overall_health_score = (transaction_health_score * 0.7 + bio_health_score * 0.3)
        
        # Summary Cards Row 1 - Core Health Metrics
        st.markdown("#### 🎯 Core Health Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Overall Health Score",
                value=f"{overall_health_score:.1f}%",
                delta=f"{'🟢' if overall_health_score >= 90 else '🟡' if overall_health_score >= 75 else '🔴'}",
                help="Weighted average of transaction and bio-auth success rates"
            )
        
        with col2:
            st.metric(
                label="Transaction Success",
                value=f"{transaction_health_score:.1f}%",
                delta=f"{'🟢' if transaction_health_score >= 95 else '🟡' if transaction_health_score >= 85 else '🔴'}",
                help="Average transaction success rate across all hours"
            )
        
        with col3:
            st.metric(
                label="Bio-Auth Success",
                value=f"{bio_health_score:.1f}%",
                delta=f"{'🟢' if bio_health_score >= 95 else '🟡' if bio_health_score >= 85 else '🔴'}",
                help="Average bio-authentication success rate"
            )
        
        with col4:
            st.metric(
                label="Total GTV (Cr)",
                value=f"{total_gtv:.2f}",
                help="Total Gross Transaction Value processed"
            )
        
        with col5:
            st.metric(
                label="Last Hour",
                value=f"{last_hour}",
                help="Last completed hour with data"
            )
        
        # Summary Cards Row 2 - Transaction Details
        st.markdown("#### 💳 Transaction Details")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Transactions",
                value=f"{total_transactions:,}",
                help="Total number of transactions processed"
            )
        
        with col2:
            st.metric(
                label="Successful Transactions",
                value=f"{success_transactions:,}",
                help="Number of successful transactions"
            )
        
        with col3:
            st.metric(
                label="Avg GTV/Hour (Cr)",
                value=f"{avg_gtv_per_hour:.2f}",
                help="Average Gross Transaction Value per hour"
            )
        
        with col4:
            st.metric(
                label="YBL Success Rate",
                value=f"{avg_ybl_rate:.1f}%",
                delta=f"{'🟢' if avg_ybl_rate >= 95 else '🟡' if avg_ybl_rate >= 85 else '🔴'}"
            )
        
        with col5:
            st.metric(
                label="NSDL Success Rate",
                value=f"{avg_nsdl_rate:.1f}%",
                delta=f"{'🟢' if avg_nsdl_rate >= 95 else '🟡' if avg_nsdl_rate >= 85 else '🔴'}"
            )
        
        # Summary Cards Row 3 - Bio-Authentication Details
        st.markdown("#### 🔐 Bio-Authentication Details")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Bio-Auth Attempts",
                value=f"{total_bio_attempts:,}",
                help="Total bio-authentication attempts"
            )
        
        with col2:
            st.metric(
                label="Successful Bio-Auth",
                value=f"{successful_bio_attempts:,}",
                help="Successful bio-authentication attempts"
            )
        
        with col3:
            st.metric(
                label="Bio-Auth Success Rate",
                value=f"{bio_health_score:.1f}%",
                help="Overall bio-authentication success rate"
            )
        
        with col4:
            st.metric(
                label="YBLN Success Rate",
                value=f"{avg_ybln_rate:.1f}%",
                delta=f"{'🟢' if avg_ybln_rate >= 95 else '🟡' if avg_ybln_rate >= 85 else '🔴'}"
            )
        
        with col5:
            st.metric(
                label="Data Coverage",
                value=f"{'Complete' if not transaction_data.empty and not bio_auth_data.empty else 'Partial' if transaction_data.empty or bio_auth_data.empty else 'None'}",
                delta=f"{'🟢' if not transaction_data.empty and not bio_auth_data.empty else '🟡' if transaction_data.empty or bio_auth_data.empty else '🔴'}"
            )
        
        # Transaction Success Rates with Anomalies
        st.markdown("---")
        st.subheader("📈 Transaction Success Rates")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filter by hour range
            tx = transaction_data.copy()
            try:
                hr_numeric = tx['hour'].str.slice(0,2).astype(int)
                tx = tx[(hr_numeric >= hour_range[0]) & (hr_numeric <= hour_range[1])]
            except Exception:
                pass
            
            # Overall success rate trend
            fig_success = go.Figure()
            fig_success.add_trace(go.Scatter(
                x=tx['hour'],
                y=tx['overall_success_rate'],
                mode='lines+markers',
                name='Current',
                line=dict(color='blue', width=3)
            ))
            if 'avg_success_rate' in tx.columns:
                fig_success.add_trace(go.Scatter(
                    x=tx['hour'],
                    y=tx['avg_success_rate'],
                    mode='lines',
                    name='7-Day Average',
                    line=dict(color='gray', width=2, dash='dash')
                ))
            fig_success.update_layout(
                title="Overall Transaction Success Rate",
                xaxis_title="Hour",
                yaxis_title="Success Rate (%)",
                height=400
            )
            st.plotly_chart(fig_success, use_container_width=True)
            
            # Transaction anomalies below the graph
            if not tx.empty:
                transaction_anomalies = tx[tx['success_rate_anomaly'] != 'normal']
                if not transaction_anomalies.empty:
                    st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
                    st.write("**🚨 Transaction Success Rate Anomalies:**")
                    for _, row in transaction_anomalies.iterrows():
                        st.write(f"• Hour {row['hour']}: {row['success_rate_anomaly']} (Rate: {row['overall_success_rate']:.1f}%)")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                    st.write("✅ **No transaction success rate anomalies detected.**")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Filter bio by hour range
            bio = bio_auth_data.copy()
            try:
                hr_numeric_bio = bio['hour'].str.slice(0,2).astype(int)
                bio = bio[(hr_numeric_bio >= hour_range[0]) & (hr_numeric_bio <= hour_range[1])]
            except Exception:
                pass
            
            # Per-user authentication rate
            fig_user = go.Figure()
            fig_user.add_trace(go.Scatter(
                x=bio['hour'],
                y=bio['per_user_rate_yesterday'],
                mode='lines+markers',
                name='Current',
                line=dict(color='brown', width=3)
            ))
            fig_user.add_trace(go.Scatter(
                x=bio['hour'],
                y=bio['median_fa2_per_user_rate'],
                mode='lines',
                name='7-Day Median',
                line=dict(color='gray', width=2, dash='dash')
            ))
            fig_user.update_layout(
                title="Per-User Authentication Rate",
                xaxis_title="Hour",
                yaxis_title="Rate",
                height=400
            )
            st.plotly_chart(fig_user, use_container_width=True)
            
            # Bio-auth anomalies below the graph
            if not bio_auth_data.empty:
                bio_anomalies = bio[
                    (bio['fa2_succ_flag'] != 'Normal') & 
                    (bio['fa2_succ_flag'] != 'normal') &
                    (bio['fa2_succ_flag'].str.contains('Anomaly', na=False))
                ]
                if not bio_anomalies.empty:
                    st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
                    st.write("**🚨 Bio-Authentication Anomalies:**")
                    for _, row in bio_anomalies.iterrows():
                        rate_col = 'fa2_rate_yesterday' if 'fa2_rate_yesterday' in bio_auth_data.columns else 'fa2_succ_rate'
                        rate_value = row.get(rate_col, 0)
                        st.write(f"• Hour {row['hour']}: {row['fa2_succ_flag']} (Rate: {rate_value:.1f}%)")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                    st.write("✅ **No bio-authentication anomalies detected.**")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Detailed Data Tables
        st.markdown("---")
        st.subheader("📋 Detailed Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Transaction & GTV Metrics by Hour**")
            if not transaction_data.empty:
                display_cols = ['hour', 'overall_success_rate', 'total_amount_cr', 'success_txns', 'ybl_success_rate', 'nsdl_success_rate']
                available_cols = [col for col in display_cols if col in transaction_data.columns]
                st.dataframe(
                    transaction_data[available_cols].round(2),
                    use_container_width=True
                )
        
        with col2:
            st.write("**Bio-Authentication Success Rates by Hour**")
            if not bio_auth_data.empty:
                display_cols = ['hour', 'fa2_rate_yesterday', 'nsdl_rate_yesterday', 'ybl_rate_yesterday', 'per_user_rate_yesterday']
                available_cols = [col for col in display_cols if col in bio_auth_data.columns]
                st.dataframe(
                    bio_auth_data[available_cols].round(2),
                    use_container_width=True
                )
        
        # GTV Analysis with Anomalies
        st.markdown("---")
        st.subheader("💰 GTV Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # GTV trend
            if not transaction_data.empty and 'total_amount_cr' in transaction_data.columns:
                fig_gtv = go.Figure()
                fig_gtv.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['total_amount_cr'],
                    mode='lines+markers',
                    name='Current GTV',
                    line=dict(color='green', width=3),
                    fill='tonexty'
                ))
                                 # Filter by hour for GTV
                tx2 = transaction_data.copy()
                try:
                    hr2 = tx2['hour'].str.slice(0,2).astype(int)
                    tx2 = tx2[(hr2 >= hour_range[0]) & (hr2 <= hour_range[1])]
                except Exception:
                    pass
                
                if 'avg_amount_cr' in tx2.columns:
                    fig_gtv.add_trace(go.Scatter(
                        x=tx2['hour'],
                        y=tx2['avg_amount_cr'],
                        mode='lines',
                        name='7-Day Average',
                        line=dict(color='gray', width=2, dash='dash')
                    ))
                fig_gtv.update_layout(
                    title="GTV Trend by Hour",
                    xaxis_title="Hour",
                    yaxis_title="GTV (Cr)",
                    height=400
                )
                st.plotly_chart(fig_gtv, use_container_width=True)
                
                # GTV anomalies below the graph
                # Allow sensitivity control (k·σ). If std columns exist, recompute anomaly flags locally
                if all(col in tx2.columns for col in ['avg_amount_cr','stddev_amount_cr','total_amount_cr']):
                    lower = tx2['avg_amount_cr'] - anomaly_k * tx2['stddev_amount_cr']
                    upper = tx2['avg_amount_cr'] + anomaly_k * tx2['stddev_amount_cr']
                    tx2['amount_cr_anomaly_local'] = np.where(tx2['total_amount_cr'] < lower, 'low', np.where(tx2['total_amount_cr'] > upper, 'high', 'normal'))
                    gtv_anomalies = tx2[tx2['amount_cr_anomaly_local'] != 'normal']
                else:
                    gtv_anomalies = transaction_data[transaction_data['amount_cr_anomaly'] != 'normal'] if 'amount_cr_anomaly' in transaction_data.columns else pd.DataFrame()
                
                if not gtv_anomalies.empty:
                    st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
                    st.write("**🚨 GTV Anomalies:**")
                    for _, row in gtv_anomalies.iterrows():
                        gtv_value = row.get('total_amount_cr', 0)
                        st.write(f"• Hour {row['hour']}: {row.get('amount_cr_anomaly_local', row.get('amount_cr_anomaly',''))} (GTV: {gtv_value:.1f} Cr)")
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-alert">', unsafe_allow_html=True)
                    st.write("✅ **No GTV anomalies detected.**")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Transaction volume trend
            if not transaction_data.empty and 'total_txns' in transaction_data.columns:
                fig_volume = go.Figure()
                fig_volume.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['total_txns'],
                    mode='lines+markers',
                    name='Total Transactions',
                    line=dict(color='purple', width=3),
                    fill='tonexty'
                ))
                fig_volume.update_layout(
                    title="Transaction Volume by Hour",
                    xaxis_title="Hour",
                    yaxis_title="Number of Transactions",
                    height=400
                )
                st.plotly_chart(fig_volume, use_container_width=True)
                
                # Volume analysis
                if not transaction_data.empty:
                    avg_volume = transaction_data['total_txns'].mean()
                    current_volume = transaction_data['total_txns'].iloc[-1] if not transaction_data.empty else 0
                    volume_status = "High" if current_volume > avg_volume * 1.2 else "Low" if current_volume < avg_volume * 0.8 else "Normal"
                    
                    st.markdown('<div class="info-alert">', unsafe_allow_html=True)
                    st.write(f"**📊 Volume Analysis:** Current: {current_volume:,.0f}, Average: {avg_volume:,.0f} ({volume_status} volume)")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Aggregator Performance Comparison
        st.markdown("---")
        st.subheader("🏦 Aggregator Performance Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Aggregator success rates comparison
            if not transaction_data.empty and all(col in transaction_data.columns for col in ['ybl_success_rate', 'nsdl_success_rate', 'ybln_success_rate']):
                # Apply hour filter
                t3 = transaction_data.copy()
                try:
                    hr3 = t3['hour'].str.slice(0,2).astype(int)
                    t3 = t3[(hr3 >= hour_range[0]) & (hr3 <= hour_range[1])]
                except Exception:
                    pass
                
                fig_aggregator = go.Figure()
                if "YBL" in aggregators_to_show:
                    fig_aggregator.add_trace(go.Scatter(
                        x=t3['hour'],
                        y=t3['ybl_success_rate'],
                        mode='lines+markers',
                        name='YBL',
                        line=dict(color='blue', width=3)
                    ))
                if "NSDL" in aggregators_to_show:
                    fig_aggregator.add_trace(go.Scatter(
                        x=t3['hour'],
                        y=t3['nsdl_success_rate'],
                        mode='lines+markers',
                        name='NSDL',
                        line=dict(color='green', width=3)
                    ))
                if "YBLN" in aggregators_to_show:
                    fig_aggregator.add_trace(go.Scatter(
                        x=t3['hour'],
                        y=t3['ybln_success_rate'],
                        mode='lines+markers',
                        name='YBLN',
                        line=dict(color='orange', width=3)
                    ))
                fig_aggregator.update_layout(
                    title="Aggregator Success Rates Comparison",
                    xaxis_title="Hour",
                    yaxis_title="Success Rate (%)",
                    height=400
                )
                st.plotly_chart(fig_aggregator, use_container_width=True)
                
                # Aggregator performance summary
                if not transaction_data.empty:
                    st.markdown('<div class="info-alert">', unsafe_allow_html=True)
                    st.write("**🏦 Aggregator Performance:**")
                    if 'ybl_success_rate' in transaction_data.columns:
                        avg_ybl = transaction_data['ybl_success_rate'].mean()
                        st.write(f"• YBL: {avg_ybl:.1f}%")
                    if 'nsdl_success_rate' in transaction_data.columns:
                        avg_nsdl = transaction_data['nsdl_success_rate'].mean()
                        st.write(f"• NSDL: {avg_nsdl:.1f}%")
                    if 'ybln_success_rate' in transaction_data.columns:
                        avg_ybln = transaction_data['ybln_success_rate'].mean()
                        st.write(f"• YBLN: {avg_ybln:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Bio-auth aggregator comparison
            if not bio_auth_data.empty and all(col in bio_auth_data.columns for col in ['nsdl_rate_yesterday', 'ybl_rate_yesterday']):
                # Apply hour filter
                b2 = bio_auth_data.copy()
                try:
                    hb2 = b2['hour'].str.slice(0,2).astype(int)
                    b2 = b2[(hb2 >= hour_range[0]) & (hb2 <= hour_range[1])]
                except Exception:
                    pass
                fig_bio_aggregator = go.Figure()
                if "YBL" in aggregators_to_show:
                    fig_bio_aggregator.add_trace(go.Scatter(
                        x=b2['hour'],
                        y=b2['ybl_rate_yesterday'],
                        mode='lines+markers',
                        name='YBL',
                        line=dict(color='blue', width=3)
                    ))
                if "NSDL" in aggregators_to_show:
                    fig_bio_aggregator.add_trace(go.Scatter(
                        x=b2['hour'],
                        y=b2['nsdl_rate_yesterday'],
                        mode='lines+markers',
                        name='NSDL',
                        line=dict(color='green', width=3)
                    ))
                fig_bio_aggregator.update_layout(
                    title="Bio-Auth Aggregator Success Rates",
                    xaxis_title="Hour",
                    yaxis_title="Success Rate (%)",
                    height=400
                )
                st.plotly_chart(fig_bio_aggregator, use_container_width=True)
                
                # Bio-auth aggregator summary
                if not bio_auth_data.empty:
                    st.markdown('<div class="info-alert">', unsafe_allow_html=True)
                    st.write("**🔐 Bio-Auth Aggregator Performance:**")
                    if 'ybl_rate_yesterday' in bio_auth_data.columns:
                        avg_ybl_bio = bio_auth_data['ybl_rate_yesterday'].mean()
                        st.write(f"• YBL: {avg_ybl_bio:.1f}%")
                    if 'nsdl_rate_yesterday' in bio_auth_data.columns:
                        avg_nsdl_bio = bio_auth_data['nsdl_rate_yesterday'].mean()
                        st.write(f"• NSDL: {avg_nsdl_bio:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Success vs Failed Transactions Analysis
        st.markdown("---")
        st.subheader("📊 Success vs Failed Transactions Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success vs Failed transactions
            if not transaction_data.empty and all(col in transaction_data.columns for col in ['success_txns', 'total_txns']):
                transaction_data['failed_txns'] = transaction_data['total_txns'] - transaction_data['success_txns']
                
                fig_success_failed = go.Figure()
                fig_success_failed.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['success_txns'],
                    mode='lines+markers',
                    name='Successful',
                    line=dict(color='green', width=3)
                ))
                fig_success_failed.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['failed_txns'],
                    mode='lines+markers',
                    name='Failed',
                    line=dict(color='red', width=3)
                ))
                fig_success_failed.update_layout(
                    title="Successful vs Failed Transactions",
                    xaxis_title="Hour",
                    yaxis_title="Number of Transactions",
                    height=400
                )
                st.plotly_chart(fig_success_failed, use_container_width=True)
                
                # Success vs Failed analysis
                if not transaction_data.empty:
                    total_success = transaction_data['success_txns'].sum()
                    total_failed = transaction_data['failed_txns'].sum()
                    success_rate = (total_success / (total_success + total_failed)) * 100 if (total_success + total_failed) > 0 else 0
                    
                    st.markdown('<div class="info-alert">', unsafe_allow_html=True)
                    st.write(f"**📊 Success vs Failed Analysis:**")
                    st.write(f"• Successful: {total_success:,} ({success_rate:.1f}%)")
                    st.write(f"• Failed: {total_failed:,} ({100-success_rate:.1f}%)")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Success rate trend over time
            if not transaction_data.empty and 'overall_success_rate' in transaction_data.columns:
                fig_success_trend = go.Figure()
                fig_success_trend.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['overall_success_rate'],
                    mode='lines+markers',
                    name='Success Rate',
                    line=dict(color='blue', width=3),
                    fill='tonexty'
                ))
                fig_success_trend.update_layout(
                    title="Success Rate Trend by Hour",
                    xaxis_title="Hour",
                    yaxis_title="Success Rate (%)",
                    height=400
                )
                st.plotly_chart(fig_success_trend, use_container_width=True)
                
                # Success rate analysis
                if not transaction_data.empty:
                    avg_success_rate = transaction_data['overall_success_rate'].mean()
                    min_success_rate = transaction_data['overall_success_rate'].min()
                    max_success_rate = transaction_data['overall_success_rate'].max()
                    
                    st.markdown('<div class="info-alert">', unsafe_allow_html=True)
                    st.write(f"**📈 Success Rate Analysis:**")
                    st.write(f"• Average: {avg_success_rate:.1f}%")
                    st.write(f"• Range: {min_success_rate:.1f}% - {max_success_rate:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Detailed Metrics Tables
        st.markdown("---")
        st.subheader("📋 Detailed Metrics Tables")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Transaction & GTV Metrics by Hour**")
            if not transaction_data.empty:
                display_cols = ['hour', 'overall_success_rate', 'total_amount_cr', 'success_txns', 'ybl_success_rate', 'nsdl_success_rate']
                available_cols = [col for col in display_cols if col in transaction_data.columns]
                st.dataframe(
                    transaction_data[available_cols].round(2),
                    use_container_width=True
                )
        
        with col2:
            st.write("**Bio-Authentication Success Rates by Hour**")
            if not bio_auth_data.empty:
                display_cols = ['hour', 'fa2_rate_yesterday', 'nsdl_rate_yesterday', 'ybl_rate_yesterday', 'per_user_rate_yesterday']
                available_cols = [col for col in display_cols if col in bio_auth_data.columns]
                st.dataframe(
                    bio_auth_data[available_cols].round(2),
                    use_container_width=True
                )
        
        # Performance Summary Cards
        st.markdown("---")
        st.subheader("📈 Performance Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if not transaction_data.empty:
                avg_success_rate = transaction_data['overall_success_rate'].mean()
                st.metric(
                    "Avg Success Rate",
                    f"{avg_success_rate:.1f}%",
                    delta=f"{'🟢' if avg_success_rate >= 95 else '🟡' if avg_success_rate >= 85 else '🔴'}"
                )
        
        with col2:
            if not transaction_data.empty and 'total_txns' in transaction_data.columns:
                total_transactions = transaction_data['total_txns'].sum()
                st.metric(
                    "Total Transactions",
                    f"{total_transactions:,}",
                    help="Total transactions processed"
                )
        
        with col3:
            if not bio_auth_data.empty:
                avg_bio_rate = bio_auth_data['fa2_rate_yesterday'].mean()
                st.metric(
                    "Avg Bio-Auth Rate",
                    f"{avg_bio_rate:.1f}%",
                    delta=f"{'🟢' if avg_bio_rate >= 95 else '🟡' if avg_bio_rate >= 85 else '🔴'}"
                )
        
        with col4:
            if not transaction_data.empty and 'total_amount_cr' in transaction_data.columns:
                total_gtv = transaction_data['total_amount_cr'].sum()
                st.metric(
                    "Total GTV (Cr)",
                    f"{total_gtv:.2f}",
                    help="Total Gross Transaction Value"
                )
        
        # Download Data Section
        st.markdown("---")
        st.subheader("💾 Download Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not transaction_data.empty:
                st.download_button(
                    label="📥 Download Transaction Data (CSV)",
                    data=transaction_data.to_csv(index=False),
                    file_name=f"transaction_data_{selected_date}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if not bio_auth_data.empty:
                st.download_button(
                    label="📥 Download Bio-Auth Data (CSV)",
                    data=bio_auth_data.to_csv(index=False),
                    file_name=f"bio_auth_data_{selected_date}.csv",
                    mime="text/csv"
                )
        
        # (Removed) Data Coverage Information per user request

elif page == "🗺️ State-wise Metrics":
    # State-wise Metrics Page
    st.markdown("---")
    st.subheader("🗺️ State-wise AEPS Health Metrics")
    
    # Load state metrics data
    state_data = get_bigquery_data("state_metrics", selected_date)
    
    if state_data is not None and not state_data.empty:
        # Filter states doing more than 1 Cr yesterday
        high_volume_states = state_data[state_data['yesterday_gtv'] > 1.0]
        
        # Top Gainers and Losers (states doing > 1 Cr)
        st.markdown("### 📊 Top Movers (States > 1 Cr GTV)")
        
        if not high_volume_states.empty:
            # Calculate gainers and losers
            gainers = high_volume_states[high_volume_states['gtv_vs_median_ratio'] > 1.1].sort_values('gtv_vs_median_ratio', ascending=False).head(5)
            losers = high_volume_states[high_volume_states['gtv_vs_median_ratio'] < 0.9].sort_values('gtv_vs_median_ratio').head(5)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🟢 Top Gainers**")
                if not gainers.empty:
                    gainers_display = gainers[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'gtv_vs_median_ratio']].copy()
                    gainers_display['yesterday_gtv'] = gainers_display['yesterday_gtv'].round(2)
                    gainers_display['median_90d_gtv'] = gainers_display['median_90d_gtv'].round(2)
                    gainers_display['gtv_vs_median_ratio'] = (gainers_display['gtv_vs_median_ratio'] * 100).round(1)
                    gainers_display.columns = ['State', 'Yesterday (Cr)', '90d Median (Cr)', '% vs Median']
                    st.dataframe(gainers_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No significant gainers found")
            
            with col2:
                st.markdown("**🔴 Top Decliners**")
                if not losers.empty:
                    losers_display = losers[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'gtv_vs_median_ratio']].copy()
                    losers_display['yesterday_gtv'] = losers_display['yesterday_gtv'].round(2)
                    losers_display['median_90d_gtv'] = losers_display['median_90d_gtv'].round(2)
                    losers_display['gtv_vs_median_ratio'] = (losers_display['gtv_vs_median_ratio'] * 100).round(1)
                    losers_display.columns = ['State', 'Yesterday (Cr)', '90d Median (Cr)', '% vs Median']
                    st.dataframe(losers_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No significant decliners found")
        else:
            st.info("No states with > 1 Cr GTV yesterday")
        
        st.markdown("---")
        
        # Top 10 States Trend (Last 10 Days)
        st.markdown("### 📈 Top 10 States Trend (Last 10 Days)")
        trend_10d = get_bigquery_data("state_10d_trend", selected_date)
        if trend_10d is not None and not trend_10d.empty:
            # Get top 10 states by average GTV over last 10 days
            top_10_states = trend_10d.groupby('final_state')['gtv'].mean().sort_values(ascending=False).head(10).index.tolist()
            top_10_data = trend_10d[trend_10d['final_state'].isin(top_10_states)]
            
            fig_trend = px.line(top_10_data, x='date', y='gtv', color='final_state', 
                              title="Daily GTV Trend - Top 10 States (Last 10 Days)",
                              markers=True)
            fig_trend.update_layout(height=500)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No trend data available")
        
        st.markdown("---")
        
        # Optional: Individual State 30-day Trend with Median
        st.markdown("### 🎯 Individual State Analysis (30 Days)")
        if trend_10d is not None and not trend_10d.empty:
            available_states = sorted(trend_10d['final_state'].unique())
            selected_state = st.selectbox("Select State for Detailed Analysis", available_states)
            
            if selected_state:
                # Get 30-day trend for selected state
                trend_30d = get_bigquery_data("state_30d_trend", selected_date)
                if trend_30d is not None and not trend_30d.empty:
                    state_30d_data = trend_30d[trend_30d['final_state'] == selected_state].sort_values('date')
                    
                    # Get median for comparison
                    state_median = state_data[state_data['final_state'] == selected_state]['median_90d_gtv'].iloc[0] if not state_data[state_data['final_state'] == selected_state].empty else 0
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_state_gtv = px.line(state_30d_data, x='date', y='gtv', 
                                              title=f"Daily GTV - {selected_state} (30 Days)",
                                              markers=True)
                        if state_median > 0:
                            fig_state_gtv.add_hline(y=state_median, line_dash="dash", line_color="red", 
                                                  annotation_text=f"90d Median: {state_median:.2f} Cr")
                        st.plotly_chart(fig_state_gtv, use_container_width=True)
                    
                    with col2:
                        fig_state_success = px.line(state_30d_data, x='date', y='success_rate', 
                                                  title=f"Daily Success Rate - {selected_state} (30 Days)",
                                                  markers=True)
                        st.plotly_chart(fig_state_success, use_container_width=True)
        
        st.markdown("---")
        
        # Summary Metrics
        st.markdown("### 📊 Summary Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_states = len(state_data)
            st.metric("Total States", total_states)
        
        with col2:
            active_states = len(state_data[state_data['yesterday_gtv'] > 0])
            st.metric("Active States", active_states)
        
        with col3:
            total_gtv = state_data['yesterday_gtv'].sum()
            st.metric("Total GTV (Cr)", f"{total_gtv:.2f}")
        
        with col4:
            avg_success = state_data['yesterday_success_rate'].mean()
            st.metric("Avg Success Rate", f"{avg_success:.1f}%")
        
        # Top States Bar Chart
        st.markdown("### 🏆 Top States by GTV")
        top_states = state_data.head(10)
        fig_top = px.bar(top_states, x='final_state', y='yesterday_gtv', 
                       title="Top 10 States by Yesterday GTV",
                       color='yesterday_gtv', color_continuous_scale='viridis')
        fig_top.update_layout(height=400)
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Business Distribution Pie Chart
        st.markdown("### 🥧 Business Distribution")
        
        # Prepare data for better pie chart
        pie_data = state_data.copy()
        
        # Group states with < 2% GTV into "Others"
        total_gtv = pie_data['yesterday_gtv'].sum()
        pie_data['percentage'] = (pie_data['yesterday_gtv'] / total_gtv * 100).round(2)
        
        # Identify states to group (those with < 2% contribution)
        small_states = pie_data[pie_data['percentage'] < 2.0]
        large_states = pie_data[pie_data['percentage'] >= 2.0]
        
        if len(small_states) > 0:
            # Create "Others" category
            others_gtv = small_states['yesterday_gtv'].sum()
            others_percentage = (others_gtv / total_gtv * 100).round(2)
            
            # Combine large states with "Others"
            final_pie_data = pd.concat([
                large_states[['final_state', 'yesterday_gtv', 'percentage']],
                pd.DataFrame([{
                    'final_state': f'Others ({len(small_states)} states)',
                    'yesterday_gtv': others_gtv,
                    'percentage': others_percentage
                }])
            ])
        else:
            final_pie_data = large_states[['final_state', 'yesterday_gtv', 'percentage']]
        
        # Sort by GTV for better visualization
        final_pie_data = final_pie_data.sort_values('yesterday_gtv', ascending=False)
        
        # Create improved pie chart
        fig_pie = px.pie(
            final_pie_data, 
            values='yesterday_gtv', 
            names='final_state', 
            title="GTV Distribution by State (States < 2% grouped as 'Others')",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.3  # Make it a donut chart for better look
        )
        
        # Improve formatting
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            textfont_size=12,
            hovertemplate="<b>%{label}</b><br>" +
                         "GTV: %{value:.2f} Cr<br>" +
                         "Share: %{percent:.1%}<br>" +
                         "<extra></extra>"
        )
        
        # Update layout for better appearance
        fig_pie.update_layout(
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                font=dict(size=10)
            ),
            margin=dict(l=20, r=200, t=40, b=20)  # Give space for legend
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Add summary table below pie chart
        st.markdown("**📊 Top States Breakdown:**")
        summary_table = final_pie_data[['final_state', 'yesterday_gtv', 'percentage']].copy()
        summary_table.columns = ['State', 'GTV (Cr)', 'Share (%)']
        summary_table = summary_table.round(2)
        st.dataframe(summary_table, use_container_width=True, hide_index=True)
        
        # Variation Analysis
        st.markdown("### 📊 Variation Analysis")
        variation_data = state_data[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'gtv_vs_median_ratio']].copy()
        variation_data['variation'] = ((variation_data['yesterday_gtv'] - variation_data['median_90d_gtv']) / variation_data['median_90d_gtv'] * 100).round(1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Above Median (>10%)**")
            above_median = variation_data[variation_data['variation'] > 10].sort_values('variation', ascending=False)
            if not above_median.empty:
                st.dataframe(above_median[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'variation']].round(2), 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No states significantly above median")
        
        with col2:
            st.markdown("**Below Median (<-10%)**")
            below_median = variation_data[variation_data['variation'] < -10].sort_values('variation')
            if not below_median.empty:
                st.dataframe(below_median[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'variation']].round(2), 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No states significantly below median")
        
        # Threshold Analysis
        st.markdown("### ⚠️ Threshold Analysis")
        threshold_data = state_data[['final_state', 'yesterday_gtv', 'median_90d_gtv', 'stddev_90d_gtv']].copy()
        threshold_data['lower_threshold'] = threshold_data['median_90d_gtv'] - threshold_data['stddev_90d_gtv']
        threshold_data['upper_threshold'] = threshold_data['median_90d_gtv'] + threshold_data['stddev_90d_gtv']
        threshold_data['status'] = 'Normal'
        threshold_data.loc[threshold_data['yesterday_gtv'] < threshold_data['lower_threshold'], 'status'] = 'Below 1σ'
        threshold_data.loc[threshold_data['yesterday_gtv'] > threshold_data['upper_threshold'], 'status'] = 'Above 1σ'
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**States Below 1σ**")
            below_1sigma = threshold_data[threshold_data['status'] == 'Below 1σ'].sort_values('yesterday_gtv')
            if not below_1sigma.empty:
                st.dataframe(below_1sigma[['final_state', 'yesterday_gtv', 'lower_threshold', 'median_90d_gtv']].round(2), 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No states below 1σ threshold")
        
        with col2:
            st.markdown("**States Above 1σ**")
            above_1sigma = threshold_data[threshold_data['status'] == 'Above 1σ'].sort_values('yesterday_gtv', ascending=False)
            if not above_1sigma.empty:
                st.dataframe(above_1sigma[['final_state', 'yesterday_gtv', 'upper_threshold', 'median_90d_gtv']].round(2), 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No states above 1σ threshold")
        
        # Detailed State Metrics Table
        st.markdown("### 📋 Detailed State Metrics")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            min_gtv = st.number_input("Min GTV (Cr)", min_value=0.0, value=0.0, step=0.1)
        with col2:
            min_success = st.number_input("Min Success Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        with col3:
            show_only_active = st.checkbox("Show Only Active States", value=False)
        
        # Apply filters
        filtered_data = state_data.copy()
        if min_gtv > 0:
            filtered_data = filtered_data[filtered_data['yesterday_gtv'] >= min_gtv]
        if min_success > 0:
            filtered_data = filtered_data[filtered_data['yesterday_success_rate'] >= min_success]
        if show_only_active:
            filtered_data = filtered_data[filtered_data['yesterday_gtv'] > 0]
        
        # Display table
        display_cols = ['final_state', 'yesterday_gtv', 'yesterday_transactions', 'yesterday_success_rate', 
                       'median_90d_gtv', 'median_90d_success_rate', 'gtv_vs_median_ratio']
        display_data = filtered_data[display_cols].round(2)
        display_data.columns = ['State', 'Yesterday GTV (Cr)', 'Transactions', 'Success Rate (%)', 
                               '90d Median GTV (Cr)', '90d Median Success (%)', 'GTV vs Median Ratio']
        
        st.dataframe(display_data, use_container_width=True, hide_index=True)
        
        # Download options
        st.markdown("### 💾 Download Data")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv_data,
                file_name=f"state_metrics_{selected_date.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            csv_all = state_data.to_csv(index=False)
            st.download_button(
                label="📥 Download All Data (CSV)",
                data=csv_all,
                file_name=f"state_metrics_all_{selected_date.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    else:
        st.error("❌ Unable to load state metrics data. Please check your BigQuery connection and credentials.")

elif page == "🏦 Bank-wise Health":
    st.markdown("---")
    st.subheader("🏦 Bank-wise Health Metrics by State")

    # Date range controls
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Start date", value=(datetime.now().date() - timedelta(days=30)))
    with col_date2:
        end_date = st.date_input("End date", value=datetime.now().date())

    # Yesterday snapshot
    st.markdown("### 📌 Yesterday Snapshot (Top 25 Banks)")
    bank_yday = get_bigquery_data("bank_yesterday", selected_date)
    if bank_yday is not None and not bank_yday.empty:
        st.dataframe(bank_yday.round(2), use_container_width=True, hide_index=True)
    else:
        st.info("No data found for yesterday.")

    # Fetch range data by formatting the query
    try:
        # Create credentials from environment variables or Streamlit secrets for temporary client
        def get_credential_value_temp(key, default=None):
            """Get credential value from environment variables or Streamlit secrets"""
            # First try environment variables
            env_value = os.getenv(key)
            if env_value:
                return env_value
            
            # Then try Streamlit secrets
            try:
                if hasattr(st, 'secrets'):
                    if key in st.secrets.get('google_credentials', {}):
                        return st.secrets['google_credentials'][key]
                    elif key in st.secrets:
                        return st.secrets[key]
            except Exception:
                pass
            
            return default
        
        credentials_info = {
            "type": get_credential_value_temp('GOOGLE_CREDENTIALS_TYPE', 'service_account'),
            "project_id": get_credential_value_temp('GOOGLE_PROJECT_ID'),
            "private_key_id": get_credential_value_temp('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": get_credential_value_temp('GOOGLE_PRIVATE_KEY', '').replace('\\n', '\n'),
            "client_email": get_credential_value_temp('GOOGLE_CLIENT_EMAIL'),
            "client_id": get_credential_value_temp('GOOGLE_CLIENT_ID'),
            "auth_uri": get_credential_value_temp('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": get_credential_value_temp('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": get_credential_value_temp('GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": get_credential_value_temp('GOOGLE_CLIENT_X509_CERT_URL'),
            "universe_domain": get_credential_value_temp('GOOGLE_UNIVERSE_DOMAIN', 'googleapis.com')
        }
        
        creds = service_account.Credentials.from_service_account_info(
            credentials_info, 
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        client_tmp = bigquery.Client(credentials=creds, project=credentials_info['project_id'])
        bank_health_sql = """
        WITH date_range AS (
          SELECT DATE(@start_date) AS start_date, DATE(@end_date) AS end_date
        ),
        daily_bank_metrics AS (
          SELECT
            v.final_state,
            DATE(a.log_date_time) AS date,
            a.cust_bank_name,
            COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS transaction_count,
            SUM(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.trans_amt END) / 10000000 AS gtv,
            COUNT(CASE WHEN b.spice_message = 'SUCCESS' AND a.trans_amt > 0 THEN a.request_id END) AS success_count,
            COUNT(CASE WHEN a.trans_amt > 0 THEN a.request_id END) AS total_count
          FROM `spicemoney-dwh.prod_dwh.aeps_trans_req` a
          JOIN `spicemoney-dwh.prod_dwh.aeps_trans_res` b ON a.request_id = b.request_id
          JOIN `spicemoney-dwh.analytics_dwh.v_client_pincode` v ON a.client_id = v.retailer_id
          CROSS JOIN date_range dr
          WHERE DATE(a.log_date_time) BETWEEN dr.start_date AND dr.end_date
            AND DATE(b.log_date_time) BETWEEN dr.start_date AND dr.end_date
            AND a.cust_bank_name IS NOT NULL AND v.final_state IS NOT NULL
          GROUP BY v.final_state, DATE(a.log_date_time), a.cust_bank_name
        ),
        bank_performance AS (
          SELECT final_state, cust_bank_name,
                 SUM(gtv) AS total_gtv,
                 SUM(transaction_count) AS total_transactions,
                 SAFE_DIVIDE(SUM(success_count), SUM(total_count)) * 100 AS success_rate,
                 COUNT(DISTINCT date) AS active_days
          FROM daily_bank_metrics
          GROUP BY final_state, cust_bank_name
        ),
        ranked_banks AS (
          SELECT final_state, cust_bank_name, total_gtv, total_transactions, success_rate, active_days,
                 RANK() OVER (PARTITION BY final_state ORDER BY total_gtv DESC) AS rank
          FROM bank_performance
          WHERE total_gtv > 0
        ),
        top_banks AS (
          SELECT final_state, cust_bank_name, total_gtv, total_transactions, success_rate, active_days
          FROM ranked_banks WHERE rank <= 5
        )
        SELECT d.final_state, d.date, d.cust_bank_name, d.transaction_count, d.gtv,
               SAFE_DIVIDE(d.success_count, d.total_count) * 100 AS trans_percentage,
               t.total_gtv AS bank_total_gtv, t.total_transactions AS bank_total_transactions,
               t.success_rate AS bank_success_rate, t.active_days
        FROM daily_bank_metrics d
        JOIN top_banks t ON d.cust_bank_name = t.cust_bank_name AND d.final_state = t.final_state
        ORDER BY d.date DESC, d.final_state, d.gtv DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", str(start_date)),
                bigquery.ScalarQueryParameter("end_date", "DATE", str(end_date)),
            ]
        )
        with st.spinner("🔄 Loading bank metrics for selected range..."):
            bank_health_data = client_tmp.query(bank_health_sql, job_config=job_config).result().to_dataframe()
    except Exception:
        bank_health_data = None

    if bank_health_data is not None and not bank_health_data.empty:
        st.success(f"✅ Showing data from {start_date} to {end_date}")

        # Keep existing downstream visuals which consume filtered_bank_data
        filtered_bank_data = bank_health_data.copy()
    else:
        st.warning("No bank data in selected range; falling back to existing loader.")
        filtered_bank_data = get_bigquery_data("bank_health", selected_date)

    # Continue with the rest of the bank page using filtered_bank_data below

    # Yesterday, pick state (preselect top by yesterday GTV)
    st.markdown("### 🧭 Yesterday State Snapshot")
    by_state_yday = get_bigquery_data("bank_yesterday_by_state", selected_date)
    if by_state_yday is not None and not by_state_yday.empty:
        top_state_row = by_state_yday.groupby('final_state')['gtv'].sum().sort_values(ascending=False).head(1)
        default_state = top_state_row.index[0] if not top_state_row.empty else None
        state_choice = st.selectbox("Select State", options=sorted(by_state_yday['final_state'].unique()), index=sorted(by_state_yday['final_state'].unique()).index(default_state) if default_state else 0)
        st.caption(f"Showing yesterday for: {state_choice}")
        st.dataframe(by_state_yday[by_state_yday['final_state'] == state_choice].sort_values('gtv', ascending=False).round(2), use_container_width=True, hide_index=True)

        # 90-day trend for same state
        st.markdown("### 📈 90-day Trend (same state)")
        trend90 = get_bigquery_data("bank_state_90d_trend", selected_date)
        if trend90 is not None and not trend90.empty:
            tsel = trend90[trend90['final_state'] == state_choice].sort_values('date')
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                fig_gtv_state = px.line(tsel, x='date', y='gtv', title=f"Daily GTV (Cr) - {state_choice}", markers=True)
                st.plotly_chart(fig_gtv_state, use_container_width=True)
            with col_t2:
                fig_succ_state = px.line(tsel, x='date', y='trans_percentage', title=f"Daily Success Rate (%) - {state_choice}", markers=True)
                st.plotly_chart(fig_succ_state, use_container_width=True)
    else:
        st.info("No yesterday state-level data available.")

    st.markdown("---")
    st.subheader("📅 Range Analysis")

else:
    st.error("❌ Unable to load data. Please check your BigQuery connection and credentials.")
    st.info("💡 Make sure the 'spicemoney-dwh.json' credentials file is in the same directory as this app.")

# Footer
st.markdown("---")
st.markdown("*AEPS Health Dashboard - Real-time monitoring of transaction and authentication performance*") 