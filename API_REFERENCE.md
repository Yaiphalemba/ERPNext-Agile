# ERPNext Agile - API Reference

## Overview

This document provides detailed API reference for all ERPNext Agile endpoints. All endpoints are accessible via Frappe's RPC API using `frappe.call()`.

## Authentication

All API endpoints require authentication. Include your session cookie or API key in requests.

## Response Format

All API responses follow this format:

```json
{
    "message": "Response data",
    "exc_type": null,
    "exc": null
}
```

## Issue Management API

### Create Agile Issue

**Endpoint:** `erpnext_agile.api.create_agile_issue`

**Description:** Create a new agile issue with Jira-like functionality.

**Parameters:**
- `issue_data` (object): Issue details
  - `project` (string, required): Project name
  - `summary` (string, required): Issue title
  - `description` (string, optional): Issue description
  - `issue_type` (string, optional): Issue type (Story, Task, Bug, Epic, Spike, Sub-task)
  - `issue_priority` (string, optional): Priority (Critical, High, Medium, Low)
  - `issue_status` (string, optional): Initial status
  - `story_points` (number, optional): Story points estimate
  - `sprint` (string, optional): Sprint name
  - `parent_issue` (string, optional): Parent issue name
  - `reporter` (string, optional): Reporter email (defaults to current user)
  - `original_estimate` (string, optional): Time estimate (e.g., "2h 30m")
  - `remaining_estimate` (string, optional): Remaining time estimate
  - `components` (array, optional): List of components
  - `fix_versions` (array, optional): List of fix versions
  - `watchers` (array, optional): List of watcher emails

**Returns:** Task document object

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.create_agile_issue',
    args: {
        issue_data: {
            project: 'My Project',
            summary: 'Implement user authentication',
            description: 'Add OAuth2 support with Google and GitHub',
            issue_type: 'Story',
            issue_priority: 'High',
            story_points: 8,
            original_estimate: '16h',
            components: ['Authentication', 'Security'],
            watchers: ['user1@example.com', 'user2@example.com']
        }
    },
    callback: function(r) {
        if (r.message) {
            console.log('Created issue:', r.message.issue_key);
        }
    }
});
```

### Transition Issue

**Endpoint:** `erpnext_agile.api.transition_issue`

**Description:** Transition issue from one status to another with workflow validation.

**Parameters:**
- `task_name` (string, required): Task name
- `from_status` (string, required): Current status
- `to_status` (string, required): Target status
- `comment` (string, optional): Transition comment

**Returns:** Updated task document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.transition_issue',
    args: {
        task_name: 'TASK-001',
        from_status: 'Open',
        to_status: 'In Progress',
        comment: 'Starting work on this issue'
    },
    callback: function(r) {
        console.log('Issue transitioned successfully');
    }
});
```

### Assign Issue

**Endpoint:** `erpnext_agile.api.assign_issue`

**Description:** Assign issue to users with optional notifications.

**Parameters:**
- `task_name` (string, required): Task name
- `assignees` (array, required): List of user emails
- `notify` (boolean, optional): Send notifications (default: true)

**Returns:** Updated task document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.assign_issue',
    args: {
        task_name: 'TASK-001',
        assignees: ['developer@example.com', 'tester@example.com'],
        notify: true
    },
    callback: function(r) {
        console.log('Issue assigned successfully');
    }
});
```

### Get Issue Details

**Endpoint:** `erpnext_agile.api.get_issue_details`

**Description:** Get comprehensive issue information including assignees and watchers.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** Object containing task details, assignees, watchers, and GitHub link status

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_issue_details',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        const issue = r.message;
        console.log('Issue:', issue.task.subject);
        console.log('Assignees:', issue.assignees);
        console.log('Watchers:', issue.watchers);
        console.log('Has GitHub link:', issue.has_github_link);
    }
});
```

## Sprint Management API

### Create Sprint

**Endpoint:** `erpnext_agile.api.create_sprint`

**Description:** Create a new sprint with validation.

**Parameters:**
- `sprint_data` (object): Sprint details
  - `project` (string, required): Project name
  - `sprint_name` (string, required): Sprint name
  - `start_date` (string, required): Start date (YYYY-MM-DD)
  - `end_date` (string, required): End date (YYYY-MM-DD)
  - `sprint_goal` (string, optional): Sprint goal description

