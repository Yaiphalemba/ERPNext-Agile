// Copyright (c) 2025, Yanky and contributors
// For license information, please see license.txt

frappe.ui.form.on('Agile Workflow Scheme', {
    refresh(frm) {
        if (!frm.is_new()) {
            // Add button to test workflow
            frm.add_custom_button(__('Test Workflow'), () => {
                show_workflow_tester(frm);
            });
            
            // Add button to visualize workflow
            frm.add_custom_button(__('Visualize Workflow'), () => {
                show_workflow_diagram(frm);
            });
        }
    }
});

frappe.ui.form.on('Agile Workflow Transition', {
    condition(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        // Show helper dialog for condition
        if (row.condition) {
            frappe.msgprint({
                title: __('Condition Syntax'),
                indicator: 'blue',
                message: `
                    <p><b>Available Variables:</b></p>
                    <ul>
                        <li><code>doc</code> - The task document</li>
                        <li><code>doc.issue_type</code> - Issue type (e.g., "Epic", "Story")</li>
                        <li><code>doc.issue_priority</code> - Priority</li>
                        <li><code>doc.story_points</code> - Story points</li>
                        <li><code>doc.assigned_to_users</code> - List of assignees</li>
                        <li><code>doc.project</code> - Project name</li>
                        <li><code>len()</code> - Get length of list</li>
                        <li><code>today()</code> - Today's date</li>
                    </ul>
                    <p><b>Example Conditions:</b></p>
                    <ul>
                        <li><code>doc.issue_type == "Epic"</code></li>
                        <li><code>doc.story_points and doc.story_points >= 5</code></li>
                        <li><code>len(doc.assigned_to_users) > 0</code></li>
                        <li><code>doc.issue_priority == "Critical"</code></li>
                        <li><code>doc.project == "My Project"</code></li>
                    </ul>
                `
            });
        }
    },
    
    transitions_add(frm, cdt, cdn) {
        // Auto-fill transition name based on statuses
        let row = locals[cdt][cdn];
        
        setTimeout(() => {
            if (row.from_status && row.to_status && !row.transition_name) {
                let from = row.from_status.replace('Agile Issue Status-', '');
                let to = row.to_status.replace('Agile Issue Status-', '');
                frappe.model.set_value(cdt, cdn, 'transition_name', `${from} → ${to}`);
            }
        }, 500);
    }
});

function show_workflow_tester(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Test Workflow'),
        fields: [
            {
                fieldtype: 'Link',
                label: __('Select Task'),
                fieldname: 'task',
                options: 'Task',
                reqd: 1,
                get_query: () => {
                    return {
                        filters: {
                            'is_agile': 1
                        }
                    };
                }
            },
            {
                fieldtype: 'HTML',
                fieldname: 'results'
            }
        ],
        primary_action_label: __('Test Transitions'),
        primary_action(values) {
            if (!values.task) {
                frappe.msgprint(__('Please select a task'));
                return;
            }
            
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Task',
                    name: values.task
                },
                callback: (r) => {
                    if (r.message) {
                        let task = r.message;
                        test_workflow_transitions(frm, task, d);
                    }
                }
            });
        }
    });
    d.show();
}

