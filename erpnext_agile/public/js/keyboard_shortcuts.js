frappe.provide('erpnext_agile.shortcuts');

$(document).ready(function() {
    // Jira-style keyboard shortcuts
    $(document).keydown(function(e) {
        // Only trigger if not in input fields
        if ($(e.target).is('input, textarea, [contenteditable]')) {
            return;
        }
        
        const key = String.fromCharCode(e.which).toLowerCase();
        
        // Handle key combinations
        if (e.ctrlKey || e.metaKey) {
            return; // Skip ctrl/cmd combinations
        }
        
        switch(key) {
            case 'c':
                // Create issue
                e.preventDefault();
                erpnext_agile.create_issue();
                break;
            case 'g':
                // Navigation shortcuts (need second key)
                erpnext_agile.shortcuts.start_navigation_mode();
                break;
            case '/':
                // Quick search
                e.preventDefault();
                erpnext_agile.shortcuts.focus_search();
                break;
            case '.':
                // Assign to me
                e.preventDefault();
                erpnext_agile.shortcuts.assign_to_me();
                break;
        }
    });
});

erpnext_agile.shortcuts = {
    navigation_mode: false,
    
    start_navigation_mode: function() {
        this.navigation_mode = true;
        frappe.show_alert('Navigation mode - press i for issues, d for dashboard');
        
        // Reset navigation mode after 3 seconds
        setTimeout(() => {
            this.navigation_mode = false;
        }, 3000);
    },
    
    focus_search: function() {
        const search_input = document.querySelector('.navbar-search input');
        if (search_input) {
            search_input.focus();
        }
    },
    
    assign_to_me: function() {
        // Get currently selected issue
        const selected_issue = document.querySelector('.issue-card.selected');
        if (selected_issue) {
            const issue_name = selected_issue.dataset.issue;
            erpnext_agile.quick_assign(issue_name, frappe.session.user);
        }
    }
};