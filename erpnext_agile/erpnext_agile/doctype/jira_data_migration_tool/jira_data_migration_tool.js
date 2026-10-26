frappe.ui.form.on('Jira Data Migration Tool', {
    refresh: function (frm) {
        // Kick off the UI and listeners safely
        setup_dashboard(frm);
        setup_buttons(frm);
        auto_resume_polling(frm);
    }
});

// ─────────────────────────────────────────
// 1. DASHBOARD UI SETUP (Modern & Minimal)
// ─────────────────────────────────────────
function setup_dashboard(frm) {
    const fieldname = "dashboard_html";
    if (!frm.fields_dict[fieldname]) return;

    const wrapper = frm.fields_dict[fieldname].$wrapper;

    // Idempotent render: Only draw it if it doesn't exist
    if (wrapper.find(".modern-jira-dashboard").length === 0) {
        wrapper.html(`
            <div class="modern-jira-dashboard" style="
                background: #111827; color: #f9fafb; padding: 20px; 
                border-radius: 12px; font-family: Inter, sans-serif;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Status</span>
                        <div class="mig-status" style="font-size: 18px; font-weight: 600; color: #9ca3af;">IDLE</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #9ca3af;">Current Phase</span>
                        <div class="mig-phase" style="font-size: 16px; font-weight: 500; color: #60a5fa;">Awaiting Start...</div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div style="background: #1f2937; padding: 12px; border-radius: 8px;">
                        <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">Total Issues</div>
                        <div class="stat-total" style="font-size: 20px; font-weight: bold;">0</div>
                    </div>
                    <div style="background: #1f2937; padding: 12px; border-radius: 8px; border-bottom: 3px solid #10b981;">
                        <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">Tasks Created</div>
                        <div class="stat-processed" style="font-size: 20px; font-weight: bold; color: #10b981;">0</div>
                    </div>
                    <div style="background: #1f2937; padding: 12px; border-radius: 8px; border-bottom: 3px solid #ef4444;">
                        <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">Failed</div>
                        <div class="stat-failed" style="font-size: 20px; font-weight: bold; color: #ef4444;">0</div>
                    </div>
                    <div style="background: #1f2937; padding: 12px; border-radius: 8px;">
                        <div style="font-size: 12px; color: #9ca3af; margin-bottom: 4px;">ETA</div>
                        <div class="stat-eta" style="font-size: 20px; font-weight: bold;">--</div>
                    </div>
                </div>

                <div style="background: #374151; border-radius: 99px; height: 12px; overflow: hidden; position: relative;">
                    <div class="progress-fill" style="
                        height: 100%; width: 0%; 
                        background: linear-gradient(90deg, #3b82f6, #10b981); 
                        transition: width 0.5s ease;
                    "></div>
                </div>
                
                <div class="warning-banner" style="
                    display: none; margin-top: 12px; padding: 10px; 
                    background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; 
                    color: #fbbf24; border-radius: 6px; font-size: 13px;">
                </div>
            </div>
        `);
    }
}

// ─────────────────────────────────────────
// 2. DASHBOARD UPDATER
// ─────────────────────────────────────────
function update_dashboard(frm, d) {
    if (!d) return;
    const w = frm.fields_dict.dashboard_html.$wrapper;
    
    const STATUS_COLORS = {
        running:   "#10b981", // Emerald
        paused:    "#f59e0b", // Amber
        stopped:   "#ef4444", // Red
        failed:    "#ef4444", 
        completed: "#3b82f6", // Blue
        idle:      "#9ca3af", // Gray
    };

    // Update stats
    w.find(".stat-processed").text(d.processed || 0);
    w.find(".stat-total").text(d.total || 0);
    w.find(".stat-failed").text(d.failed || 0);
    
    // Format ETA
    const eta_text = d.eta ? `${Math.floor(d.eta / 60)}m ${Math.floor(d.eta % 60)}s` : "--";
    w.find(".stat-eta").text(eta_text);

    // Visual Progress
    w.find(".progress-fill").css("width", (d.percent || 0) + "%");
    w.find(".mig-status")
        .text((d.status || "idle").toUpperCase())
        .css("color", STATUS_COLORS[d.status] || STATUS_COLORS.idle);

    // Show Current Phase
    w.find(".mig-phase").text(d.phase || (d.status === "running" ? "Processing..." : "---"));

    // Warnings
    const $warn = w.find(".warning-banner");
    if (d.warning) {
        $warn.text("⚠️ " + d.warning).fadeIn(200);
    } else {
        $warn.hide();
    }
}

