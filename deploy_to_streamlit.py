#!/usr/bin/env python3
"""
AEPS Health Dashboard - Streamlit Cloud Deployment Helper
This script helps you prepare and deploy your dashboard to Streamlit Cloud.
"""

import os
import subprocess
import sys

def print_step(step_num, title, description):
    """Print a formatted step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")
    print(description)
    print()

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'aeps_health_dashboard_secure.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        '.streamlit/config.toml'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found!")
    return True

def check_credentials():
    """Check if credentials file exists"""
    if not os.path.exists('spicemoney-dwh.json'):
        print("⚠️  Warning: spicemoney-dwh.json not found!")
        print("   You'll need to add this file to your repository for BigQuery access.")
        return False
    
    print("✅ Credentials file found!")
    return True

def main():
    print("🚀 AEPS Health Dashboard - Streamlit Cloud Deployment")
    print("=" * 60)
    
    # Step 1: Check files
    print_step(1, "File Check", "Verifying all required files are present...")
    if not check_requirements():
        print("❌ Please ensure all required files are in the current directory.")
        return
    
    check_credentials()
    
    # Step 2: Git setup
    print_step(2, "Git Repository Setup", """
1. Create a new GitHub repository:
   - Go to https://github.com/new
   - Name it: aeps-health-dashboard
   - Make it private (recommended for security)
   - Don't initialize with README (we already have one)

2. Initialize git and push your code:
   git init
   git add .
   git commit -m "Initial commit: AEPS Health Dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aeps-health-dashboard.git
   git push -u origin main
    """)
    
    # Step 3: Streamlit Cloud deployment
    print_step(3, "Streamlit Cloud Deployment", """
1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click "New app"
4. Configure your app:
   - Repository: YOUR_USERNAME/aeps-health-dashboard
   - Branch: main
   - Main file path: aeps_health_dashboard_secure.py
   - App URL: aeps-health-dashboard (or your preferred name)

5. Click "Deploy app"
    """)
    
    # Step 4: Environment variables
    print_step(4, "Environment Variables Setup", """
1. In your Streamlit Cloud app settings:
2. Go to "Settings" → "Secrets"
3. Add the following secrets:

   [secrets]
   DASHBOARD_PASSWORD = "your-secure-password-here"
   GOOGLE_CREDENTIALS_PATH = "spicemoney-dwh.json"

4. Upload your spicemoney-dwh.json file to the secrets
    """)
    
    # Step 5: Security setup
    print_step(5, "Security Configuration", """
1. Set a strong dashboard password
2. Share the dashboard URL with your team
3. Monitor access and usage
4. Consider setting up additional security measures:
   - IP whitelisting
   - SSO integration
   - Access logging
    """)
    
    # Step 6: Testing
    print_step(6, "Testing Your Deployment", """
1. Access your dashboard at: https://your-app-name.streamlit.app
2. Test authentication with your password
3. Verify data loading from BigQuery
4. Check all dashboard features work correctly
5. Test on different devices/browsers
    """)
    
    print("\n" + "="*60)
    print("🎉 DEPLOYMENT COMPLETE!")
    print("="*60)
    print("""
Your AEPS Health Dashboard is now live and accessible to your organization!

🔗 Dashboard URL: https://your-app-name.streamlit.app
🔐 Password: (the one you set in environment variables)

📧 Share this information with your team:
- Dashboard URL
- Login credentials
- Usage guidelines

🔄 For updates:
- Push changes to your GitHub repository
- Streamlit Cloud will automatically redeploy

📞 Need help? Check the README.md file for troubleshooting.
    """)

if __name__ == "__main__":
    main() 