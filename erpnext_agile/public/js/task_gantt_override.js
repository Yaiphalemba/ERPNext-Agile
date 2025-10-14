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

        // Function to apply custom colors
        GanttView.prototype.apply_task_colors = async function() {
            if (!this.gantt?.bars) return;
            
            const today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
            const tasks = this.tasks || [];
            const task_ids = tasks.map(t => t.id);

            // Bulk fetch status only if not already fetched
            if (!this.__task_status_map || Object.keys(this.__task_status_map).length === 0) {
                this.__task_status_map = {};
                
                if (task_ids.length) {
                    await frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "Task",
                            fields: ["name", "status"],
                            filters: [["name", "in", task_ids]],
                            limit_page_length: 999
                        },
                        callback: (res) => {
                            res.message.forEach(task => {
                                this.__task_status_map[task.name] = task.status;
                            });
                        }
                    });
                }
            }

            setTimeout(() => {
                this.gantt.bars.forEach(bar => {
                    const task = bar.task;
                    const end_date = frappe.datetime.str_to_obj(task.end);
                    const status = this.__task_status_map[task.id] || "Open"; // default

                    const overdue = status?.toLowerCase() !== "completed" &&
                        status?.toLowerCase() !== "cancelled" &&
                        end_date < today;

                    let bar_color = "#1890ff"; // main bar blue
                    let progress_color = "#0251bf"; // progress portion

                    if (status?.toLowerCase() === "completed") {
                        bar_color = "#52c41a";
                        progress_color = "#029c07";
                    } else if (status?.toLowerCase() === "cancelled") {
                        bar_color = "#8c8c8c";
                        progress_color = "#666967";
                    } else if (overdue) {
                        bar_color = "#ff4d4f";
                        progress_color = "#a8071a";
                    } else {
                        bar_color = "#f0e513";
                        progress_color = "#c9a606";
                    }
                    
                    // Apply colors
                    bar.$bar.style.fill = bar_color;
                    if (bar.$bar_progress) {
                        bar.$bar_progress.style.fill = progress_color;
                    }
                });
            }, 100);
        };

        // Override refresh to add our color logic
        GanttView.prototype.refresh = async function () {
            this.__task_status_map = {};
            await original_refresh.call(this);
            await this.apply_task_colors();
        };

        // Override render_gantt to hook into view changes
        GanttView.prototype.render_gantt = function() {
            original_render_gantt.call(this);
            
            // Store the original on_view_change function
            const original_on_view_change = this.gantt.options.on_view_change;
            
            // Override on_view_change to apply colors after view change
            this.gantt.options.on_view_change = (mode) => {
                // Call the original handler first
                if (original_on_view_change) {
                    original_on_view_change(mode);
                }
                
                // Apply our custom colors after a small delay
                setTimeout(() => this.apply_task_colors(), 300);
            };
        };

        console.log("GanttView patched with persistent status coloring!");
    };

    frappe.after_ajax(patch_gantt_view);
})();