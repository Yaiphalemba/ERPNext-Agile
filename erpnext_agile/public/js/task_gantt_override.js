(function () {
    const patch_gantt_view = () => {
        if (!frappe.views || !frappe.views.GanttView) {
            return setTimeout(patch_gantt_view, 200);
        }

        const GanttView = frappe.views.GanttView;

        if (GanttView.prototype.__patched) return;
        GanttView.prototype.__patched = true;

        const original_refresh = GanttView.prototype.refresh;
        const original_render_gantt = GanttView.prototype.render_gantt;

        // Make apply_task_colors a true async function
        GanttView.prototype.apply_task_colors = async function() {
            if (!this.gantt || !this.gantt.bars) return;
            
            const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
            const tasks = this.tasks || [];
            const task_ids = tasks.map(t => t.id);

            // Fetch statuses if we haven't already
            if (!this.__task_status_map || Object.keys(this.__task_status_map).length === 0) {
                this.__task_status_map = {};
                
                if (task_ids.length > 0) {
                    // Properly await the API call using Promises
                    await frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Task",
                            fields: ["name", "status"],
                            filters: [["name", "in", task_ids]],
                            limit_page_length: 999
                        }
                    }).then(res => {
                        if (res.message) {
                            res.message.forEach(task => {
                                this.__task_status_map[task.name] = task.status;
                            });
                        }
                    });
                }
            }

            // The data is guaranteed to be here now. Apply the colors.
            // A tiny timeout is still okay here just to let the Frappe/Frappe-Gantt 
            // SVG rendering finish its own internal layout loop before we hijack the styles.
            setTimeout(() => {
                this.gantt.bars.forEach(bar => {
                    const task = bar.task;
                    const end_date = frappe.datetime.str_to_obj(task.end);
                    const status = this.__task_status_map[task.id] || "Open";

                    const overdue = status.toLowerCase() !== "completed" &&
                                    status.toLowerCase() !== "cancelled" &&
                                    end_date < today;

                    let bar_color, progress_color;

                    if (status.toLowerCase() === "completed") {
                        bar_color = "#52c41a";
                        progress_color = "#029c07";
                    } else if (status.toLowerCase() === "cancelled") {
                        bar_color = "#8c8c8c";
                        progress_color = "#666967";
                    } else if (overdue) {
                        bar_color = "#ff4d4f";
                        progress_color = "#a8071a";
                    } else {
                        // Open/Pending
                        bar_color = "#faad14"; // Adjusted the yellow to be a bit softer/modern
                        progress_color = "#d48806";
                    }
                    
                    // Apply styles directly to the SVG elements
                    if (bar.$bar) bar.$bar.style.fill = bar_color;
                    if (bar.$bar_progress) bar.$bar_progress.style.fill = progress_color;
                });
            }, 50); // Reduced to 50ms, just enough for the browser paint cycle
        };

        // Override refresh
        GanttView.prototype.refresh = function () {
            // Reset the map so it fetches fresh data on manual refresh
            this.__task_status_map = {};
            
            // Call original (synchronous)
            original_refresh.call(this);
            
            // Fire and forget our color application
            this.apply_task_colors();
        };

        // Override render_gantt
        GanttView.prototype.render_gantt = function() {
            original_render_gantt.call(this);
            
            const original_on_view_change = this.gantt.options.on_view_change;
            
            this.gantt.options.on_view_change = (mode) => {
                if (original_on_view_change) {
                    original_on_view_change(mode);
                }
                
                // When view changes (Day/Week/Month), Frappe-Gantt destroys and 
                // recreates the SVG bars. We need to reapply the styles.
                // We don't need to fetch data again, just reapply the existing map.
                this.apply_task_colors();
            };
        };
    };

    frappe.after_ajax(patch_gantt_view);
})();