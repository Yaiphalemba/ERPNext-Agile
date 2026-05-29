frappe.ui.form.on('Jira Data Migration Tool', {
    refresh: function (frm) {

        // ─────────────────────────────────────────
        // DASHBOARD SETUP (idempotent)
        // ─────────────────────────────────────────
        const fieldname = "dashboard_html";
        if (!frm.fields_dict[fieldname]) return;

        const wrapper = frm.fields_dict[fieldname].$wrapper;

        if (wrapper.find(".migration-dashboard").length === 0) {
            wrapper.html(`
                <div class="migration-dashboard">
                    <div class="status-row">
                        Status: <b class="migration-status">IDLE</b>
                        <span class="warning-msg" style="display:none; color:#f59e0b; margin-left:8px;"></span>
                    </div>
                    <div class="stats-row">
                        <span>Processed: <b class="stat-p">0</b></span>
                        <span>Total: <b class="stat-t">0</b></span>
                        <span>Failed: <b class="stat-f">0</b></span>
                        <span>ETA: <b class="stat-eta">--</b></span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-fill"></div>
                    </div>
                </div>
            `);

            wrapper.find(".migration-dashboard").css({
                padding: "16px", borderRadius: "12px",
                background: "#0f172a", color: "#e5e7eb",
                marginBottom: "15px", fontFamily: "monospace"
            });
            wrapper.find(".status-row").css({
                marginBottom: "12px", fontSize: "14px", fontWeight: "bold"
            });
            wrapper.find(".stats-row").css({
                display: "flex", gap: "24px",
                marginBottom: "12px", fontSize: "13px"
            });
            wrapper.find(".progress-track").css({
                background: "#1e293b", borderRadius: "10px",
                height: "14px", overflow: "hidden"
            });
            wrapper.find(".progress-fill").css({
                height: "100%", width: "0%",
                background: "linear-gradient(90deg, #22c55e, #06b6d4)",
                transition: "width 0.4s ease"
            });
        }

        // ─────────────────────────────────────────
        // SHARED DASHBOARD UPDATER
        // ─────────────────────────────────────────
        function updateDashboard(d) {
            if (!d) return;
            const w = wrapper;
            const STATUS_COLORS = {
                running:   "#22c55e",
                paused:    "#f59e0b",
                stopped:   "#ef4444",
                failed:    "#ef4444",
                completed: "#3b82f6",
                idle:      "#e5e7eb",
            };

            w.find(".stat-p").text(d.processed || 0);
            w.find(".stat-t").text(d.total || 0);
            w.find(".stat-f").text(d.failed || 0);
            w.find(".stat-eta").text(formatETA(d.eta));
            w.find(".progress-fill").css("width", (d.percent || 0) + "%");
            w.find(".migration-status")
                .text((d.status || "idle").toUpperCase())
                .css("color", STATUS_COLORS[d.status] || "#e5e7eb");

            const $warn = w.find(".warning-msg");
            if (d.warning) {
                $warn.text("⚠️ " + d.warning).show();
            } else {
                $warn.hide().text("");
            }
        }

        function formatETA(sec) {
            if (!sec) return "--";
            const m = Math.floor(sec / 60);
            const s = Math.floor(sec % 60);
            return `${m}m ${s}s`;
        }

        // ─────────────────────────────────────────
        // POLLING ENGINE
        // ─────────────────────────────────────────
        function startPolling(frm) {
            // Guard: don't spin up duplicate pollers
            if (frm._is_polling) return;
            frm._is_polling = true;
            frm._last_status = frm._last_status || null;
            let errorCount = 0;
            const MAX_ERRORS = 3;
            const TERMINAL = ["completed", "stopped", "failed"];

            function poll() {
                if (!frm._is_polling) return;

                frappe.call({
                    method: "erpnext_agile.jira_sync.get_migration_progress",
                    args: { project_key: frm.doc.project_key },
                    callback: function (r) {
                        errorCount = 0;
                        const d = r.message;
                        if (!d) return schedule();

                        updateDashboard(d);

                        // Fire one-shot alerts on status transitions
                        if (frm._last_status !== d.status) {
                            const ALERTS = {
                                paused:    { msg: "⏸ Paused",                    i: "orange" },
                                stopped:   { msg: "🛑 Stopped",                  i: "red"    },
                                completed: { msg: "✅ Migration complete",        i: "blue"   },
                                failed:    { msg: "❌ Migration failed — check error logs", i: "red" },
                            };
                            if (ALERTS[d.status]) {
                                frappe.show_alert({
                                    message: ALERTS[d.status].msg,
                                    indicator: ALERTS[d.status].i
                                });
                            }
                            frm._last_status = d.status;
                        }

                        if (TERMINAL.includes(d.status)) {
                            stopPolling();
                            return;
                        }

                        schedule();
                    },
                    error: function () {
                        errorCount++;
                        if (errorCount >= MAX_ERRORS) {
                            frappe.show_alert({
                                message: "Server unreachable — polling stopped. Refresh to resume.",
                                indicator: "red"
                            });
                            stopPolling();
                            return;
                        }
                        // Back off a bit on errors
                        frm._poll_timer = setTimeout(poll, 5000);
                    }
                });
            }

            function schedule() {
                frm._poll_timer = setTimeout(poll, 3000);
            }

            function stopPolling() {
                frm._is_polling = false;
                if (frm._poll_timer) clearTimeout(frm._poll_timer);
            }

            // Kick off immediately
            if (frm._poll_timer) clearTimeout(frm._poll_timer);
            poll();
        }

        // ─────────────────────────────────────────
        // AUTO-RESUME: detect in-flight migration on page load / refresh
        // ─────────────────────────────────────────
        if (frm.doc.project_key && !frm._is_polling) {
            frappe.call({
                method: "erpnext_agile.jira_sync.get_migration_progress",
                args: { project_key: frm.doc.project_key },
                callback: function (r) {
                    const d = r.message;
                    if (!d) return;
                    // Paint current state even if not polling
                    updateDashboard(d);
                    // Resume live polling if migration is still active
                    if (["running", "paused"].includes(d.status)) {
                        startPolling(frm);
                    }
                }
            });
        }

        // ─────────────────────────────────────────
        // ACTION BUTTONS
        // ─────────────────────────────────────────
        frm.add_custom_button(__('Verify Connection'), function () {
            frappe.call({
                method: "erpnext_agile.jira_sync.verify_connection",
                callback: function (r) {
                    if (!r.exc) {
                        frappe.msgprint(r.message);
                        frm.reload_doc();
                    }
                }
            });
        });

        frm.add_custom_button(__('Start Migration'), function () {
            if (!frm.doc.project_key) {
                frappe.msgprint("Please enter a Project Key first.");
                return;
            }
            frappe.call({
                method: "erpnext_agile.jira_sync.start_migration",
                args: { project_key: frm.doc.project_key },
                callback: function (r) {
                    frappe.show_alert({ message: r.message || "Migration started", indicator: "green" });
                    // Reset stale status so transition alerts fire correctly
                    frm._last_status = null;
                    frm._is_polling  = false;
                    startPolling(frm);
                }
            });
        }).addClass("btn-success");

        frm.add_custom_button(__('Pause'), function () {
            frappe.call({
                method: "erpnext_agile.jira_sync.pause_migration",
                args: { project_key: frm.doc.project_key },
                callback: r => frappe.show_alert(r.message)
            });
        }).addClass("btn-warning");

        frm.add_custom_button(__('Resume'), function () {
            frappe.call({
                method: "erpnext_agile.jira_sync.resume_migration",
                args: { project_key: frm.doc.project_key },
                callback: r => {
                    frappe.show_alert(r.message);
                    // Ensure polling is active after resume
                    if (!frm._is_polling) startPolling(frm);
                }
            });
        }).addClass("btn-primary");

        frm.add_custom_button(__('Stop'), function () {
            frappe.confirm("Are you sure you want to stop the migration?", () => {
                frappe.call({
                    method: "erpnext_agile.jira_sync.stop_migration",
                    args: { project_key: frm.doc.project_key },
                    callback: r => frappe.show_alert(r.message)
                });
            });
        }).addClass("btn-danger");

        frm.add_custom_button(__('Retry Failed'), function () {
            frappe.call({
                method: "erpnext_agile.jira_sync.retry_failed_issues",
                args: { project_key: frm.doc.project_key },
                callback: r => frappe.msgprint(r.message)
            });
        });

        frm.add_custom_button(__('Stop Polling'), function () {
            if (frm._is_polling) {
                frm._is_polling = false;
                if (frm._poll_timer) clearTimeout(frm._poll_timer);
                frappe.show_alert("Polling stopped");
            }
        }).addClass("btn-secondary");
    }
});