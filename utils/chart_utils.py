"""
Chart utilities for DDMac Analysis Tool
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

def create_histogram(df: pd.DataFrame, column: str, bins: int = 30, title: str = None) -> go.Figure:
    """
    Create a histogram for a numeric column
    
    Args:
        df: pandas DataFrame
        column: Column name to plot
        bins: Number of bins
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = f"Distribution of {column}"
    
    fig = px.histogram(
        df, 
        x=column, 
        nbins=bins,
        title=title,
        labels={'count': 'Frequency', column: column}
    )
    
    fig.update_layout(
        xaxis_title=column,
        yaxis_title="Frequency",
        showlegend=False
    )
    
    return fig

def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, 
                       color_col: str = None, title: str = None) -> go.Figure:
    """
    Create a scatter plot
    
    Args:
        df: pandas DataFrame
        x_col: X-axis column name
        y_col: Y-axis column name
        color_col: Optional column for color coding
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = f"{x_col} vs {y_col}"
    
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        opacity=0.7
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    
    return fig

def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                     title: str = None) -> go.Figure:
    """
    Create a line chart
    
    Args:
        df: pandas DataFrame
        x_col: X-axis column name
        y_col: Y-axis column name
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = f"{y_col} over {x_col}"
    
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title
    )
    
    fig.update_layout(
        xaxis_title=x_col,
        yaxis_title=y_col
    )
    
    return fig

def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str = None,
                    title: str = None, orientation: str = 'v') -> go.Figure:
    """
    Create a bar chart
    
    Args:
        df: pandas DataFrame
        x_col: X-axis column name (or categories)
        y_col: Y-axis column name (if None, will count occurrences)
        title: Optional title for the chart
        orientation: 'v' for vertical, 'h' for horizontal
        
    Returns:
        Plotly figure object
    """
    if y_col is None:
        # Count occurrences
        data = df[x_col].value_counts().reset_index()
        data.columns = [x_col, 'count']
        y_col = 'count'
        df_plot = data
    else:
        df_plot = df
    
    if title is None:
        title = f"{y_col} by {x_col}"
    
    if orientation == 'v':
        fig = px.bar(df_plot, x=x_col, y=y_col, title=title)
    else:
        fig = px.bar(df_plot, x=y_col, y=x_col, title=title, orientation='h')
    
    return fig

def create_box_plot(df: pd.DataFrame, x_col: str = None, y_col: str = None,
                   title: str = None) -> go.Figure:
    """
    Create a box plot
    
    Args:
        df: pandas DataFrame
        x_col: Optional grouping column
        y_col: Numeric column for box plot
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        if x_col:
            title = f"Distribution of {y_col} by {x_col}"
        else:
            title = f"Distribution of {y_col}"
    
    fig = px.box(df, x=x_col, y=y_col, title=title)
    
    return fig

def create_correlation_heatmap(df: pd.DataFrame, title: str = None) -> go.Figure:
    """
    Create a correlation heatmap for numeric columns
    
    Args:
        df: pandas DataFrame
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = "Correlation Heatmap"
    
    # Get only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        # Return empty figure if no numeric columns
        fig = go.Figure()
        fig.add_annotation(
            text="No numeric columns available for correlation analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    corr_matrix = numeric_df.corr()
    
    fig = px.imshow(
        corr_matrix,
        title=title,
        color_continuous_scale='RdBu',
        aspect='auto'
    )
    
    fig.update_layout(
        width=600,
        height=600
    )
    
    return fig

def create_pie_chart(df: pd.DataFrame, column: str, title: str = None,
                    max_categories: int = 10) -> go.Figure:
    """
    Create a pie chart
    
    Args:
        df: pandas DataFrame
        column: Column name for categories
        title: Optional title for the chart
        max_categories: Maximum number of categories to show
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = f"Distribution of {column}"
    
    # Get value counts
    value_counts = df[column].value_counts()
    
    # Limit to max_categories
    if len(value_counts) > max_categories:
        top_categories = value_counts.head(max_categories - 1)
        other_count = value_counts.iloc[max_categories - 1:].sum()
        value_counts = pd.concat([top_categories, pd.Series({'Others': other_count})])
    
    fig = px.pie(
        values=value_counts.values,
        names=value_counts.index,
        title=title
    )
    
    return fig

def create_time_series(df: pd.DataFrame, date_col: str, value_col: str,
                      title: str = None) -> go.Figure:
    """
    Create a time series plot
    
    Args:
        df: pandas DataFrame
        date_col: Date column name
        value_col: Value column name
        title: Optional title for the chart
        
    Returns:
        Plotly figure object
    """
    if title is None:
        title = f"{value_col} over time"
    
    # Ensure date column is datetime
    df_plot = df.copy()
    df_plot[date_col] = pd.to_datetime(df_plot[date_col])
    
    fig = px.line(
        df_plot,
        x=date_col,
        y=value_col,
        title=title
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=value_col
    )
    
    return fig

def suggest_charts(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Suggest appropriate chart types based on data types
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Dictionary with suggested charts and required columns
    """
    suggestions = {}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = []
    
    # Try to identify datetime columns
    for col in categorical_cols:
        try:
            pd.to_datetime(df[col].dropna().head(10))
            datetime_cols.append(col)
        except:
            pass
    
    # Single column charts
    if numeric_cols:
        suggestions['Histogram'] = [f"Distribution of {col}" for col in numeric_cols]
        suggestions['Box Plot'] = [f"Distribution of {col}" for col in numeric_cols]
    
    if categorical_cols:
        suggestions['Bar Chart'] = [f"Count of {col}" for col in categorical_cols]
        suggestions['Pie Chart'] = [f"Distribution of {col}" for col in categorical_cols]
    
    # Two column charts
    if len(numeric_cols) >= 2:
        suggestions['Scatter Plot'] = [f"{x} vs {y}" for x in numeric_cols for y in numeric_cols if x != y]
        suggestions['Correlation Heatmap'] = ["All numeric columns correlation"]
    
    # Time series
    if datetime_cols and numeric_cols:
        suggestions['Time Series'] = [f"{val} over {date}" for date in datetime_cols for val in numeric_cols]
    
    # Mixed type charts
    if categorical_cols and numeric_cols:
        suggestions['Grouped Bar Chart'] = [f"{num} by {cat}" for cat in categorical_cols for num in numeric_cols]
        suggestions['Box Plot by Category'] = [f"{num} distribution by {cat}" for cat in categorical_cols for num in numeric_cols]
    
    return suggestions