**Returns:** Sprint document object

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.create_sprint',
    args: {
        sprint_data: {
            project: 'My Project',
            sprint_name: 'Sprint 1',
            start_date: '2024-01-01',
            end_date: '2024-01-14',
            sprint_goal: 'Complete user authentication system'
        }
    },
    callback: function(r) {
        console.log('Created sprint:', r.message.name);
    }
});
```

### Start Sprint

**Endpoint:** `erpnext_agile.api.start_sprint`

**Description:** Start a sprint and close any other active sprints in the project.

**Parameters:**
- `sprint_name` (string, required): Sprint name

**Returns:** Updated sprint document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.start_sprint',
    args: {
        sprint_name: 'My Project-Sprint 1'
    },
    callback: function(r) {
        console.log('Sprint started successfully');
    }
});
```

### Complete Sprint

**Endpoint:** `erpnext_agile.api.complete_sprint`

**Description:** Complete a sprint and handle incomplete issues.

**Parameters:**
- `sprint_name` (string, required): Sprint name

**Returns:** Updated sprint document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.complete_sprint',
    args: {
        sprint_name: 'My Project-Sprint 1'
    },
    callback: function(r) {
        console.log('Sprint completed successfully');
    }
});
```

### Add Issues to Sprint

**Endpoint:** `erpnext_agile.api.add_issues_to_sprint`

**Description:** Add multiple issues to a sprint during planning.

**Parameters:**
- `sprint_name` (string, required): Sprint name
- `issue_keys` (array, required): List of issue keys

**Returns:** Object with count of added issues

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.add_issues_to_sprint',
    args: {
        sprint_name: 'My Project-Sprint 1',
        issue_keys: ['PROJ-123', 'PROJ-124', 'PROJ-125']
    },
    callback: function(r) {
        console.log('Added', r.message.added, 'issues to sprint');
    }
});
```

### Remove Issues from Sprint

**Endpoint:** `erpnext_agile.api.remove_issues_from_sprint`

**Description:** Remove issues from a sprint.

**Parameters:**
- `sprint_name` (string, required): Sprint name
- `issue_keys` (array, required): List of issue keys

**Returns:** Object with count of removed issues

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.remove_issues_from_sprint',
    args: {
        sprint_name: 'My Project-Sprint 1',
        issue_keys: ['PROJ-123']
    },
    callback: function(r) {
        console.log('Removed', r.message.removed, 'issues from sprint');
    }
});
```

### Get Sprint Report

**Endpoint:** `erpnext_agile.api.get_sprint_report`

**Description:** Generate comprehensive sprint report with metrics and statistics.

**Parameters:**
- `sprint_name` (string, required): Sprint name

**Returns:** Comprehensive sprint report object

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_sprint_report',
    args: {
        sprint_name: 'My Project-Sprint 1'
    },
    callback: function(r) {
        const report = r.message;
        console.log('Sprint:', report.sprint.sprint_name);
        console.log('Total issues:', report.issue_stats.total);
        console.log('Completed issues:', report.issue_stats.completed);
        console.log('Velocity:', report.team_velocity.average);
    }
});
```

### Get Sprint Burndown

**Endpoint:** `erpnext_agile.api.get_sprint_burndown`

**Description:** Get burndown chart data for sprint visualization.

**Parameters:**
- `sprint_name` (string, required): Sprint name

**Returns:** Array of burndown data points

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_sprint_burndown',
    args: {
        sprint_name: 'My Project-Sprint 1'
    },
    callback: function(r) {
        const burndownData = r.message;
        // Use data for chart visualization
        console.log('Burndown data points:', burndownData.length);
    }
});
```

## Backlog Management API

### Get Backlog

**Endpoint:** `erpnext_agile.api.get_backlog`

**Description:** Get project backlog items (issues not in any sprint).

**Parameters:**
- `project` (string, required): Project name
- `filters` (object, optional): Filter criteria
  - `group_by` (string, optional): Group by 'epic' or null

**Returns:** Array of backlog items or grouped object

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_backlog',
    args: {
        project: 'My Project',
        filters: {
            group_by: 'epic'
        }
    },
    callback: function(r) {
        const backlog = r.message;
        if (backlog.with_epic) {
            console.log('Epics with items:', Object.keys(backlog.with_epic));
        }
        console.log('Items without epic:', backlog.without_epic.length);
    }
});
```

### Estimate Backlog Item

**Endpoint:** `erpnext_agile.api.estimate_backlog_item`

**Description:** Estimate story points for a backlog item.

**Parameters:**
- `task_name` (string, required): Task name
- `story_points` (number, required): Story points estimate
- `estimation_method` (string, optional): Estimation method (default: 'planning_poker')

