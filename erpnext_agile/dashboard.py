# Updated dashboard.py
def get_agile_project_dashboard():
    """Custom dashboard for agile projects"""
    return {
        "charts": [
            {
                "chart_name": "Sprint Burndown",
                "chart_type": "line",
                "custom_options": {
                    "type": "line",
                    "axisOptions": {
                        "xAxisMode": "tick",
                        "xIsSeries": 1
                    }
                },
                "source": "Task"
            },
            {
                "chart_name": "Task Distribution",
                "chart_type": "donut", 
                "document_type": "Task",
                "group_by_type": "Count",
                "group_by_based_on": "issue_type"
            }
        ],
        "number_cards": [
            {
                "label": "Open Tasks",
                "function": "count",
                "document_type": "Task",
                "filters_json": '{"status": ["not in", ["Resolved", "Closed"]], "project.enable_agile": 1}'
            },
            {
                "label": "Current Sprint",
                "function": "count", 
                "document_type": "Task",
                "filters_json": '{"current_sprint": ["!=", ""], "project.enable_agile": 1}'
            }
        ]
    }

def get_dashboard_data(data):
    def get_indicator(doc):
        if getattr(doc, "agile_status", None):
            return (doc.agile_status, "blue", "agile_status,=," + doc.agile_status)
        return data.get("status", lambda doc: (doc.status, "grey", "status,=," + doc.status))(doc)

    data["status"] = get_indicator
    return data