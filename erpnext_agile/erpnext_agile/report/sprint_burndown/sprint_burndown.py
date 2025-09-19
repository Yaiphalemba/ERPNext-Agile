import frappe
from frappe.utils import flt, date_diff, getdate

def execute(filters=None):
    """Generate sprint burndown chart data"""
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 100},
        {"fieldname": "remaining_points", "label": "Remaining Points", "fieldtype": "Float", "width": 150},
        {"fieldname": "ideal_remaining", "label": "Ideal Remaining", "fieldtype": "Float", "width": 150},
        {"fieldname": "completed_today", "label": "Completed Today", "fieldtype": "Float", "width": 150}
    ]

def get_data(filters):
    """Get burndown data for sprint"""
    sprint = frappe.get_doc("Agile Sprint", filters.get("sprint"))
    
    # Get total story points in sprint
    total_points = frappe.db.sql("""
        SELECT SUM(story_points) FROM `tabAgile Issue`
        WHERE current_sprint = %s
    """, sprint.name)[0][0] or 0
    
    # Calculate daily burndown
    current_date = getdate(sprint.start_date)
    end_date = getdate(sprint.end_date)
    sprint_days = date_diff(end_date, current_date) + 1
    daily_ideal = total_points / sprint_days
    
    data = []
    remaining_points = total_points
    
    while current_date <= end_date:
        # Get points completed on this date
        completed_today = frappe.db.sql("""
            SELECT SUM(story_points) FROM `tabAgile Issue`
            WHERE current_sprint = %s 
            AND status IN ('Resolved', 'Closed')
            AND DATE(modified) = %s
        """, (sprint.name, current_date))[0][0] or 0
        
        remaining_points -= completed_today
        ideal_remaining = max(0, total_points - (daily_ideal * (date_diff(current_date, getdate(sprint.start_date)) + 1)))
        
        data.append({
            "date": current_date,
            "remaining_points": remaining_points,
            "ideal_remaining": ideal_remaining,
            "completed_today": completed_today
        })
        
        current_date = frappe.utils.add_days(current_date, 1)
    
    return data

def get_chart_data(data, filters):
    """Generate chart configuration"""
    return {
        "data": {
            "labels": [d["date"] for d in data],
            "datasets": [
                {
                    "name": "Remaining Points",
                    "values": [d["remaining_points"] for d in data],
                    "chartType": "line"
                },
                {
                    "name": "Ideal Burndown", 
                    "values": [d["ideal_remaining"] for d in data],
                    "chartType": "line"
                }
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#fc8d59", "#91bfdb"]
    }