**Returns:** Object with success status and point changes

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.estimate_backlog_item',
    args: {
        task_name: 'TASK-001',
        story_points: 5,
        estimation_method: 'planning_poker'
    },
    callback: function(r) {
        console.log('Estimation updated:', r.message.new_points, 'points');
    }
});
```

### Split Story

**Endpoint:** `erpnext_agile.api.split_story`

**Description:** Split a user story into multiple sub-stories.

**Parameters:**
- `task_name` (string, required): Parent task name
- `split_data` (object): Split details
  - `splits` (array, required): Array of split objects
    - `summary` (string, required): Sub-story title
    - `description` (string, optional): Sub-story description
    - `story_points` (number, optional): Story points for sub-story

**Returns:** Object with parent and sub-task information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.split_story',
    args: {
        task_name: 'TASK-001',
        split_data: {
            splits: [
                {
                    summary: 'User login functionality',
                    description: 'Implement basic login',
                    story_points: 3
                },
                {
                    summary: 'Password reset functionality',
                    description: 'Implement password reset',
                    story_points: 2
                }
            ]
        }
    },
    callback: function(r) {
        console.log('Split into', r.message.sub_tasks.length, 'sub-tasks');
    }
});
```

### Get Backlog Metrics

**Endpoint:** `erpnext_agile.api.get_backlog_metrics`

**Description:** Get backlog health metrics and statistics.

**Parameters:**
- `project` (string, required): Project name

**Returns:** Object with backlog metrics

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_backlog_metrics',
    args: {
        project: 'My Project'
    },
    callback: function(r) {
        const metrics = r.message;
        console.log('Total items:', metrics.total_items);
        console.log('Total points:', metrics.total_points);
        console.log('Estimated items:', metrics.estimated_items);
        console.log('Estimation percentage:', metrics.estimation_percentage + '%');
    }
});
```

## Board Management API

### Get Board Data

**Endpoint:** `erpnext_agile.api.get_board_data`

**Description:** Get board data for Kanban/Scrum board visualization.

**Parameters:**
- `project` (string, required): Project name
- `sprint` (string, optional): Sprint name for sprint view
- `view_type` (string, optional): 'sprint' or 'backlog' (default: 'sprint')

**Returns:** Board data structure with columns and issues

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_board_data',
    args: {
        project: 'My Project',
        sprint: 'My Project-Sprint 1',
        view_type: 'sprint'
    },
    callback: function(r) {
        const board = r.message;
        console.log('Board columns:', Object.keys(board.columns));
        console.log('Active sprint:', board.active_sprint);
    }
});
```

### Move Issue

**Endpoint:** `erpnext_agile.api.move_issue`

**Description:** Move issue from one column to another (drag & drop).

**Parameters:**
- `task_name` (string, required): Task name
- `from_status` (string, required): Current status
- `to_status` (string, required): Target status
- `position` (number, optional): Position in target column

**Returns:** Object with success status

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.move_issue',
    args: {
        task_name: 'TASK-001',
        from_status: 'Open',
        to_status: 'In Progress',
        position: 0
    },
    callback: function(r) {
        console.log('Issue moved successfully');
    }
});
```

### Quick Create Issue

**Endpoint:** `erpnext_agile.api.quick_create_issue`

**Description:** Quick create issue from board (inline creation).

**Parameters:**
- `project` (string, required): Project name
- `status` (string, required): Initial status
- `issue_data` (object): Issue details
  - `summary` (string, required): Issue title
  - `description` (string, optional): Issue description
  - `issue_type` (string, optional): Issue type
  - `issue_priority` (string, optional): Priority
  - `story_points` (number, optional): Story points
  - `sprint` (string, optional): Sprint name

**Returns:** Object with created task information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.quick_create_issue',
    args: {
        project: 'My Project',
        status: 'Open',
        issue_data: {
            summary: 'Fix login bug',
            description: 'Users cannot login with special characters',
            issue_type: 'Bug',
            issue_priority: 'High',
            story_points: 2
        }
    },
    callback: function(r) {
        console.log('Created issue:', r.message.issue_key);
    }
});
```

### Get Board Metrics

**Endpoint:** `erpnext_agile.api.get_board_metrics`

**Description:** Get board metrics for visualization and analysis.

**Parameters:**
- `project` (string, required): Project name
- `sprint` (string, optional): Sprint name

