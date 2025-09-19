frappe.provide('erpnext_agile');

erpnext_agile.AgileBoard = class {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.init();
    }
    
    init() {
        this.setup_board();
        this.bind_events();
    }
    
    setup_board() {
        // Create Jira-style board interface
        this.wrapper.innerHTML = `
            <div class="agile-board-container">
                <div class="board-header">
                    <h3 class="board-title">Sprint Board</h3>
                    <div class="board-actions">
                        <button class="btn btn-primary btn-sm" onclick="erpnext_agile.create_issue()">
                            Create Issue
                        </button>
                    </div>
                </div>
                <div class="board-columns" id="agile-board-columns">
                    <!-- Columns will be populated by load_board_data -->
                </div>
            </div>
        `;
        
        this.load_board_data();
    }
    
    load_board_data() {
        frappe.call({
            method: 'erpnext_agile.api.get_board_data',
            args: {
                agile_project: this.get_current_project()
            },
            callback: (r) => {
                if (r.message) {
                    this.render_board(r.message);
                }
            }
        });
    }
    
    render_board(data) {
        const columns_container = document.getElementById('agile-board-columns');
        columns_container.innerHTML = '';
        
        // Group issues by status
        const issues_by_status = {};
        data.issues.forEach(issue => {
            if (!issues_by_status[issue.status]) {
                issues_by_status[issue.status] = [];
            }
            issues_by_status[issue.status].push(issue);
        });
        
        // Create columns
        data.statuses.forEach(status => {
            const column = this.create_board_column(status, issues_by_status[status.name] || []);
            columns_container.appendChild(column);
        });
        
        this.setup_drag_and_drop();
    }
    
    create_board_column(status, issues) {
        const column = document.createElement('div');
        column.className = 'board-column';
        column.dataset.status = status.name;
        
        column.innerHTML = `
            <div class="column-header" style="background-color: ${status.color}">
                <h4>${status.name}</h4>
                <span class="issue-count">${issues.length}</span>
            </div>
            <div class="column-content" ondrop="erpnext_agile.drop_issue(event)" ondragover="erpnext_agile.allow_drop(event)">
                ${issues.map(issue => this.create_issue_card(issue)).join('')}
            </div>
        `;
        
        return column;
    }
    
    create_issue_card(issue) {
        const assignee_avatar = issue.assignee ? 
            frappe.avatar(issue.assignee, 'avatar-small') : 
            '<div class="avatar avatar-small">?</div>';
        
        return `
            <div class="issue-card" draggable="true" data-issue="${issue.name}" ondragstart="erpnext_agile.drag_issue(event)">
                <div class="issue-header">
                    <span class="issue-key">${issue.issue_key}</span>
                    <span class="issue-type" title="${issue.issue_type}">
                        ${this.get_issue_type_icon(issue.issue_type)}
                    </span>
                </div>
                <div class="issue-summary">${issue.summary}</div>
                <div class="issue-footer">
                    <div class="issue-meta">
                        <span class="priority priority-${issue.priority.toLowerCase()}">${issue.priority}</span>
                        ${issue.story_points ? `<span class="story-points">${issue.story_points} pts</span>` : ''}
                    </div>
                    <div class="issue-assignee">${assignee_avatar}</div>
                </div>
                ${issue.github_pull_request ? '<div class="github-pr-badge">PR #' + issue.github_pull_request + '</div>' : ''}
            </div>
        `;
    }
    
    get_issue_type_icon(issue_type) {
        const icons = {
            'Story': '📖',
            'Bug': '🐛', 
            'Task': '✓',
            'Epic': '🏛️',
            'Sub-task': '⚡',
            'Spike': '🔍'
        };
        return icons[issue_type] || '📋';
    }
    
    setup_drag_and_drop() {
        // Enable drag and drop functionality
        window.erpnext_agile = window.erpnext_agile || {};
        
        window.erpnext_agile.drag_issue = (event) => {
            event.dataTransfer.setData('text/plain', event.target.dataset.issue);
        };
        
        window.erpnext_agile.allow_drop = (event) => {
            event.preventDefault();
        };
        
        window.erpnext_agile.drop_issue = (event) => {
            event.preventDefault();
            const issue_name = event.dataTransfer.getData('text/plain');
            const column = event.target.closest('.board-column');
            const new_status = column.dataset.status;
            
            this.update_issue_status(issue_name, new_status);
        };
    }
    
    update_issue_status(issue_name, new_status) {
        frappe.call({
            method: 'erpnext_agile.api.update_issue_status',
            args: {
                issue_name: issue_name,
                new_status: new_status
            },
            callback: (r) => {
                if (r.message) {
                    frappe.show_alert(r.message.message);
                    this.load_board_data(); // Refresh board
                }
            }
        });
    }
    
    get_current_project() {
        // Get from URL or local storage
        return frappe.get_route()[1] || localStorage.getItem('current_agile_project');
    }
};

// Global functions for Jira-style quick actions
window.erpnext_agile = window.erpnext_agile || {};

erpnext_agile.create_issue = function() {
    const dialog = new frappe.ui.Dialog({
        title: 'Create Issue',
        fields: [
            {
                fieldtype: 'Link',
                fieldname: 'agile_project',
                label: 'Project',
                options: 'Agile Project',
                reqd: 1
            },
            {
                fieldtype: 'Data',
                fieldname: 'summary',
                label: 'Summary',
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'issue_type',
                label: 'Issue Type',
                options: 'Agile Issue Type',
                default: 'Task'
            },
            {
                fieldtype: 'Link',
                fieldname: 'priority',
                label: 'Priority', 
                options: 'Agile Issue Priority',
                default: 'Medium'
            },
            {
                fieldtype: 'Link',
                fieldname: 'assignee',
                label: 'Assignee',
                options: 'User'
            },
            {
                fieldtype: 'Text Editor',
                fieldname: 'description',
                label: 'Description'
            }
        ],
        primary_action_label: 'Create',
        primary_action: function(values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Agile Issue',
                        ...values
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert(`Issue ${r.message.issue_key} created`);
                        dialog.hide();
                        // Refresh current view
                        if (window.cur_page && cur_page.page_name === 'agile-board') {
                            cur_page.agile_board.load_board_data();
                        }
                    }
                }
            });
        }
    });
    
    dialog.show();
};

erpnext_agile.quick_assign = function(issue_name) {
    frappe.prompt('Assignee', (values) => {
        frappe.call({
            method: 'frappe.client.set_value',
            args: {
                doctype: 'Agile Issue',
                name: issue_name,
                fieldname: 'assignee',
                value: values.assignee
            },
            callback: () => {
                frappe.show_alert('Issue assigned successfully');
            }
        });
    }, 'Assign Issue', 'Assign');
};