// ─────────────────────────────────────────
// 3. POLLING ENGINE (Smart & Resilient)
// ─────────────────────────────────────────
function start_polling(frm) {
    if (frm._is_polling) return;
    frm._is_polling = true;
    
    let errorCount = 0;
    const MAX_ERRORS = 3;
    const TERMINAL = ["completed", "stopped", "failed"];

    const poll = () => {
        if (!frm._is_polling) return;

        frappe.call({
            method: "erpnext_agile.jira_sync.get_migration_progress",
            args: { project_key: frm.doc.project_key },
            callback: (r) => {
                errorCount = 0; // Reset on success
                const d = r.message;
                if (!d) {
                    schedule();
                    return;
                }

                update_dashboard(frm, d);

                // Stop if we hit a terminal state and percent is 100%
                if (TERMINAL.includes(d.status)) {
                    stop_polling(frm);
                    
                    // Fire completion alert only once
                    if (d.status === "completed" && !frm._notified_completion) {
                        frappe.show_alert({ message: "✅ Migration fully complete!", indicator: "blue" });
                        frm._notified_completion = true;
                    }
                    return;
                }

                schedule();
            },
            error: () => {
                errorCount++;
                if (errorCount >= MAX_ERRORS) {
                    frappe.show_alert({ message: "Server unreachable — polling stopped.", indicator: "red" });
                    stop_polling(frm);
                    return;
                }
                // Backoff retry
                frm._poll_timer = setTimeout(poll, 5000);
            }
        });
    };

    const schedule = () => {
        frm._poll_timer = setTimeout(poll, 3000); // 3 second polling interval
    };

    poll(); // Kickoff
}

function stop_polling(frm) {
    frm._is_polling = false;
    if (frm._poll_timer) clearTimeout(frm._poll_timer);
}

function auto_resume_polling(frm) {
    if (frm.doc.project_key && !frm._is_polling) {
        frappe.call({
            method: "erpnext_agile.jira_sync.get_migration_progress",
            args: { project_key: frm.doc.project_key },
            callback: (r) => {
                const d = r.message;
                if (d) {
                    update_dashboard(frm, d);
                    if (["running", "paused"].includes(d.status)) {
                        start_polling(frm);
                    }
                }
            }
        });
    }
}

// ─────────────────────────────────────────
// 4. ACTION BUTTONS
// ─────────────────────────────────────────
function setup_buttons(frm) {
    frm.add_custom_button(__('Verify Connection'), () => {
        frappe.call({
            method: "erpnext_agile.jira_sync.verify_connection",
            callback: (r) => {
                if (!r.exc) {
                    frappe.msgprint(r.message);
                    frm.reload_doc();
                }
            }
        });
    });

    frm.add_custom_button(__('Start Migration'), () => {
        if (!frm.doc.project_key) {
            frappe.msgprint("Please enter a Project Key first.");
            return;
        }
        frappe.call({
            method: "erpnext_agile.jira_sync.start_migration",
            args: { project_key: frm.doc.project_key },
            callback: (r) => {
                frappe.show_alert({ message: "Migration Pipeline Started", indicator: "green" });
                frm._notified_completion = false; // Reset notification lock
                start_polling(frm);
            }
        });
    }).addClass("btn-success");

    frm.add_custom_button(__('Pause'), () => {
        frappe.call({
            method: "erpnext_agile.jira_sync.pause_migration",
            args: { project_key: frm.doc.project_key },
            callback: r => frappe.show_alert(r.message)
        });
    }).addClass("btn-warning");

    frm.add_custom_button(__('Resume'), () => {
        frappe.call({
            method: "erpnext_agile.jira_sync.resume_migration",
            args: { project_key: frm.doc.project_key },
            callback: r => {
                frappe.show_alert(r.message);
                start_polling(frm);
            }
        });
    }).addClass("btn-primary");

    frm.add_custom_button(__('Stop'), () => {
        frappe.confirm("Are you sure you want to hard stop the migration?", () => {
            frappe.call({
                method: "erpnext_agile.jira_sync.stop_migration",
                args: { project_key: frm.doc.project_key },
                callback: r => {
                    frappe.show_alert(r.message);
                    stop_polling(frm);
                }
            });
        });
    }).addClass("btn-danger");
}