**Returns:** Object with board metrics

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_board_metrics',
    args: {
        project: 'My Project',
        sprint: 'My Project-Sprint 1'
    },
    callback: function(r) {
        const metrics = r.message;
        console.log('Total issues:', metrics.total_issues);
        console.log('Total points:', metrics.total_points);
        console.log('Cycle time:', metrics.cycle_time.average_days, 'days');
        console.log('Throughput:', metrics.throughput.issues_per_day, 'issues/day');
    }
});
```

### Filter Board

**Endpoint:** `erpnext_agile.api.filter_board`

**Description:** Filter board by various criteria.

**Parameters:**
- `project` (string, required): Project name
- `sprint` (string, optional): Sprint name
- `filters` (object, optional): Filter criteria
  - `assignee` (string, optional): Filter by assignee
  - `issue_type` (string, optional): Filter by issue type
  - `priority` (string, optional): Filter by priority

**Returns:** Filtered board data

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.filter_board',
    args: {
        project: 'My Project',
        sprint: 'My Project-Sprint 1',
        filters: {
            assignee: 'developer@example.com',
            issue_type: 'Story',
            priority: 'High'
        }
    },
    callback: function(r) {
        console.log('Filtered board data received');
    }
});
```

### Get Swimlane Data

**Endpoint:** `erpnext_agile.api.get_swimlane_data`

**Description:** Get board data organized by swimlanes.

**Parameters:**
- `project` (string, required): Project name
- `sprint` (string, optional): Sprint name
- `swimlane_by` (string, optional): 'issue_type', 'assignee', or 'type' (default: 'issue_type')

**Returns:** Board data organized by swimlanes

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_swimlane_data',
    args: {
        project: 'My Project',
        sprint: 'My Project-Sprint 1',
        swimlane_by: 'issue_type'
    },
    callback: function(r) {
        const swimlanes = r.message;
        console.log('Swimlanes:', Object.keys(swimlanes.swimlanes));
    }
});
```

## Time Tracking API

### Log Work

**Endpoint:** `erpnext_agile.api.log_work`

**Description:** Log work time on an issue.

**Parameters:**
- `task_name` (string, required): Task name
- `time_spent` (string, required): Time spent (e.g., "2h 30m", "1.5h", "90m")
- `work_description` (string, required): Description of work done
- `work_date` (string, optional): Work date (YYYY-MM-DD, defaults to today)

**Returns:** Object with logged time information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.log_work',
    args: {
        task_name: 'TASK-001',
        time_spent: '2h 30m',
        work_description: 'Implemented OAuth2 Google integration',
        work_date: '2024-01-15'
    },
    callback: function(r) {
        console.log('Logged', r.message.time_logged, 'of work');
        console.log('Total time spent:', r.message.total_time_spent);
    }
});
```

### Update Estimate

**Endpoint:** `erpnext_agile.api.update_estimate`

**Description:** Update time estimates for an issue.

**Parameters:**
- `task_name` (string, required): Task name
- `estimate_type` (string, required): 'original' or 'remaining'
- `time_value` (string, required): Time value (e.g., "8h", "1d")

**Returns:** Object with updated estimate information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.update_estimate',
    args: {
        task_name: 'TASK-001',
        estimate_type: 'original',
        time_value: '8h'
    },
    callback: function(r) {
        console.log('Updated', r.message.estimate_type, 'estimate to', r.message.new_value);
    }
});
```

### Get Time Tracking Report

**Endpoint:** `erpnext_agile.api.get_time_tracking_report`

**Description:** Get comprehensive time tracking report for an issue.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** Object with detailed time tracking information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_time_tracking_report',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        const report = r.message;
        console.log('Issue:', report.issue_key);
        console.log('Original estimate:', report.summary.original_estimate);
        console.log('Time spent:', report.summary.time_spent);
        console.log('Remaining estimate:', report.summary.remaining_estimate);
        console.log('Variance:', report.summary.variance);
        console.log('Work logs:', report.total_logs);
    }
});
```

### Get Team Time Report

**Endpoint:** `erpnext_agile.api.get_team_time_report`

**Description:** Get team time tracking report for a project.

**Parameters:**
- `project` (string, required): Project name
- `start_date` (string, optional): Start date (YYYY-MM-DD, defaults to 30 days ago)
- `end_date` (string, optional): End date (YYYY-MM-DD, defaults to today)

