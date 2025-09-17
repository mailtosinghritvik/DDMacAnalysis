"""
Data processing utilities for DDMac Analysis Tool
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import os
import tempfile

def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate and analyze a pandas DataFrame
    
    Args:
        df: pandas DataFrame to validate
        
    Returns:
        Dictionary with validation results and basic statistics
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum(),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum()
    }
    
    # Check for empty DataFrame
    if df.empty:
        validation_results['errors'].append("DataFrame is empty")
        validation_results['is_valid'] = False
    
    # Check for excessive missing values
    missing_percentage = (df.isnull().sum() / len(df)) * 100
    high_missing_cols = missing_percentage[missing_percentage > 50].index.tolist()
    if high_missing_cols:
        validation_results['warnings'].append(f"Columns with >50% missing values: {high_missing_cols}")
    
    # Check for duplicate columns
    if len(df.columns) != len(set(df.columns)):
        validation_results['errors'].append("Duplicate column names found")
        validation_results['is_valid'] = False
    
    return validation_results

def clean_dataframe(df: pd.DataFrame, options: Dict[str, Any] = None) -> pd.DataFrame:
    """
    Clean a pandas DataFrame based on provided options
    
    Args:
        df: pandas DataFrame to clean
        options: Dictionary with cleaning options
        
    Returns:
        Cleaned pandas DataFrame
    """
    if options is None:
        options = {}
    
    df_cleaned = df.copy()
    
    # Remove duplicates
    if options.get('remove_duplicates', True):
        df_cleaned = df_cleaned.drop_duplicates()
    
    # Handle missing values
    missing_strategy = options.get('missing_strategy', 'keep')
    if missing_strategy == 'drop_rows':
        df_cleaned = df_cleaned.dropna()
    elif missing_strategy == 'drop_cols':
        df_cleaned = df_cleaned.dropna(axis=1)
    elif missing_strategy == 'fill_mean':
        numeric_columns = df_cleaned.select_dtypes(include=[np.number]).columns
        df_cleaned[numeric_columns] = df_cleaned[numeric_columns].fillna(df_cleaned[numeric_columns].mean())
    elif missing_strategy == 'fill_median':
        numeric_columns = df_cleaned.select_dtypes(include=[np.number]).columns
        df_cleaned[numeric_columns] = df_cleaned[numeric_columns].fillna(df_cleaned[numeric_columns].median())
    
    # Clean column names
    if options.get('clean_column_names', True):
        df_cleaned.columns = df_cleaned.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Convert data types
    if 'column_types' in options:
        for col, dtype in options['column_types'].items():
            if col in df_cleaned.columns:
                try:
                    df_cleaned[col] = df_cleaned[col].astype(dtype)
                except (ValueError, TypeError):
                    pass  # Skip if conversion fails
    
    return df_cleaned

def get_column_suggestions(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Suggest data types and cleaning operations for DataFrame columns
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        Dictionary with suggestions for each column
    """
    suggestions = {}
    
    for col in df.columns:
        col_suggestions = []
        series = df[col]
        
        # Check for date columns
        if series.dtype == 'object':
            # Try to parse as datetime
            try:
                pd.to_datetime(series.dropna().head(100), infer_datetime_format=True)
                col_suggestions.append("Consider converting to datetime")
            except (ValueError, TypeError):
                pass
        
        # Check for categorical columns
        if series.dtype == 'object' and series.nunique() / len(series) < 0.1:
            col_suggestions.append("Consider converting to category")
        
        # Check for numeric columns stored as text
        if series.dtype == 'object':
            try:
                pd.to_numeric(series.dropna().head(100))
                col_suggestions.append("Consider converting to numeric")
            except (ValueError, TypeError):
                pass
        
        # Check for high cardinality
        if series.nunique() > len(series) * 0.9:
            col_suggestions.append("High cardinality - might be an identifier")
        
        # Check for missing values
        missing_pct = series.isnull().sum() / len(series) * 100
        if missing_pct > 10:
            col_suggestions.append(f"{missing_pct:.1f}% missing values")
        
        suggestions[col] = col_suggestions
    
    return suggestions

def export_dataframe(df: pd.DataFrame, format: str, filename: str = None) -> str:
    """
    Export DataFrame to various formats
    
    Args:
        df: pandas DataFrame to export
        format: Export format ('csv', 'excel', 'json', 'parquet')
        filename: Optional filename, if None a temporary file is created
        
    Returns:
        Path to the exported file
    """
    if filename is None:
        suffix = f'.{format}' if format != 'excel' else '.xlsx'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        filepath = temp_file.name
        temp_file.close()
    else:
        filepath = filename
    
    if format.lower() == 'csv':
        df.to_csv(filepath, index=False)
    elif format.lower() == 'excel':
        df.to_excel(filepath, index=False)
    elif format.lower() == 'json':
        df.to_json(filepath, orient='records', indent=2)
    elif format.lower() == 'parquet':
        df.to_parquet(filepath, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return filepath

def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for a DataFrame
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        Dictionary with various statistics
    """
    stats = {
        'basic_info': {
            'shape': df.shape,
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'dtypes_count': df.dtypes.value_counts().to_dict()
        },
        'missing_data': {
            'total_missing': df.isnull().sum().sum(),
            'missing_by_column': df.isnull().sum().to_dict(),
            'missing_percentage': (df.isnull().sum() / len(df) * 100).to_dict()
        },
        'numeric_stats': {},
        'categorical_stats': {}
    }
    
    # Numeric columns statistics
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 0:
        stats['numeric_stats'] = df[numeric_columns].describe().to_dict()
    
    # Categorical columns statistics
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    for col in categorical_columns:
        stats['categorical_stats'][col] = {
            'unique_count': df[col].nunique(),
            'top_values': df[col].value_counts().head(5).to_dict()
        }
    
    return stats