function test_workflow_transitions(frm, task, dialog) {
    frappe.call({
        method: 'erpnext_agile.doctype.agile_workflow_scheme.agile_workflow_scheme.get_available_transitions',
        args: {
            workflow_scheme: frm.doc.name,
            from_status: task.issue_status,
            task_name: task.name
        },
        callback: (r) => {
            if (r.message) {
                let html = `
                    <div class="workflow-test-results">
                        <h4>Task: ${task.name}</h4>
                        <p><b>Current Status:</b> ${task.issue_status}</p>
                        <p><b>Issue Type:</b> ${task.issue_type}</p>
                        <p><b>Priority:</b> ${task.issue_priority}</p>
                        <p><b>Story Points:</b> ${task.story_points || 'Not set'}</p>
                        <hr>
                        <h5>Available Transitions:</h5>
                `;
                
                if (r.message.length === 0) {
                    html += '<p class="text-muted">No transitions available from current status</p>';
                } else {
                    html += '<ul>';
                    r.message.forEach(t => {
                        let badge = '';
                        if (t.required_permission) {
                            badge = `<span class="badge badge-info">${t.required_permission}</span>`;
                        }
                        let condition_icon = t.condition ? 
                            '<i class="fa fa-code text-warning" title="Has condition"></i>' : '';
                        
                        html += `<li>
                            <b>${t.transition_name}</b> → ${t.to_status} 
                            ${badge} ${condition_icon}
                        </li>`;
                    });
                    html += '</ul>';
                }
                
                html += '</div>';
                
                dialog.fields_dict.results.$wrapper.html(html);
            }
        }
    });
}

function show_workflow_diagram(frm) {
    frappe.call({
        method: 'erpnext_agile.doctype.agile_workflow_scheme.agile_workflow_scheme.get_workflow_diagram',
        args: {
            workflow_scheme: frm.doc.name
        },
        callback: (r) => {
            if (r.message) {
                let d = new frappe.ui.Dialog({
                    title: __('Workflow Diagram'),
                    size: 'large',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'diagram'
                        }
                    ]
                });
                
                let html = render_workflow_diagram(r.message);
                d.fields_dict.diagram.$wrapper.html(html);
                d.show();
            }
        }
    });
}

function render_workflow_diagram(data) {
    let html = `
        <style>
            .workflow-diagram {
                padding: 20px;
                background: #f8f9fa;
            }
            .workflow-status {
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                border-radius: 5px;
                background: white;
                border: 2px solid #ddd;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .workflow-status.to-do {
                border-color: #6c757d;
            }
            .workflow-status.in-progress {
                border-color: #007bff;
            }
            .workflow-status.done {
                border-color: #28a745;
            }
            .workflow-transition {
                margin: 5px 0;
                padding: 5px;
                background: #e9ecef;
                border-left: 3px solid #007bff;
            }
            .workflow-legend {
                margin-top: 20px;
                padding: 10px;
                background: white;
                border: 1px solid #ddd;
            }
        </style>
        <div class="workflow-diagram">
            <h4>Workflow: ${data.workflow_name || 'Transitions'}</h4>
    `;
    
    // Render statuses and their transitions
    for (let from_status in data.transitions) {
        let status_info = data.statuses[from_status];
        let category_class = (status_info.category || 'To Do').toLowerCase().replace(' ', '-');
        
        html += `
            <div class="workflow-status ${category_class}">
                <h5 style="margin: 0 0 10px 0;">
                    ${status_info.name}
                    <small class="text-muted">(${status_info.category})</small>
                </h5>
        `;
        
        if (data.transitions[from_status].length > 0) {
            html += '<div style="margin-top: 10px;"><b>Can transition to:</b></div>';
            data.transitions[from_status].forEach(t => {
                let perm_badge = t.required_permission ? 
                    `<span class="badge badge-secondary">${t.required_permission}</span>` : '';
                let condition_icon = t.has_condition ? 
                    '<i class="fa fa-code text-warning" title="Has condition"></i>' : '';
                
                html += `
                    <div class="workflow-transition">
                        <i class="fa fa-arrow-right"></i> 
                        <b>${t.transition_name}</b> 
                        ${perm_badge} ${condition_icon}
                    </div>
                `;
            });
        } else {
            html += '<div class="text-muted" style="margin-top: 10px;">No outgoing transitions</div>';
        }
        
        html += '</div>';
    }
    
    html += `
            <div class="workflow-legend">
                <h6>Legend:</h6>
                <p>
                    <span class="badge badge-secondary">Role</span> = Required permission<br>
                    <i class="fa fa-code text-warning"></i> = Has conditional logic
                </p>
            </div>
        </div>
    `;
    
    return html;
}