**Returns:** Object with team time tracking summary

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_team_time_report',
    args: {
        project: 'My Project',
        start_date: '2024-01-01',
        end_date: '2024-01-31'
    },
    callback: function(r) {
        const report = r.message;
        console.log('Team total time:', report.team_total);
        console.log('Team members:', report.team_members.length);
        report.team_members.forEach(member => {
            console.log(member.user_fullname + ':', member.total_time);
        });
    }
});
```

### Start Timer

**Endpoint:** `erpnext_agile.api.start_timer`

**Description:** Start work timer for an issue.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** Object with timer information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.start_timer',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        console.log('Timer started:', r.message.timer);
        console.log('Start time:', r.message.start_time);
    }
});
```

### Stop Timer

**Endpoint:** `erpnext_agile.api.stop_timer`

**Description:** Stop work timer and log work.

**Parameters:**
- `timer_name` (string, required): Timer name
- `work_description` (string, optional): Work description

**Returns:** Object with logged time information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.stop_timer',
    args: {
        timer_name: 'TIMER-001',
        work_description: 'Completed OAuth2 implementation'
    },
    callback: function(r) {
        console.log('Timer stopped. Time logged:', r.message.time_spent);
    }
});
```

## GitHub Integration API

### Sync Agile Issue to GitHub

**Endpoint:** `erpnext_agile.api.sync_agile_issue_to_github`

**Description:** Sync an agile issue to GitHub.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** GitHub issue information

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.sync_agile_issue_to_github',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        console.log('GitHub issue created:', r.message.issue.number);
    }
});
```

### Sync GitHub Issue to Agile

**Endpoint:** `erpnext_agile.api.sync_github_issue_to_agile`

**Description:** Sync a GitHub issue to agile task.

**Parameters:**
- `repo_issue_name` (string, required): Repository issue name

**Returns:** Created/updated task document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.sync_github_issue_to_agile',
    args: {
        repo_issue_name: 'REPO-ISSUE-001'
    },
    callback: function(r) {
        console.log('Agile task created:', r.message.issue_key);
    }
});
```

### Bulk Sync Project Issues

**Endpoint:** `erpnext_agile.api.bulk_sync_project_issues`

**Description:** Bulk sync all GitHub issues for a project.

**Parameters:**
- `project_name` (string, required): Project name

**Returns:** Object with sync results

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.bulk_sync_project_issues',
    args: {
        project_name: 'My Project'
    },
    callback: function(r) {
        console.log('Bulk sync completed:');
        console.log('Synced:', r.message.synced);
        console.log('Created:', r.message.created);
        console.log('Updated:', r.message.updated);
    }
});
```

## Project Queries API

### Get Project Overview

**Endpoint:** `erpnext_agile.api.get_project_overview`

**Description:** Get comprehensive project overview with statistics.

**Parameters:**
- `project` (string, required): Project name

**Returns:** Object with project overview data

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_project_overview',
    args: {
        project: 'My Project'
    },
    callback: function(r) {
        const overview = r.message;
        console.log('Project:', overview.project.project_name);
        console.log('Active sprint:', overview.active_sprint?.sprint_name);
        console.log('Total issues:', overview.statistics.total_issues);
        console.log('Completed issues:', overview.statistics.completed_issues);
        console.log('Completion percentage:', overview.statistics.completion_percentage + '%');
    }
});
```

### Search Issues

**Endpoint:** `erpnext_agile.api.search_issues`

**Description:** Search issues with filters.

**Parameters:**
- `query` (string, required): Search query
- `project` (string, optional): Project name
- `filters` (object, optional): Additional filters
  - `sprint` (string, optional): Sprint name
  - `status` (string, optional): Issue status
  - `assignee` (string, optional): Assignee email

**Returns:** Array of matching issues

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.search_issues',
    args: {
        query: 'authentication',
        project: 'My Project',
        filters: {
            status: 'Open',
            assignee: 'developer@example.com'
        }
    },
    callback: function(r) {
        console.log('Found', r.message.length, 'issues');
        r.message.forEach(issue => {
            console.log(issue.issue_key + ':', issue.subject);
        });
    }
});
```

### Get User Dashboard

**Endpoint:** `erpnext_agile.api.get_user_dashboard`

**Description:** Get current user's agile dashboard.

**Parameters:** None (uses current user)

**Returns:** Object with user's dashboard data

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.api.get_user_dashboard',
    callback: function(r) {
        const dashboard = r.message;
        console.log('My assigned issues:', dashboard.assigned_issues.length);
        console.log('My reported issues:', dashboard.reported_issues.length);
        console.log('My projects:', dashboard.projects.length);
    }
});
```

## Version Control API

### Create Issue Version

**Endpoint:** `erpnext_agile.version_control.create_issue_version`

**Description:** Create a version snapshot of an issue.

**Parameters:**
- `task_name` (string, required): Task name
- `change_description` (string, optional): Description of changes

**Returns:** Version document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.create_issue_version',
    args: {
        task_name: 'TASK-001',
        change_description: 'Before major refactor'
    },
    callback: function(r) {
        console.log('Version created:', r.message.version_number);
    }
});
```

