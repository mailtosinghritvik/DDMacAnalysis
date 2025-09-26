#!/usr/bin/env python3
"""
Enhanced Individual Employee Insights
Uses performance overview data to provide comprehensive individual insights
Fixes all errors and provides robust data handling
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import time

class EnhancedIndividualInsights:
    """Enhanced Individual Employee Insights using performance overview data"""
    
    def __init__(self, supabase_handler):
        self.handler = supabase_handler
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_duration = 300  # 5 minutes cache
    
    def _get_from_cache(self, key: str):
        """Get data from cache if not expired"""
        if key in self._cache and time.time() - self._cache_timestamp[key] < self._cache_duration:
            return self._cache[key]
        return None
    
    def _set_cache(self, key: str, data):
        """Set data in cache with timestamp"""
        self._cache[key] = data
        self._cache_timestamp[key] = time.time()
    
    def get_employee_performance_overview(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get comprehensive performance overview for an employee"""
        cache_key = f"performance_overview_{user_id}_{start_date}_{end_date}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Get comprehensive employee data
            response = self.handler.supabase.rpc(
                'get_individual_employee_summary',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if not response.data:
                return self._create_empty_performance_data()
            
            emp_data = response.data[0]
            
            # Get additional performance metrics
            productivity_data = self.get_employee_productivity_metrics(user_id, start_date, end_date)
            client_distribution = self.get_employee_client_distribution(user_id, start_date, end_date)
            task_distribution = self.get_employee_task_distribution(user_id, start_date, end_date)
            daily_work = self.get_employee_daily_work_summary(user_id, start_date, end_date)
            weekly_work = self.get_employee_weekly_work_summary(user_id, start_date, end_date)
            
            # Safely convert all numeric values to native Python types
            def safe_convert(value, default=0, convert_type=float):
                try:
                    if value is None:
                        return default
                    return convert_type(value)
                except (ValueError, TypeError):
                    return default
            
            performance_data = {
                'basic_info': {
                    'employee_id': safe_convert(emp_data.get('employee_id'), 0, int),
                    'employee_name': str(emp_data.get('employee_name', 'Unknown')),
                    'full_name': str(emp_data.get('full_name', 'Unknown')),
                    'work_start_date': emp_data.get('work_start_date'),
                    'work_end_date': emp_data.get('work_end_date')
                },
                'work_metrics': {
                    'total_work_hours': safe_convert(emp_data.get('total_work_hours'), 0.0, float),
                    'actual_work_days': safe_convert(emp_data.get('actual_work_days'), 0, int),
                    'average_daily_hours': safe_convert(emp_data.get('average_daily_hours'), 0.0, float),
                    'total_entries': safe_convert(emp_data.get('total_entries'), 0, int),
                    'billable_hours': safe_convert(emp_data.get('billable_hours'), 0.0, float),
                    'overtime_hours': safe_convert(emp_data.get('overtime_hours'), 0.0, float)
                },
                'performance_metrics': {
                    'utilization_percentage': safe_convert(emp_data.get('utilization_percentage'), 0.0, float),
                    'productivity_score': safe_convert(emp_data.get('productivity_score'), 0.0, float),
                    'performance_rating': str(emp_data.get('performance_rating', 'Unknown'))
                },
                'project_data': {
                    'client_list': list(emp_data.get('client_list', [])),
                    'task_list': list(emp_data.get('task_list', []))
                },
                'distributions': {
                    'client_distribution': client_distribution,
                    'task_distribution': task_distribution
                },
                'time_series': {
                    'daily_work': daily_work,
                    'weekly_work': weekly_work
                },
                'productivity_details': productivity_data
            }
            
            self._set_cache(cache_key, performance_data)
            return performance_data
            
        except Exception as e:
            st.error(f"Error getting performance overview: {str(e)}")
            return self._create_empty_performance_data()
    
    def _create_empty_performance_data(self):
        """Create empty performance data structure"""
        return {
            'basic_info': {
                'employee_id': None,
                'employee_name': 'Unknown',
                'full_name': 'Unknown',
                'work_start_date': None,
                'work_end_date': None
            },
            'work_metrics': {
                'total_work_hours': 0.0,
                'actual_work_days': 0,
                'average_daily_hours': 0.0,
                'total_entries': 0,
                'billable_hours': 0.0,
                'overtime_hours': 0.0
            },
            'performance_metrics': {
                'utilization_percentage': 0.0,
                'productivity_score': 0.0,
                'performance_rating': 'No Data'
            },
            'project_data': {
                'client_list': [],
                'task_list': []
            },
            'distributions': {
                'client_distribution': pd.DataFrame(),
                'task_distribution': pd.DataFrame()
            },
            'time_series': {
                'daily_work': pd.DataFrame(),
                'weekly_work': pd.DataFrame()
            },
            'productivity_details': pd.DataFrame()
        }
    
    def get_employee_productivity_metrics(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get productivity metrics for an employee"""
        try:
            response = self.handler.supabase.rpc(
                'get_individual_productivity_metrics',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting productivity metrics: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_client_distribution(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get client distribution for an employee"""
        try:
            response = self.handler.supabase.rpc(
                'get_individual_client_distribution',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting client distribution: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_task_distribution(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get task distribution for an employee"""
        try:
            response = self.handler.supabase.rpc(
                'get_individual_task_distribution',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting task distribution: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_daily_work_summary(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get daily work summary for an employee"""
        try:
            response = self.handler.supabase.rpc(
                'get_individual_daily_work_summary',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting daily work summary: {str(e)}")
            return pd.DataFrame()
    
    def get_employee_weekly_work_summary(self, user_id: int, start_date: str = None, end_date: str = None):
        """Get weekly work summary for an employee"""
        try:
            response = self.handler.supabase.rpc(
                'get_individual_weekly_work_summary',
                {
                    'user_id_param': user_id,
                    'start_date_param': start_date,
                    'end_date_param': end_date
                }
            ).execute()
            
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting weekly work summary: {str(e)}")
            return pd.DataFrame()
    
    def create_enhanced_productivity_gauge(self, performance_data):
        """Create enhanced productivity gauge using performance data"""
        metrics = performance_data['performance_metrics']
        basic_info = performance_data['basic_info']
        
        productivity_score = metrics['productivity_score']
        utilization = metrics['utilization_percentage']
        performance_rating = metrics['performance_rating']
        
        # Create gauge with multiple metrics
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = productivity_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"Productivity Score - {basic_info['employee_name']}"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=400,
            font={'color': "darkblue", 'family': "Arial Black"},
            title_font_size=20
        )
        
        return fig
    
    def create_performance_metrics_display(self, performance_data):
        """Create comprehensive performance metrics display"""
        work_metrics = performance_data['work_metrics']
        performance_metrics = performance_data['performance_metrics']
        basic_info = performance_data['basic_info']
        
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Hours", 
                f"{work_metrics['total_work_hours']:.1f}h",
                delta=f"{work_metrics['overtime_hours']:.1f}h overtime" if work_metrics['overtime_hours'] > 0 else None
            )
        
        with col2:
            st.metric(
                "Daily Average", 
                f"{work_metrics['average_daily_hours']:.1f}h",
                delta=f"{work_metrics['actual_work_days']} days worked"
            )
        
        with col3:
            st.metric(
                "Utilization", 
                f"{performance_metrics['utilization_percentage']:.1f}%",
                delta=performance_metrics['performance_rating']
            )
        
        with col4:
            st.metric(
                "Productivity Score", 
                f"{performance_metrics['productivity_score']:.1f}",
                delta=f"{work_metrics['total_entries']} entries"
            )
    
    def create_project_breakdown_display(self, performance_data):
        """Create enhanced project breakdown display"""
        project_data = performance_data['project_data']
        distributions = performance_data['distributions']
        
        # Client distribution
        if not distributions['client_distribution'].empty:
            st.subheader("🏢 Client Distribution")
            client_df = distributions['client_distribution'].head(10)
            
            # Create client distribution chart
            fig_client = px.pie(
                client_df, 
                values='total_hours', 
                names='client_name',
                title="Hours by Client"
            )
            fig_client.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_client, use_container_width=True)
            
            # Client data table
            st.dataframe(client_df, use_container_width=True)
        
        # Task distribution
        if not distributions['task_distribution'].empty:
            st.subheader("📋 Task Distribution")
            task_df = distributions['task_distribution'].head(10)
            
            # Create task distribution chart
            fig_task = px.bar(
                task_df, 
                x='task_name', 
                y='total_hours',
                title="Hours by Task",
                color='total_hours',
                color_continuous_scale='Blues'
            )
            fig_task.update_xaxes(tickangle=45)
            st.plotly_chart(fig_task, use_container_width=True)
            
            # Task data table
            st.dataframe(task_df, use_container_width=True)
    
    def create_time_series_charts(self, performance_data):
        """Create time series charts for daily and weekly work"""
        time_series = performance_data['time_series']
        
        # Daily work chart
        if not time_series['daily_work'].empty:
            st.subheader("📅 Daily Work Pattern")
            daily_df = time_series['daily_work']
            
            fig_daily = px.line(
                daily_df, 
                x='work_date', 
                y='total_hours',
                title="Daily Hours Worked",
                color_discrete_sequence=['#1f77b4']
            )
            fig_daily.update_layout(
                xaxis_title="Date",
                yaxis_title="Hours Worked"
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        
        # Weekly work chart
        if not time_series['weekly_work'].empty:
            st.subheader("📊 Weekly Work Summary")
            weekly_df = time_series['weekly_work']
            
            fig_weekly = px.bar(
                weekly_df, 
                x='work_week', 
                y='total_hours',
                title="Weekly Hours Worked",
                color='total_hours',
                color_continuous_scale='Viridis'
            )
            fig_weekly.update_xaxes(tickangle=45)
            st.plotly_chart(fig_weekly, use_container_width=True)
    
    def display_enhanced_individual_insights(self, user_id: int, employee_name: str, start_date: str = None, end_date: str = None):
        """Display enhanced individual insights using performance overview data"""
        
        # Show loading indicator
        with st.spinner(f"Loading enhanced insights for {employee_name}..."):
            performance_data = self.get_employee_performance_overview(user_id, start_date, end_date)
        
        if not performance_data['basic_info']['employee_id']:
            st.error(f"No data found for {employee_name}")
            return
        
        # Header
        st.subheader(f"🎯 Enhanced Individual Insights - {employee_data['basic_info']['full_name']}")
        
        # Performance metrics display
        self.create_performance_metrics_display(performance_data)
        
        # Productivity gauge
        st.subheader("📊 Productivity Overview")
        gauge_fig = self.create_enhanced_productivity_gauge(performance_data)
        st.plotly_chart(gauge_fig, use_container_width=True)
        
        # Project breakdown
        self.create_project_breakdown_display(performance_data)
        
        # Time series charts
        self.create_time_series_charts(performance_data)
        
        # Summary statistics
        st.subheader("📈 Summary Statistics")
        work_metrics = performance_data['work_metrics']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Billable Hours", f"{work_metrics['billable_hours']:.1f}h")
        with col2:
            st.metric("Overtime Hours", f"{work_metrics['overtime_hours']:.1f}h")
        with col3:
            st.metric("Unique Clients", len(performance_data['project_data']['client_list']))
        with col4:
            st.metric("Unique Tasks", len(performance_data['project_data']['task_list']))

def create_enhanced_individual_insights_section(handler, user_id: int, employee_name: str, start_date: str = None, end_date: str = None):
    """Create enhanced individual insights section"""
    
    # Initialize enhanced insights
    enhanced_insights = EnhancedIndividualInsights(handler)
    
    # Display enhanced insights
    enhanced_insights.display_enhanced_individual_insights(user_id, employee_name, start_date, end_date)
