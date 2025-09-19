"""
Generate sample AccuBid Excel file for testing the Excel Ingestion page
"""
import pandas as pd
import os

def create_sample_accubid_file():
    """Create a sample AccuBid Excel file with Key Indicators sheet"""
    
    # Sample Key Indicators data (realistic AccuBid values)
    key_indicators = {
        'Key Indicators': [
            'Total Project Cost',
            'Direct Labor Cost', 
            'Direct Labor Hours',
            'Material Cost',
            'Equipment Rental',
            'Subcontractor Cost',
            'General Expenses',
            'Labor Factor',
            'Overhead Percentage',
            'Profit Margin',
            'Project Duration (Days)',
            'Crew Size',
            'Safety Score',
            'Efficiency Rating',
            'Change Orders',
            'Total Square Footage',
            'Cost per Square Foot',
            'Electrical Loads (Amps)',
            'Number of Circuits',
            'Panel Count'
        ],
        'Values': [
            '$245,750.00',
            '$98,300.00',
            '2,186',
            '$89,200.00',
            '$15,500.00',
            '$23,800.00',
            '$8,950.00',
            '1.15',
            '18%',
            '12%',
            '52',
            '6',
            '96.8%',
            '8.7/10',
            '3',
            '12,500',
            '$19.66',
            '800',
            '48',
            '4'
        ]
    }
    
    # Additional realistic AccuBid sheets
    materials_data = {
        'Description': [
            '12 AWG THWN Wire - 600V',
            '3/4" EMT Conduit',
            '1" EMT Conduit', 
            '200A Main Panel',
            '20A Circuit Breakers',
            'Wire Nuts #12',
            'Receptacles - 20A GFCI',
            'Light Fixtures - LED 4ft',
            'Junction Boxes - 4x4',
            'Cable Tray - 12" wide'
        ],
        'Quantity': [5000, 800, 400, 1, 24, 200, 45, 32, 28, 150],
        'Unit': ['ft', 'ft', 'ft', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ft'],
        'Unit_Cost': [0.85, 2.45, 3.20, 1250.00, 28.50, 0.15, 45.00, 125.00, 8.50, 12.75],
        'Total_Cost': [4250.00, 1960.00, 1280.00, 1250.00, 684.00, 30.00, 2025.00, 4000.00, 238.00, 1912.50]
    }
    
    labor_data = {
        'Trade': [
            'Journeyman Electrician',
            'Electrical Helper', 
            'Foreman',
            'Apprentice Level 3',
            'Apprentice Level 1'
        ],
        'Hours': [1200, 600, 240, 300, 146],
        'Rate': [48.50, 32.00, 58.00, 42.00, 28.00],
        'Total_Cost': [58200.00, 19200.00, 13920.00, 12600.00, 4088.00]
    }
    
    equipment_data = {
        'Equipment': [
            'Scissor Lift - 26ft',
            'Cable Pulling System',
            'Conduit Bender - 1"',
            'Generator - 20KW',
            'Hand Tools Set',
            'Laser Level',
            'Cable Fault Locator',
            'Megger Testing Kit'
        ],
        'Days': [15, 8, 20, 10, 52, 12, 3, 5],
        'Daily_Rate': [185.00, 75.00, 25.00, 125.00, 15.00, 35.00, 95.00, 65.00],
        'Total_Cost': [2775.00, 600.00, 500.00, 1250.00, 780.00, 420.00, 285.00, 325.00]
    }
    
    # Create the Excel file
    file_path = '/Users/ritviksingh/Desktop/Ace148/DDMacAnalysis/temp/Sample_AccuBid_Estimate.xlsx'
    
    # Ensure temp directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Key Indicators sheet (this is what our app will read)
        pd.DataFrame(key_indicators).to_excel(writer, sheet_name='Key Indicators', index=False)
        
        # Additional realistic AccuBid sheets
        pd.DataFrame(materials_data).to_excel(writer, sheet_name='Materials', index=False)
        pd.DataFrame(labor_data).to_excel(writer, sheet_name='Labor', index=False)
        pd.DataFrame(equipment_data).to_excel(writer, sheet_name='Equipment', index=False)
        
        # Summary sheet
        summary_data = {
            'Category': ['Materials', 'Labor', 'Equipment', 'Subcontractors', 'General Expenses'],
            'Cost': [17629.50, 108008.00, 6935.00, 23800.00, 8950.00],
            'Percentage': [10.7, 65.7, 4.2, 14.5, 5.4]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Cost Summary', index=False)
    
    print(f"✅ Created sample AccuBid file: {file_path}")
    print(f"   - File size: {os.path.getsize(file_path) / 1024:.1f} KB")
    print(f"   - Sheets: Key Indicators, Materials, Labor, Equipment, Cost Summary")
    print("🎯 Ready for testing Excel Ingestion page!")
    
    return file_path

if __name__ == "__main__":
    create_sample_accubid_file()