### Get Version History

**Endpoint:** `erpnext_agile.version_control.get_version_history`

**Description:** Get version history for an issue.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** Array of version records

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.get_version_history',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        const history = r.message;
        history.forEach(version => {
            console.log('v' + version.version_number + ' by ' + version.created_by + ' at ' + version.created_at);
        });
    }
});
```

### Restore Issue Version

**Endpoint:** `erpnext_agile.version_control.restore_issue_version`

**Description:** Restore issue to a specific version.

**Parameters:**
- `task_name` (string, required): Task name
- `version_number` (number, required): Version number to restore

**Returns:** Updated task document

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.restore_issue_version',
    args: {
        task_name: 'TASK-001',
        version_number: 3
    },
    callback: function(r) {
        frappe.show_alert('Issue restored to version 3');
        cur_frm.reload_doc();
    }
});
```

### Compare with Current

**Endpoint:** `erpnext_agile.version_control.compare_with_current`

**Description:** Compare a version with current state.

**Parameters:**
- `task_name` (string, required): Task name
- `version_number` (number, required): Version number to compare

**Returns:** Array of differences

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.compare_with_current',
    args: {
        task_name: 'TASK-001',
        version_number: 5
    },
    callback: function(r) {
        const diff = r.message;
        diff.forEach(change => {
            console.log(change.field + ':', change.change_type);
        });
    }
});
```

### Get Version Statistics

**Endpoint:** `erpnext_agile.version_control.get_version_statistics`

**Description:** Get version statistics for an issue.

**Parameters:**
- `task_name` (string, required): Task name

**Returns:** Object with version statistics

**Example:**
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.get_version_statistics',
    args: {
        task_name: 'TASK-001'
    },
    callback: function(r) {
        const stats = r.message;
        console.log('Total versions:', stats.total_versions);
        console.log('Contributors:', stats.unique_contributors);
    }
});
```

## Error Handling

### Common Error Responses

All API endpoints may return these error responses:

```json
{
    "message": null,
    "exc_type": "ValidationError",
    "exc": "Project is not agile-enabled"
}
```

### Error Types

- **ValidationError**: Invalid input data or business rule violation
- **PermissionError**: User doesn't have required permissions
- **NotFoundError**: Requested resource doesn't exist
- **IntegrityError**: Database constraint violation
- **ServerError**: Internal server error

### Handling Errors

```javascript
frappe.call({
    method: 'erpnext_agile.api.create_agile_issue',
    args: { /* ... */ },
    callback: function(r) {
        if (r.exc) {
            // Handle error
            frappe.msgprint({
                title: 'Error',
                message: r.exc,
                indicator: 'red'
            });
        } else {
            // Handle success
            console.log('Success:', r.message);
        }
    }
});
```

## Rate Limiting

API endpoints are subject to ERPNext's rate limiting. For high-volume operations, consider:

1. Using bulk endpoints where available
2. Implementing client-side throttling
3. Using background jobs for heavy operations
4. Caching frequently accessed data

## Authentication

All API endpoints require authentication. Include your session cookie or API key in requests:

```javascript
// Session-based authentication (default)
frappe.call({
    method: 'erpnext_agile.api.get_backlog',
    args: { project: 'My Project' }
});

// API key authentication
frappe.call({
    method: 'erpnext_agile.api.get_backlog',
    args: { project: 'My Project' },
    headers: {
        'Authorization': 'token your-api-key:your-api-secret'
    }
});
```

## Best Practices

### Performance

1. **Use appropriate filters** to limit data returned
2. **Cache frequently accessed data** on the client side
3. **Use pagination** for large datasets
4. **Batch operations** when possible

### Error Handling

1. **Always check for errors** in callback functions
2. **Provide meaningful error messages** to users
3. **Log errors** for debugging
4. **Implement retry logic** for transient failures

### Security

1. **Validate all inputs** on both client and server
2. **Use parameterized queries** to prevent SQL injection
3. **Check permissions** before performing operations
4. **Sanitize user input** before displaying

### Data Consistency

1. **Use transactions** for multi-step operations
2. **Validate business rules** before saving
3. **Handle concurrent modifications** gracefully
4. **Provide rollback mechanisms** for failed operations
