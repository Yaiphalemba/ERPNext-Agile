frappe.query_reports["Sprint Burndown"] = {
    filters: [
        {
            fieldname: "sprint",
            label: __("Sprint"),
            fieldtype: "Link",
            options: "Agile Sprint",
            reqd: 1
        },
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            reqd: 0
        }
    ],

    onload: function(report) {
        report.page.set_title(__("Sprint Burndown"));
    },

    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "remaining_points") {
            value = `<span style="color:#fc8d59; font-weight:bold;">${value}</span>`;
        } else if (column.fieldname === "ideal_remaining") {
            value = `<span style="color:#91bfdb;">${value}</span>`;
        } else if (column.fieldname === "completed_today") {
            value = `<span style="color:#4daf4a;">${value}</span>`;
        }

        return value;
    },

    get_chart_data: function(columns, result) {
        if (!result || !result.length) return null;

        return {
            data: {
                labels: result.map(d => d.date),
                datasets: [
                    {
                        name: "Remaining Points",
                        values: result.map(d => d.remaining_points),
                        chartType: "line"
                    },
                    {
                        name: "Ideal Burndown",
                        values: result.map(d => d.ideal_remaining),
                        chartType: "line"
                    }
                ]
            },
            type: "line",
            height: 300,
            colors: ["#fc8d59", "#91bfdb"]
        };
    }
};