(function () {
    const patch_smart_notifications = () => {
        // Wait until the notification bell actually exists in the DOM
        if (!$('.dropdown-notifications').length) {
            return setTimeout(patch_smart_notifications, 200);
        }

        // Prevent double injection if this script runs twice
        if (window.__smart_notifications_patched) return;
        window.__smart_notifications_patched = true;

        // The keyword map. Add or tweak these based on your Doctypes!
        const tab_map = {
            'projects': ['Task', 'Issue', 'Project', 'Agile Release'],
            'hr': ['Leave', 'Referral', 'Applicant', 'Employee']
        };

        // Clean, modern, minimalistic UI for the pills. 
        // Using position: sticky so it floats beautifully when you scroll down.
        const tabs_html = `
            <div class="smart-notification-filters" style="display: flex; gap: 8px; padding: 10px 15px; background: var(--bg-color); border-bottom: 1px solid var(--border-color); position: sticky; top: 0; z-index: 10;">
                <button class="btn btn-xs btn-primary rounded-pill smart-tab-btn" data-target="all">All</button>
                <button class="btn btn-xs btn-default rounded-pill smart-tab-btn" data-target="projects">Projects</button>
                <button class="btn btn-xs btn-default rounded-pill smart-tab-btn" data-target="hr">HR & Admin</button>
            </div>
        `;

        // We listen to the Bootstrap event that fires right after the dropdown is rendered
        $(document).on('shown.bs.dropdown', '.dropdown-notifications', function () {
            const $panel = $(this).find('.panel-notifications');
            
            // If we haven't injected our UI into the panel yet, do it now.
            if (!$panel.find('.smart-notification-filters').length) {
                // Prepend places it right at the top of the list, above the first recent-item
                $panel.prepend(tabs_html);
                
                // Handle the click logic
                $panel.find('.smart-tab-btn').on('click', function(e) {
                    e.preventDefault();
                    // CRITICAL: Stop the dropdown from closing when we click a pill!
                    e.stopPropagation(); 

                    // UI: Toggle active state of the pills
                    $panel.find('.smart-tab-btn').removeClass('btn-primary').addClass('btn-default');
                    $(this).removeClass('btn-default').addClass('btn-primary');

                    const target = $(this).data('target');
                    const $items = $panel.find('.recent-item.notification-item');

                    // Filter logic: Blazing fast client-side DOM toggling
                    $items.each(function() {
                        const $item = $(this);
                        
                        // Grab the text from the actual notification message area
                        const text = $item.find('.message').text(); 

                        if (target === 'all') {
                            $item.css('display', ''); // Reset to default display
                        } else {
                            const keywords = tab_map[target] || [];
                            // If the message contains any of our mapped keywords, show it.
                            const match = keywords.some(kw => text.includes(kw));
                            match ? $item.css('display', '') : $item.css('display', 'none');
                        }
                    });
                });
            }
        });
    };

    // Hook into Frappe's loading cycle
    frappe.after_ajax(patch_smart_notifications);
})();