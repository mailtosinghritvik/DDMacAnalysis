#!/usr/bin/env python3
"""
Deploy Team Comparison SQL Function
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_simple_team_comparison_function():
    """Create a simpler, more reliable team comparison function"""
    
    sql_function = """
-- ==============================================
-- SIMPLE TEAM COMPARISON FUNCTION
-- ==============================================
-- This function calculates user vs team comparison with proper separation

CREATE OR REPLACE FUNCTION get_user_team_comparison(
    user_id_param BIGINT,
    start_date_param DATE DEFAULT NULL,
    end_date_param DATE DEFAULT NULL
)
RETURNS TABLE (
    metric_name TEXT,
    user_value NUMERIC,
    team_average NUMERIC,
    user_rank BIGINT,
    total_users BIGINT,
    percentile NUMERIC
) AS $$
DECLARE
    user_total_hours NUMERIC := 0;
    user_avg_daily_hours NUMERIC := 0;
    user_clients_served BIGINT := 0;
    user_avg_session_length NUMERIC := 0;
    user_longest_session NUMERIC := 0;
    user_work_days BIGINT := 0;
    user_total_sessions BIGINT := 0;
    
    team_avg_total_hours NUMERIC := 0;
    team_avg_daily_hours NUMERIC := 0;
    team_avg_clients_served NUMERIC := 0;
    team_avg_session_length NUMERIC := 0;
    team_avg_longest_session NUMERIC := 0;
    total_team_members BIGINT := 0;
    
    user_total_hours_rank BIGINT := 1;
    user_daily_hours_rank BIGINT := 1;
    user_clients_rank BIGINT := 1;
    user_session_length_rank BIGINT := 1;
    user_longest_session_rank BIGINT := 1;
