# AEPS Health Dashboard - Deployment Guide

## 🚀 **Option 1: Streamlit Cloud (Recommended)**

### **Step 1: Prepare Your Repository**
1. **Create a GitHub repository** with your dashboard files:
   ```
   aeps-health-dashboard/
   ├── aeps_health_dashboard.py
   ├── requirements.txt
   ├── README.md
   └── spicemoney-dwh.json (credentials)
   ```

### **Step 2: Deploy to Streamlit Cloud**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository and main file (`aeps_health_dashboard.py`)
5. Deploy!

**✅ Benefits:**
- Free hosting
- Automatic HTTPS
- Custom domain support
- Team access controls
- Automatic deployments from GitHub

**🔗 Your dashboard will be available at:**
`https://your-app-name.streamlit.app`

---

## 🏢 **Option 2: Internal Network Deployment**

### **Step 1: Deploy on Internal Server**
```bash
# On your internal server
streamlit run aeps_health_dashboard.py --server.port 8501 --server.address 0.0.0.0
```

### **Step 2: Configure Network Access**
- **Internal URL**: `http://your-server-ip:8501`
- **Domain**: `http://aeps-dashboard.your-company.com` (if you have internal DNS)

### **Step 3: Set up Reverse Proxy (Optional)**
```nginx
# Nginx configuration
server {
    listen 80;
    server_name aeps-dashboard.your-company.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ☁️ **Option 3: Cloud Deployment**

### **Google Cloud Run**
```bash
# Create Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "aeps_health_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### **Deploy to Cloud Run**
```bash
gcloud run deploy aeps-dashboard \
  --source . \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated
```

---

## 🔐 **Security Considerations**

### **1. Credentials Management**
```python
# Use environment variables instead of file
import os
credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'spicemoney-dwh.json')
```

### **2. Access Control**
```python
# Add authentication to your dashboard
import streamlit as st

def check_authentication():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("Enter Dashboard Password", type="password")
        if password == "your-secure-password":
            st.session_state.authenticated = True
        else:
            st.stop()

# Add this at the top of your dashboard
check_authentication()
```

### **3. IP Whitelisting**
```python
# Restrict access to company IPs
ALLOWED_IPS = ['192.168.1.0/24', '10.0.0.0/8']  # Your company IP ranges

def check_ip_access():
    # Implement IP checking logic
    pass
```

---

## 📧 **Option 4: Email Integration**

### **Daily Health Reports**
```python
# Add to your dashboard
def send_daily_report():
    # Generate PDF report
    # Send via email to stakeholders
    pass

# Schedule with cron or cloud scheduler
```

---

## 🔄 **Option 5: Automated Deployment**

### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy Dashboard
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Streamlit Cloud
      run: |
        # Deploy commands
```

---

## 📊 **Recommended Setup for Your Organization:**

### **Phase 1: Quick Start**
1. **Deploy to Streamlit Cloud** (immediate access)
2. **Share the public URL** with your team
3. **Set up basic authentication**

### **Phase 2: Production**
1. **Move to internal server** for better security
2. **Set up custom domain**
3. **Implement proper access controls**
4. **Add monitoring and alerts**

### **Phase 3: Enterprise**
1. **Deploy to cloud infrastructure**
2. **Set up CI/CD pipeline**
3. **Add advanced security features**
4. **Integrate with company SSO**

---

## 🎯 **Next Steps:**

1. **Choose your deployment option**
2. **Set up the infrastructure**
3. **Configure security**
4. **Share with your team**
5. **Monitor usage and feedback**

**Need help with any specific deployment option? Let me know!** 