// Copyright (c) 2026, Yanky and contributors
// For license information, please see license.txt

frappe.query_reports["Sprint Carry Forward Analysis"] = {
    filters: [
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            reqd: 1
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (!data) {
            return value;
        }

        if (column.fieldname === "carry_forward_percentage") {

            let percent = flt(data.carry_forward_percentage);

            let color = "green";

            if (percent >= 25) {
                color = "red";
            } else if (percent >= 10) {
                color = "orange";
            }

            value = `<span style="font-weight:600;color:${color}">
                        ${percent.toFixed(2)}%
                    </span>`;
        }

        if (column.fieldname === "shifted_tasks") {

            if (data.shifted_tasks > 0) {
                value = `<span style="color:#d9534f;font-weight:bold">
                            ${data.shifted_tasks}
                        </span>`;
            }
        }

        if (column.fieldname === "shifted_story_points") {

            if (flt(data.shifted_story_points) > 0) {
                value = `<span style="color:#ff8c00;font-weight:bold">
                            ${data.shifted_story_points}
                        </span>`;
            }
        }

        return value;
    },

    onload: function (report) {

        report.page.add_inner_button(__("Refresh"), function () {
            report.refresh();
        });

    }
};