BEGIN
    -- Get user metrics
    SELECT 
        COALESCE(SUM(t.duration) / 3600.0, 0),
        COUNT(DISTINCT t.date),
        COUNT(DISTINCT j.name),
        COUNT(t.id),
        CASE 
            WHEN COUNT(t.id) > 0 THEN COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END,
        CASE 
            WHEN COUNT(t.id) > 0 THEN MAX(t.duration) / 3600.0
            ELSE 0
        END
    INTO 
        user_total_hours,
        user_work_days,
        user_clients_served,
        user_total_sessions,
        user_avg_session_length,
        user_longest_session
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE u.id = user_id_param;
    
    -- Calculate user average daily hours
    user_avg_daily_hours := CASE 
        WHEN user_work_days > 0 THEN user_total_hours / user_work_days
        ELSE 0
    END;
    
    -- Get team averages (excluding the target user)
    SELECT 
        AVG(COALESCE(SUM(t.duration) / 3600.0, 0)),
        AVG(CASE 
            WHEN COUNT(DISTINCT t.date) > 0 THEN COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
            ELSE 0
        END),
        AVG(COUNT(DISTINCT j.name)),
        AVG(CASE 
            WHEN COUNT(t.id) > 0 THEN COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
            ELSE 0
        END),
        AVG(CASE 
            WHEN COUNT(t.id) > 0 THEN MAX(t.duration) / 3600.0
            ELSE 0
        END),
        COUNT(DISTINCT u.id)
    INTO 
        team_avg_total_hours,
        team_avg_daily_hours,
        team_avg_clients_served,
        team_avg_session_length,
        team_avg_longest_session,
        total_team_members
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id;
    
    -- Calculate user rankings
    SELECT 
        COUNT(*) + 1
    INTO user_total_hours_rank
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id
    HAVING COALESCE(SUM(t.duration) / 3600.0, 0) > user_total_hours;
    
    SELECT 
        COUNT(*) + 1
    INTO user_daily_hours_rank
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id
    HAVING CASE 
        WHEN COUNT(DISTINCT t.date) > 0 THEN COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(DISTINCT t.date)
        ELSE 0
    END > user_avg_daily_hours;
    
    SELECT 
        COUNT(*) + 1
    INTO user_clients_rank
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    LEFT JOIN jobcodes j ON t.jobcode_id = j.id
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id
    HAVING COUNT(DISTINCT j.name) > user_clients_served;
    
    SELECT 
        COUNT(*) + 1
    INTO user_session_length_rank
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id
    HAVING CASE 
        WHEN COUNT(t.id) > 0 THEN COALESCE(SUM(t.duration) / 3600.0, 0) / COUNT(t.id)
        ELSE 0
    END > user_avg_session_length;
    
    SELECT 
        COUNT(*) + 1
    INTO user_longest_session_rank
    FROM users u
    LEFT JOIN timesheets t ON u.id = t.user_id 
        AND (start_date_param IS NULL OR t.date >= start_date_param)
        AND (end_date_param IS NULL OR t.date <= end_date_param)
    WHERE u.active = true AND u.id != user_id_param
    GROUP BY u.id
    HAVING CASE 
        WHEN COUNT(t.id) > 0 THEN MAX(t.duration) / 3600.0
        ELSE 0
    END > user_longest_session;
    
    -- Return the comparison data
    RETURN QUERY
    SELECT 
        'Total Hours'::TEXT,
        user_total_hours,
        COALESCE(team_avg_total_hours, 0),
        user_total_hours_rank,
        total_team_members + 1,
        ROUND(((total_team_members + 1 - user_total_hours_rank + 1)::NUMERIC / (total_team_members + 1)) * 100, 1)
    
    UNION ALL
    
    SELECT 
        'Avg Hours/Day'::TEXT,
        user_avg_daily_hours,
        COALESCE(team_avg_daily_hours, 0),
        user_daily_hours_rank,
        total_team_members + 1,
        ROUND(((total_team_members + 1 - user_daily_hours_rank + 1)::NUMERIC / (total_team_members + 1)) * 100, 1)
    
    UNION ALL
    
    SELECT 
        'Clients Served'::TEXT,
        user_clients_served::NUMERIC,
        COALESCE(team_avg_clients_served, 0),
        user_clients_rank,
        total_team_members + 1,
        ROUND(((total_team_members + 1 - user_clients_rank + 1)::NUMERIC / (total_team_members + 1)) * 100, 1)
    
    UNION ALL
    
    SELECT 
        'Avg Session Length'::TEXT,
        user_avg_session_length,
        COALESCE(team_avg_session_length, 0),
        user_session_length_rank,
        total_team_members + 1,
        ROUND(((total_team_members + 1 - user_session_length_rank + 1)::NUMERIC / (total_team_members + 1)) * 100, 1)
    
    UNION ALL
    
    SELECT 
        'Longest Session'::TEXT,
        user_longest_session,
        COALESCE(team_avg_longest_session, 0),
        user_longest_session_rank,
        total_team_members + 1,
        ROUND(((total_team_members + 1 - user_longest_session_rank + 1)::NUMERIC / (total_team_members + 1)) * 100, 1);
END;
$$ LANGUAGE plpgsql;
"""
    
    return sql_function

def main():
    """Main deployment function"""
    print("🚀 Deploy Team Comparison SQL Function")
    print("=" * 50)
    
    # Create the SQL function
    sql_function = create_simple_team_comparison_function()
    
    # Save to file
    with open("deploy_team_comparison_function.sql", "w", encoding="utf-8") as f:
        f.write(sql_function)
    
    print("✅ SQL function created: deploy_team_comparison_function.sql")
    print()
    print("📋 Next Steps:")
    print("1. Open your Supabase Dashboard")
    print("2. Go to SQL Editor")
    print("3. Copy and paste the contents of deploy_team_comparison_function.sql")
    print("4. Run the SQL to create the function")
    print("5. Test with: python test_team_comparison.py")
    print()
    print("🎯 This will fix the identical values issue in User vs DDMAC Team Comparison!")

if __name__ == "__main__":
    main()
