# 🏥 AEPS Health Dashboard - User Guide

## 📋 What is the AEPS Health Dashboard?

The **AEPS Health Dashboard** is a real-time monitoring system that tracks the performance and health of **Aadhaar Enabled Payment System (AEPS)** transactions. It provides comprehensive insights into transaction success rates, bio-authentication performance, and system anomalies to help you monitor business operations effectively.

---

## 🎯 Key Features at a Glance

| Feature | Description | What You Get |
|---------|-------------|--------------|
| **🔍 Real-time Monitoring** | Live tracking of AEPS transactions | Current system health status |
| **📊 Multi-dimensional Analysis** | Transaction, Bio-auth, State & Bank views | Complete business visibility |
| **🚨 Anomaly Detection** | Automatic alerts for unusual patterns | Proactive issue identification |
| **📈 Historical Trends** | 7-90 day performance comparisons | Data-driven decision making |
| **🗺️ Geographic Insights** | State-wise performance breakdown | Regional business intelligence |

---

## 🎛️ Dashboard Navigation

### **Main Pages**
1. **🏥 Health Overview** - Real-time system health and performance metrics
2. **🗺️ State-wise Metrics** - Geographic performance analysis and trends  
3. **🏦 Bank-wise Health** - Bank performance metrics and comparisons

### **Key Controls (Sidebar)**
- **📅 Date Selection**: Choose specific date for analysis
- **⏰ Time Range**: Filter by hours (0-23) for detailed analysis
- **🏦 Aggregator Filter**: Select YBL, NSDL, YBLN for focused view
- **🎚️ Anomaly Sensitivity**: Adjust alert threshold (1-3 standard deviations)
- **🔄 Auto-refresh**: Enable automatic data updates (1-60 minutes)

---

## 📊 Understanding the Metrics

### **Health Scores** 🎯
- **Overall Health**: Weighted score (70% transactions + 30% bio-auth)
- **🟢 Green (90%+)**: Excellent performance
- **🟡 Yellow (75-89%)**: Good performance, monitor closely
- **🔴 Red (<75%)**: Requires immediate attention

### **Transaction Metrics** 💳
- **Success Rate**: Percentage of successful transactions
- **GTV (Gross Transaction Value)**: Total transaction value in Crores
- **Volume**: Number of transactions processed
- **Aggregator Performance**: YBL, NSDL, YBLN individual success rates

### **Bio-Authentication Metrics** 🔐
- **FA2 Success Rate**: Fingerprint authentication success percentage
- **Per-User Rate**: Average authentication attempts per user
- **Aggregator Breakdown**: Bio-auth performance by provider

---

## 🚨 Alert System

### **Anomaly Types**
| Alert | Meaning | Action Required |
|-------|---------|-----------------|
| **🔴 Lower Anomaly ↓** | Performance below normal range | Investigate immediately |
| **🟡 Upper Anomaly ↑** | Performance above normal range | Monitor for sustainability |
| **✅ Normal** | Performance within expected range | Continue monitoring |

### **When to Act**
- **Immediate**: Red alerts, success rates <85%, GTV drops >20%
- **Monitor**: Yellow alerts, unusual spikes, aggregator imbalances
- **Review**: Weekly trends, state-wise variations, bank performance

---

## 🗺️ State-wise Analysis Features

### **Top Movers Section**
- **🟢 Top Gainers**: States performing above 90-day median
- **🔴 Top Decliners**: States underperforming compared to historical data
- **📊 Threshold Analysis**: States outside 1σ (standard deviation) range

### **Trend Analysis**
- **10-Day Trend**: Recent performance patterns
- **30-Day Deep Dive**: Individual state detailed analysis
- **Business Distribution**: GTV share by state (pie chart)

---

## 🏦 Bank-wise Health Insights

### **Performance Metrics**
- **Yesterday Snapshot**: Top 25 banks by GTV
- **Range Analysis**: Custom date range performance
- **Success Rate Tracking**: Bank-specific transaction success rates
- **90-Day Trends**: Long-term bank performance patterns

---

## 💡 How to Use the Dashboard Effectively

### **Daily Monitoring Checklist** ✅
1. Check **Overall Health Score** - should be >90%
2. Review **Anomaly Alerts** - investigate any red flags
3. Monitor **Aggregator Performance** - ensure balanced load
4. Verify **Top States** - watch for unusual patterns
5. Check **GTV Trends** - compare with historical averages

### **Weekly Review Process** 📅
1. Analyze **7-day trends** for performance patterns
2. Review **state-wise variations** for regional issues
3. Compare **bank performance** across different providers
4. Identify **improvement opportunities** from data insights

### **Monthly Strategic Analysis** 📈
1. Review **30-day trends** for long-term patterns
2. Analyze **seasonal variations** in performance
3. Evaluate **aggregator relationships** and performance
4. Plan **capacity and infrastructure** based on growth trends

---

## 🔧 Quick Troubleshooting

| Issue | Possible Cause | Quick Fix |
|-------|---------------|-----------|
| **No data showing** | Date/time filter too restrictive | Expand date range or reset filters |
| **Low success rates** | System issues or high load | Check aggregator status, review logs |
| **Missing states** | Data connectivity issues | Refresh dashboard, check data source |
| **Slow loading** | Large date range selected | Reduce time range, use auto-refresh wisely |

---

## 📞 Support & Contact

- **Technical Issues**: Contact IT Support Team
- **Data Questions**: Reach out to Analytics Team  
- **Feature Requests**: Submit via internal ticketing system
- **Dashboard Access**: Contact System Administrator

---

**💡 Pro Tip**: Bookmark the dashboard and set up auto-refresh for continuous monitoring during business hours. Use the download feature to export data for detailed offline analysis and reporting.

---

*Last Updated: December 2024 | Version 2.0 | AEPS Health Monitoring System*