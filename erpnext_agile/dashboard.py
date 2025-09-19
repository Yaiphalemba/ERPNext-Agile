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
                "source": "Agile Issue"
            },
            {
                "chart_name": "Issue Distribution",
                "chart_type": "donut", 
                "document_type": "Agile Issue",
                "group_by_type": "Count",
                "group_by_based_on": "issue_type"
            }
        ],
        "number_cards": [
            {
                "label": "Open Issues",
                "function": "count",
                "document_type": "Agile Issue",
                "filters_json": '{"status": ["not in", ["Resolved", "Closed"]]}'
            },
            {
                "label": "Current Sprint",
                "function": "count", 
                "document_type": "Agile Issue",
                "filters_json": '{"current_sprint": ["!=", ""]}'
            }
        ]
    }