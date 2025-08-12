import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Google Cloud imports
from google.oauth2 import service_account
from google.cloud import bigquery

# Page configuration
st.set_page_config(
    page_title="AEPS Health Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .anomaly-alert {
        background-color: #ffebee;
        color: #c62828;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #c62828;
    }
    .success-alert {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem;
        border-radius: 0.25rem;
        border-left: 4px solid #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🏥 AEPS Health Dashboard</h1>', unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.header("⚙️ Dashboard Settings")

# Date selection
selected_date = st.sidebar.date_input(
    "Select Date",
    value=datetime.now().date(),
    max_value=datetime.now().date()
)

# Time range selection
time_range = st.sidebar.selectbox(
    "Time Range",
    ["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
    index=0
)

# Refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# BigQuery connection function
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bigquery_data(query_name, selected_date):
    """Fetch data from BigQuery for different health metrics"""
    
    # Check if credentials file exists
    import os
    if not os.path.exists('spicemoney-dwh.json'):
        st.error("❌ BigQuery credentials file 'spicemoney-dwh.json' not found!")
        return None
    
    try:
        # Set up BigQuery connection
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/cloud-platform',
            "https://www.googleapis.com/auth/bigquery"
        ]
        
        credentials = service_account.Credentials.from_service_account_file(
            'spicemoney-dwh.json', 
            scopes=scope
        )
        
        client = bigquery.Client(
            credentials=credentials, 
            project=credentials.project_id
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
            yesterday_data AS (
              SELECT 
                date,
                hour,
                total_amount_cr,
                success_txns,
                ROUND(SAFE_DIVIDE(success_txns, total_txns) * 100, 2) AS overall_success_rate,
                ROUND(SAFE_DIVIDE(ybl_success, ybl_total) * 100, 2) AS ybl_success_rate,
                ROUND(SAFE_DIVIDE(nsdl_success, nsdl_total) * 100, 2) AS nsdl_success_rate,
                ROUND(SAFE_DIVIDE(ybln_success, ybln_total) * 100, 2) AS ybln_success_rate
              FROM hourly_metrics
              WHERE date = today
            ),
            median_sd_data AS (
              SELECT 
                hour,
                ROUND(APPROX_QUANTILES(total_amount_cr, 2)[OFFSET(1)], 2) AS median_amount_cr,
                ROUND(STDDEV_POP(total_amount_cr), 2) AS stddev_amount_cr,
                ROUND(APPROX_QUANTILES(success_txns, 2)[OFFSET(1)], 0) AS median_success_txns,
                ROUND(STDDEV_POP(success_txns), 2) AS stddev_success_txns,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(success_txns, total_txns) * 100, 2)[OFFSET(1)], 2) AS median_success_rate,
                ROUND(STDDEV_POP(SAFE_DIVIDE(success_txns, total_txns) * 100), 2) AS stddev_success_rate,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(ybl_success, ybl_total) * 100, 2)[OFFSET(1)], 2) AS median_ybl_success_rate,
                ROUND(STDDEV_POP(SAFE_DIVIDE(ybl_success, ybl_total) * 100), 2) AS stddev_ybl_success_rate,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(nsdl_success, nsdl_total) * 100, 2)[OFFSET(1)], 2) AS median_nsdl_success_rate,
                ROUND(STDDEV_POP(SAFE_DIVIDE(nsdl_success, nsdl_total) * 100), 2) AS stddev_nsdl_success_rate,
                ROUND(APPROX_QUANTILES(SAFE_DIVIDE(ybln_success, ybln_total) * 100, 2)[OFFSET(1)], 2) AS median_ybln_success_rate,
                ROUND(STDDEV_POP(SAFE_DIVIDE(ybln_success, ybln_total) * 100), 2) AS stddev_ybln_success_rate
              FROM hourly_metrics
              WHERE date BETWEEN last_7_days_start AND last_7_days_end
              GROUP BY hour
            )

            SELECT 
              y.date,
              COALESCE(y.hour, m.hour) AS hour,
              y.total_amount_cr,
              y.success_txns,
              y.overall_success_rate,
              y.ybl_success_rate,
              y.nsdl_success_rate,
              y.ybln_success_rate,
              m.median_amount_cr,
              m.median_success_txns,
              m.median_success_rate,
              m.median_ybl_success_rate,
              m.median_nsdl_success_rate,
              m.median_ybln_success_rate,
              CASE 
                WHEN y.overall_success_rate < m.median_success_rate - stddev_success_rate THEN 'lower anomaly ↓'
                WHEN y.overall_success_rate > m.median_success_rate + stddev_success_rate THEN 'upper anomaly ↑'
                ELSE 'normal'
              END AS success_rate_anomaly
            FROM median_sd_data m
            FULL OUTER JOIN yesterday_data y ON m.hour = y.hour
            ORDER BY hour
            """.format(selected_date),
            
            "bio_auth_success": """
            DECLARE today DATE DEFAULT DATE('{}');
            DECLARE last_7_days_start DATE DEFAULT DATE_SUB(today, INTERVAL 8 DAY);
            DECLARE last_7_days_end DATE DEFAULT DATE_SUB(today, INTERVAL 1 DAY);

            WITH insert_data AS (
              SELECT * 
              FROM `spicemoney-dwh.ds_striim.T_AEPSR_BIO_AUTH_LOGGING_P` 
              WHERE DATE(OP_TIME)  BETWEEN last_7_days_start AND today
                AND OP_NAME = 'INSERT'
            ),
            update_data AS (
              SELECT * 
              FROM `spicemoney-dwh.ds_striim.T_AEPSR_BIO_AUTH_LOGGING_P` 
              WHERE DATE(OP_TIME)  BETWEEN last_7_days_start AND today
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
                hour,date,
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
              CASE 
                WHEN y.fa2_succ_rate < m.median_fa2_succ_rate - stddev_succ_rate THEN 'Lower Anomaly ↓'
                WHEN y.fa2_succ_rate > m.median_fa2_succ_rate + stddev_succ_rate THEN 'Upper Anomaly ↑'
                WHEN y.fa2_succ_rate IS NULL THEN 'No Data'
                ELSE 'Normal'
              END AS fa2_succ_flag
            FROM median_data m
            FULL OUTER JOIN yesterday_data y ON m.hour = y.hour
            ORDER BY hour
            """.format(selected_date)
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
    bio_auth_data = get_bigquery_data("bio_auth_success", selected_date)

with col3:
    st.info("📊 Loading device performance and error analysis data...")

# Main dashboard content
if transaction_data is not None and bio_auth_data is not None:
    
    # Overall Health Score
    st.markdown("---")
    st.subheader("🏥 Overall AEPS Health Score")
    
    # Calculate health scores
    if not transaction_data.empty:
        avg_transaction_success = transaction_data['overall_success_rate'].mean()
        transaction_health_score = min(100, max(0, avg_transaction_success))
        
        # Calculate GTV metrics
        total_gtv = transaction_data['total_amount_cr'].sum() if 'total_amount_cr' in transaction_data.columns else 0
        avg_gtv_per_hour = transaction_data['total_amount_cr'].mean() if 'total_amount_cr' in transaction_data.columns else 0
        median_gtv = transaction_data['median_amount_cr'].mean() if 'median_amount_cr' in transaction_data.columns else 0
    else:
        transaction_health_score = 0
        total_gtv = 0
        avg_gtv_per_hour = 0
        median_gtv = 0
    
    if not bio_auth_data.empty:
        avg_bio_success = bio_auth_data['fa2_rate_yesterday'].mean()
        bio_health_score = min(100, max(0, avg_bio_success))
    else:
        bio_health_score = 0
    
    overall_health_score = (transaction_health_score * 0.7 + bio_health_score * 0.3)
    
    # Health score visualization
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Overall Health Score",
            value=f"{overall_health_score:.1f}%",
            delta=f"{'🟢' if overall_health_score >= 90 else '🟡' if overall_health_score >= 75 else '🔴'}"
        )
    
    with col2:
        st.metric(
            label="Transaction Success",
            value=f"{transaction_health_score:.1f}%",
            delta=f"{'🟢' if transaction_health_score >= 95 else '🟡' if transaction_health_score >= 85 else '🔴'}"
        )
    
    with col3:
        st.metric(
            label="Bio-Auth Success",
            value=f"{bio_health_score:.1f}%",
            delta=f"{'🟢' if bio_health_score >= 90 else '🟡' if bio_health_score >= 80 else '🔴'}"
        )
    
    with col4:
        st.metric(
            label="Total GTV (Cr)",
            value=f"{total_gtv:.1f}",
            delta=f"{'📈' if total_gtv > median_gtv * 24 else '📉' if total_gtv < median_gtv * 20 else '➡️'}"
        )
    
    with col5:
        # Count anomalies
        transaction_anomalies = len(transaction_data[transaction_data['success_rate_anomaly'] != 'normal']) if not transaction_data.empty else 0
        bio_anomalies = len(bio_auth_data[bio_auth_data['fa2_succ_flag'] != 'Normal']) if not bio_auth_data.empty else 0
        total_anomalies = transaction_anomalies + bio_anomalies
        
        st.metric(
            label="Active Anomalies",
            value=total_anomalies,
            delta=f"{'🔴' if total_anomalies > 5 else '🟡' if total_anomalies > 0 else '🟢'}"
        )
    
    # GTV and Transaction Trends
    st.markdown("---")
    st.subheader("💰 GTV & Transaction Performance")
    
    if not transaction_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # GTV trend
            if 'total_amount_cr' in transaction_data.columns:
                fig_gtv = go.Figure()
                fig_gtv.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['total_amount_cr'],
                    mode='lines+markers',
                    name='Current GTV',
                    line=dict(color='green', width=2)
                ))
                if 'median_amount_cr' in transaction_data.columns:
                    fig_gtv.add_trace(go.Scatter(
                        x=transaction_data['hour'],
                        y=transaction_data['median_amount_cr'],
                        mode='lines',
                        name='7-Day Median GTV',
                        line=dict(color='gray', width=1, dash='dash')
                    ))
                fig_gtv.update_layout(
                    title="Gross Transaction Value (GTV) - Crores",
                    xaxis_title="Hour",
                    yaxis_title="GTV (Crores)",
                    height=400
                )
                st.plotly_chart(fig_gtv, use_container_width=True)
            else:
                st.info("GTV data not available")
        
        with col2:
            # Transaction volume trend
            if 'success_txns' in transaction_data.columns:
                fig_vol = go.Figure()
                fig_vol.add_trace(go.Scatter(
                    x=transaction_data['hour'],
                    y=transaction_data['success_txns'],
                    mode='lines+markers',
                    name='Successful Transactions',
                    line=dict(color='blue', width=2)
                ))
                if 'median_success_txns' in transaction_data.columns:
                    fig_vol.add_trace(go.Scatter(
                        x=transaction_data['hour'],
                        y=transaction_data['median_success_txns'],
                        mode='lines',
                        name='7-Day Median',
                        line=dict(color='gray', width=1, dash='dash')
                    ))
                fig_vol.update_layout(
                    title="Transaction Volume",
                    xaxis_title="Hour",
                    yaxis_title="Number of Transactions",
                    height=400
                )
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info("Transaction volume data not available")
    
    # Transaction Success Rate Trends
    st.markdown("---")
    st.subheader("📈 Transaction Success Rate Trends")
    
    if not transaction_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Overall success rate trend
            fig_overall = go.Figure()
            fig_overall.add_trace(go.Scatter(
                x=transaction_data['hour'],
                y=transaction_data['overall_success_rate'],
                mode='lines+markers',
                name='Current',
                line=dict(color='blue', width=2)
            ))
            fig_overall.add_trace(go.Scatter(
                x=transaction_data['hour'],
                y=transaction_data['median_success_rate'],
                mode='lines',
                name='7-Day Median',
                line=dict(color='gray', width=1, dash='dash')
            ))
            fig_overall.update_layout(
                title="Overall Transaction Success Rate",
                xaxis_title="Hour",
                yaxis_title="Success Rate (%)",
                height=400
            )
            st.plotly_chart(fig_overall, use_container_width=True)
        
        with col2:
            # Aggregator comparison
            fig_agg = go.Figure()
            fig_agg.add_trace(go.Scatter(
                x=transaction_data['hour'],
                y=transaction_data['ybl_success_rate'],
                mode='lines+markers',
                name='YBL',
                line=dict(color='green', width=2)
            ))
            fig_agg.add_trace(go.Scatter(
                x=transaction_data['hour'],
                y=transaction_data['nsdl_success_rate'],
                mode='lines+markers',
                name='NSDL',
                line=dict(color='red', width=2)
            ))
            fig_agg.add_trace(go.Scatter(
                x=transaction_data['hour'],
                y=transaction_data['ybln_success_rate'],
                mode='lines+markers',
                name='YBLN',
                line=dict(color='orange', width=2)
            ))
            fig_agg.update_layout(
                title="Success Rate by Aggregator",
                xaxis_title="Hour",
                yaxis_title="Success Rate (%)",
                height=400
            )
            st.plotly_chart(fig_agg, use_container_width=True)
    
    # Bio-Authentication Trends
    st.markdown("---")
    st.subheader("🔐 Bio-Authentication Success Trends")
    
    if not bio_auth_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Overall bio-auth success rate
            fig_bio = go.Figure()
            fig_bio.add_trace(go.Scatter(
                x=bio_auth_data['hour'],
                y=bio_auth_data['fa2_rate_yesterday'],
                mode='lines+markers',
                name='Current',
                line=dict(color='purple', width=2)
            ))
            fig_bio.add_trace(go.Scatter(
                x=bio_auth_data['hour'],
                y=bio_auth_data['median_fa2_succ_rate'],
                mode='lines',
                name='7-Day Median',
                line=dict(color='gray', width=1, dash='dash')
            ))
            fig_bio.update_layout(
                title="Bio-Authentication Success Rate",
                xaxis_title="Hour",
                yaxis_title="Success Rate (%)",
                height=400
            )
            st.plotly_chart(fig_bio, use_container_width=True)
        
        with col2:
            # Per-user authentication rate
            fig_user = go.Figure()
            fig_user.add_trace(go.Scatter(
                x=bio_auth_data['hour'],
                y=bio_auth_data['per_user_rate_yesterday'],
                mode='lines+markers',
                name='Current',
                line=dict(color='brown', width=2)
            ))
            fig_user.add_trace(go.Scatter(
                x=bio_auth_data['hour'],
                y=bio_auth_data['median_fa2_per_user_rate'],
                mode='lines',
                name='7-Day Median',
                line=dict(color='gray', width=1, dash='dash')
            ))
            fig_user.update_layout(
                title="Per-User Authentication Rate",
                xaxis_title="Hour",
                yaxis_title="Rate",
                height=400
            )
            st.plotly_chart(fig_user, use_container_width=True)
    
    # Anomaly Alerts
    st.markdown("---")
    st.subheader("🚨 Anomaly Alerts")
    
    # Transaction anomalies
    if not transaction_data.empty:
        transaction_anomalies = transaction_data[transaction_data['success_rate_anomaly'] != 'normal']
        gtv_anomalies = transaction_data[transaction_data['amount_cr_anomaly'] != 'normal'] if 'amount_cr_anomaly' in transaction_data.columns else pd.DataFrame()
        
        if not transaction_anomalies.empty:
            st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
            st.write("**Transaction Success Rate Anomalies:**")
            for _, row in transaction_anomalies.iterrows():
                st.write(f"• Hour {row['hour']}: {row['success_rate_anomaly']} (Rate: {row['overall_success_rate']:.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        if not gtv_anomalies.empty:
            st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
            st.write("**GTV Anomalies:**")
            for _, row in gtv_anomalies.iterrows():
                gtv_value = row.get('total_amount_cr', 0)
                st.write(f"• Hour {row['hour']}: {row['amount_cr_anomaly']} (GTV: {gtv_value:.1f} Cr)")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Bio-auth anomalies
    if not bio_auth_data.empty:
        bio_anomalies = bio_auth_data[bio_auth_data['fa2_succ_flag'] != 'Normal']
        if not bio_anomalies.empty:
            st.markdown('<div class="anomaly-alert">', unsafe_allow_html=True)
            st.write("**Bio-Authentication Anomalies:**")
            for _, row in bio_anomalies.iterrows():
                st.write(f"• Hour {row['hour']}: {row['fa2_succ_flag']} (Rate: {row['fa2_rate_yesterday']:.1f}%)")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # If no anomalies
    if (transaction_data.empty or transaction_data[transaction_data['success_rate_anomaly'] != 'normal'].empty) and \
       (bio_auth_data.empty or bio_auth_data[bio_auth_data['fa2_succ_flag'] != 'Normal'].empty):
        st.markdown('<div class="success-alert">', unsafe_allow_html=True)
        st.write("✅ **No anomalies detected in the current time period.**")
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

else:
    st.error("❌ Unable to load data. Please check your BigQuery connection and credentials.")
    st.info("💡 Make sure the 'spicemoney-dwh.json' credentials file is in the same directory as this app.")

# Footer
st.markdown("---")
st.markdown("*AEPS Health Dashboard - Real-time monitoring of transaction and authentication performance*") 