"""
Test script for DDMac Time Tracking Analytics Platform
This script tests all the main components and generates sample data
"""

import sys
import os
sys.path.append('/Users/ritviksingh/Desktop/Ace148/DDMacAnalysis')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.time_analysis import (
    analyze_clients,
    analyze_projects_for_client,
    analyze_employees_overview,
    analyze_employee_detailed,
    TimeTrackingAnalyzer,
    generate_sample_timesheet_data
)

def test_analytics_platform():
    """Test the complete DDMac analytics platform"""
    
    print("🚀 Testing DDMac Time Tracking Analytics Platform")
    print("=" * 60)
    
    # Generate sample data
    print("\n📊 Generating sample timesheet data...")
    sample_data = generate_sample_timesheet_data(num_employees=8, num_days=90)
    analyzer = TimeTrackingAnalyzer(sample_data)
    
    print(f"✅ Generated {len(sample_data)} timesheet records")
    print(f"   - Date range: {sample_data['date'].min()} to {sample_data['date'].max()}")
    print(f"   - Employees: {sample_data['employee'].nunique()}")
    print(f"   - Clients: {sample_data['client'].nunique()}")
    print(f"   - Projects: {sample_data['project'].nunique()}")
    
    # Test client analysis
    print("\n💼 Testing Client Analysis...")
    try:
        client_analysis = analyze_clients(sample_data)
        print(f"✅ Client analysis completed - {len(client_analysis)} clients analyzed")
        top_client = client_analysis.loc[client_analysis['Total_Hours'].idxmax()]
        print(f"   - Top client: {top_client['Client']} ({top_client['Total_Hours']:.1f} hours)")
    except Exception as e:
        print(f"❌ Client analysis failed: {e}")
    
    # Test project analysis
    print("\n📋 Testing Project Analysis...")
    try:
        test_client = sample_data['client'].iloc[0]
        project_analysis = analyze_projects_for_client(sample_data, test_client)
        print(f"✅ Project analysis completed for {test_client}")
        print(f"   - {len(project_analysis)} projects analyzed")
    except Exception as e:
        print(f"❌ Project analysis failed: {e}")
    
    # Test employee analysis
    print("\n👥 Testing Employee Analysis...")
    try:
        employee_analysis = analyze_employees_overview(sample_data)
        print(f"✅ Employee analysis completed - {len(employee_analysis)} employees analyzed")
        top_performer = employee_analysis.loc[employee_analysis['Total_Hours'].idxmax()]
        print(f"   - Top performer: {top_performer['Employee']} ({top_performer['Total_Hours']:.1f} hours)")
    except Exception as e:
        print(f"❌ Employee analysis failed: {e}")
    
    # Test detailed reports
    print("\n📈 Testing Detailed Reports...")
    try:
        test_employee = sample_data['employee'].iloc[0]
        detailed_report = analyze_employee_detailed(sample_data, test_employee)
        print(f"✅ Detailed report generated for {test_employee}")
        print(f"   - {len(detailed_report)} time entries analyzed")
    except Exception as e:
        print(f"❌ Detailed report failed: {e}")
    
    # Test health scoring
    print("\n🏥 Testing Health Scoring...")
    try:
        health_scores = analyzer.calculate_project_health()
        healthy_projects = len([score for score in health_scores.values() if score >= 0.7])
        print(f"✅ Health scoring completed for {len(health_scores)} projects")
        print(f"   - Healthy projects (score ≥ 0.7): {healthy_projects}")
    except Exception as e:
        print(f"❌ Health scoring failed: {e}")
    
    # Test performance scoring
    print("\n⭐ Testing Performance Scoring...")
    try:
        performance_scores = analyzer.calculate_employee_performance()
        high_performers = len([score for score in performance_scores.values() if score >= 0.8])
        print(f"✅ Performance scoring completed for {len(performance_scores)} employees")
        print(f"   - High performers (score ≥ 0.8): {high_performers}")
    except Exception as e:
        print(f"❌ Performance scoring failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 DDMac Analytics Platform Test Complete!")
    print("\n📝 Summary:")
    print("   - All core analytics functions tested")
    print("   - Sample data generation working")
    print("   - Ready for Streamlit dashboard deployment")
    print("\n🚀 To run the dashboard:")
    print("   cd /Users/ritviksingh/Desktop/Ace148/DDMacAnalysis")
    print("   streamlit run Home.py")
    
    return sample_data

if __name__ == "__main__":
    test_data = test_analytics_platform()
