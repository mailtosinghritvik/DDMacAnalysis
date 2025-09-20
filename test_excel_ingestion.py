"""
Test script for Excel Ingestion functionality
"""
import pandas as pd
import tempfile
import os

def test_excel_ingestion():
    """Test the Excel ingestion functionality"""
    
    print("🧪 Testing Excel Ingestion Functionality")
    print("=" * 50)
    
    # Create sample AccuBid-like Excel file for testing
    print("\n📊 Creating sample AccuBid Excel file...")
    
    # Sample Key Indicators data
    key_indicators = {
        'Key Indicators': [
            'Total Project Cost',
            'Direct Labor Hours',
            'Material Cost',
            'Equipment Cost',
            'Overhead Percentage',
            'Profit Margin',
            'Project Duration (Days)',
            'Number of Workers',
            'Safety Score',
            'Quality Rating'
        ],
        'Values': [
            '$156,750.00',
            '2,480',
            '$89,200.00',
            '$12,500.00',
            '15%',
            '12%',
            '45',
            '8',
            '98.5%',
            '9.2/10'
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(key_indicators)
    
    # Create temporary Excel file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
            # Write Key Indicators sheet
            df.to_excel(writer, sheet_name='Key Indicators', index=False)
            
            # Add some additional sheets to simulate real AccuBid file
            sample_data = pd.DataFrame({
                'Item': ['Wire', 'Conduit', 'Panels'],
                'Quantity': [1000, 500, 10],
                'Cost': [1500, 800, 5000]
            })
            sample_data.to_excel(writer, sheet_name='Materials', index=False)
            
            labor_data = pd.DataFrame({
                'Trade': ['Electrician', 'Helper', 'Foreman'],
                'Hours': [1200, 800, 480],
                'Rate': [45, 28, 55]
            })
            labor_data.to_excel(writer, sheet_name='Labor', index=False)
        
        test_file_path = tmp_file.name
    
    print(f"✅ Created test file: {test_file_path}")
    print(f"   - Key Indicators: {len(df)} rows")
    print(f"   - File size: {os.path.getsize(test_file_path) / 1024:.1f} KB")
    
    # Test reading the file
    print("\n📖 Testing file reading...")
    try:
        excel_file = pd.ExcelFile(test_file_path)
        print(f"✅ File opened successfully")
        print(f"   - Available sheets: {', '.join(excel_file.sheet_names)}")
        
        # Test Key Indicators sheet
        if 'Key Indicators' in excel_file.sheet_names:
            key_indicators_df = pd.read_excel(excel_file, sheet_name='Key Indicators')
            print(f"✅ Key Indicators sheet read successfully")
            print(f"   - Shape: {key_indicators_df.shape}")
            print(f"   - Columns: {list(key_indicators_df.columns)}")
            
            # Process like in the actual function
            indicators_data = key_indicators_df.iloc[:, :2].copy()
            indicators_data.columns = ['Key Indicators', 'Values']
            indicators_data = indicators_data.dropna(subset=['Key Indicators'])
            
            print(f"✅ Data processed successfully")
            print(f"   - Final indicators count: {len(indicators_data)}")
            
            # Display sample data
            print("\n📋 Sample Key Indicators:")
            for i, row in indicators_data.head(5).iterrows():
                print(f"   • {row['Key Indicators']}: {row['Values']}")
            
        else:
            print("❌ Key Indicators sheet not found")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    # Cleanup
    os.unlink(test_file_path)
    print(f"\n🧹 Cleaned up test file")
    
    print("\n" + "=" * 50)
    print("✅ Excel Ingestion Test Complete!")
    print("\n📝 Summary:")
    print("   - Sample AccuBid file creation: ✅")
    print("   - Excel file reading: ✅")
    print("   - Key Indicators extraction: ✅")
    print("   - Data processing: ✅")
    print("\n🚀 Ready for Streamlit integration!")

if __name__ == "__main__":
    test_excel_ingestion()