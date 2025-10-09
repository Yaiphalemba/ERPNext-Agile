# ERPNext Agile - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation Guide](#installation-guide)
4. [Quick Start](#quick-start)
5. [User Guide](#user-guide)
6. [API Reference](#api-reference)
7. [Developer Guide](#developer-guide)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)
11. [Required File Structure](#required-file-structure)

---

## Overview

ERPNext Agile is a comprehensive Jira-like agile project management system built for ERPNext. It provides enterprise-grade issue tracking, sprint management, backlog organization, time tracking, and GitHub integration - all seamlessly integrated into your ERPNext environment.

### Key Benefits

- **Native ERPNext Integration**: Built specifically for ERPNext, not a third-party addon
- **Jira-like Experience**: Familiar workflow for teams migrating from Jira
- **Complete Agile Suite**: Issues, sprints, backlogs, boards, time tracking, and reporting
- **GitHub Integration**: Bi-directional sync with GitHub repositories
- **Version Control**: Complete issue history and rollback capabilities
- **Scalable Architecture**: Handles teams from 5 to 500+ users
- **Extensible**: Easy to customize and extend

### Architecture

The system consists of:

- **Backend Managers**: Python classes handling core business logic
- **DocTypes**: ERPNext data models for all agile entities
- **API Layer**: Whitelisted endpoints for frontend integration
- **Frontend Enhancements**: JavaScript extensions for Task and Project forms
- **Scheduled Tasks**: Automated metrics and reporting
- **Version Control**: Complete change tracking system

---

## Features

### 🎯 Issue Management
- **Jira-style Issue Keys**: Unique identifiers like PROJ-123
- **Issue Types**: Story, Task, Bug, Epic, Spike, Sub-task
- **Priority Levels**: Critical, High, Medium, Low
- **Custom Workflows**: Configurable status transitions
- **Multi-user Assignment**: Assign issues to multiple team members
- **Watchers & Notifications**: Stay updated on issue changes
- **Parent-child Relationships**: Link related issues
- **Components & Versions**: Organize by system components and releases

### 🏃 Sprint Management
- **Sprint Planning**: Create and manage development sprints
- **Sprint States**: Future, Active, Completed
- **Capacity Management**: Track team velocity and capacity
- **Burndown Charts**: Automated hourly burndown generation
- **Velocity Tracking**: Historical sprint performance
- **Sprint Health**: Real-time sprint metrics
- **Issue Scope Management**: Add/remove issues during sprint

### 📋 Backlog Management
- **Product Backlog**: Centralized issue repository
- **Story Point Estimation**: Planning poker and estimation tools
- **Backlog Refinement**: Grooming sessions and acceptance criteria
- **Story Splitting**: Break down large stories
- **Prioritization**: Value-effort ratio and custom algorithms
- **Bulk Operations**: Mass estimation and prioritization

### 🎨 Kanban Board
- **Visual Workflow**: Drag-and-drop issue movement
- **Swimlanes**: Organize by parent_issue, assignee, or issue type
- **Quick Issue Creation**: Inline issue creation from board
- **Board Filtering**: Filter by assignee, parent_issue, type, priority
- **Cycle Time Metrics**: Track issue flow efficiency
- **Throughput Analysis**: Issues completed per day
- **Real-time Updates**: Live board synchronization

### ⏱️ Time Tracking
- **Work Log Entries**: Detailed time logging with descriptions
- **Time Estimates**: Original and remaining time estimates
- **Work Timers**: Start/stop timers for accurate tracking
- **Team Time Reports**: Comprehensive time analytics
- **Time Variance Tracking**: Compare estimates vs actual
- **Flexible Time Formats**: Support for hours, minutes, and decimal formats
- **Audit Trail**: Complete time tracking history

### 🔗 GitHub Integration
- **Bi-directional Sync**: Sync issues between ERPNext and GitHub
- **Automatic Issue Creation**: Create GitHub issues from agile tasks
- **Branch Naming Conventions**: Automated feature branch suggestions
- **Commit Linking**: Link commits to issues
- **PR Tracking**: Monitor pull request progress
- **Bulk Sync Operations**: Sync entire projects at once
- **Label Management**: Automatic GitHub label creation

### 📊 Version Control
- **Complete Issue History**: Track every change to issues
- **Version Snapshots**: Create manual version checkpoints
- **Compare Versions**: See what changed between versions
- **Restore Capability**: Rollback to any previous version
- **Change Tracking**: Detailed audit trail
- **Bulk Version Operations**: Manage versions across multiple issues

### 📈 Reports & Analytics
- **Sprint Reports**: Comprehensive sprint analysis
- **Velocity Charts**: Team performance over time
- **Burndown Charts**: Sprint progress visualization
- **Cycle Time Analysis**: Issue flow efficiency
- **Throughput Metrics**: Team productivity measures
- **Backlog Health**: Estimation and readiness metrics
- **Team Time Reports**: Time tracking analytics

---

## Installation Guide

### Prerequisites

- ERPNext v15+ installed and running
- Python 3.10+
- Bench CLI tool
- Git

### Step 1: Download the App

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app
bench get-app https://github.com/your-username/erpnext_agile.git
```

### Step 2: Install the App

```bash
# Install the app to your site
bench --site your-site.com install-app erpnext_agile

# Migrate the database
bench --site your-site.com migrate

# Restart the server
bench restart
```

### Step 3: Post-Installation Setup

After installation, the app will automatically:

1. Create all required DocTypes
2. Set up default issue types, priorities, and statuses
3. Configure custom fields for Task and Project
4. Install JavaScript enhancements
5. Set up scheduled tasks

### Step 4: Enable Agile for Projects

1. Go to **Project** list
2. Open a project you want to make agile
3. Check **Enable Agile** checkbox
4. Set **Project Key** (e.g., "PROJ" for PROJ-123 issue keys)
5. Configure **Workflow Scheme** and **Permission Scheme**
6. Save the project

### Step 5: Configure GitHub Integration (Optional)

1. Install the GitHub Integration app:
   ```bash
   bench get-app https://github.com/frappe/github_integration.git
   bench --site your-site.com install-app github_integration
   ```

2. In your project settings:
   - Set **GitHub Repository** (format: owner/repo)
   - Enable **Auto Create GitHub Issues**
   - Configure **Branch Naming Convention**

### Verification

To verify the installation:

1. Go to **Task** list and create a new task
2. Check that agile fields are visible
3. Create a new **Agile Sprint**
4. Test the **View Board** button in Project form

---

## Quick Start

### 1. Create Your First Agile Issue

```python
from erpnext_agile.agile_issue_manager import AgileIssueManager

manager = AgileIssueManager()
issue = manager.create_agile_issue({
    'project': 'My Project',
    'summary': 'Implement user authentication',
    'description': 'Add OAuth2 support with Google and GitHub',
    'issue_type': 'Story',
    'issue_priority': 'High',
    'story_points': 8
})

print(f"Created issue: {issue.issue_key}")
```

### 2. Start a Sprint

```python
from erpnext_agile.agile_sprint_manager import AgileSprintManager

manager = AgileSprintManager()
sprint = manager.create_sprint({
    'project': 'My Project',
    'sprint_name': 'Sprint 1',
    'start_date': '2024-01-01',
    'end_date': '2024-01-14',
    'sprint_goal': 'Complete user authentication system'
})

# Start the sprint
manager.start_sprint(sprint.name)
```

### 3. Log Work Time

```python
from erpnext_agile.agile_time_tracking import AgileTimeTracking

tracker = AgileTimeTracking()
result = tracker.log_work(
    task_name='TASK-001',
    time_spent='2h 30m',
    work_description='Implemented OAuth2 Google integration'
)

print(f"Logged {result['time_logged']} of work")
```

### 4. View the Board

```python
from erpnext_agile.agile_board_manager import AgileBoardManager

manager = AgileBoardManager()
board_data = manager.get_board_data(
    project='My Project',
    sprint='My Project-Sprint 1',
    view_type='sprint'
)

print(f"Board has {len(board_data['columns'])} columns")
```

---

## User Guide

### Issue Management

#### Creating Issues

1. **From Task Form**:
   - Go to Task list → New
   - Fill in standard fields (Subject, Description, Project)
   - Check **Is Agile** checkbox
   - Fill agile-specific fields (Type, Priority, Story Points, etc.)
   - Save

2. **From Board**:
   - Go to Project → View Board
   - Click **Quick Create** in any column
   - Fill issue details inline
   - Issue is created and added to the column

3. **Via API**:
   ```javascript
   frappe.call({
       method: 'erpnext_agile.api.create_agile_issue',
       args: {
           issue_data: {
               project: 'My Project',
               summary: 'Fix login bug',
               issue_type: 'Bug',
               issue_priority: 'High'
           }
       },
       callback: function(r) {
           console.log('Created:', r.message.issue_key);
       }
   });
   ```

#### Issue Types

- **Story**: User-facing feature or functionality
- **Task**: Technical work or maintenance
- **Bug**: Defect or issue to be fixed
- **Epic**: Large feature spanning multiple sprints
- **Spike**: Research or investigation work
- **Sub-task**: Part of a larger issue

#### Issue Priorities

- **Critical**: System down, security vulnerability
- **High**: Major feature, important bug
- **Medium**: Standard feature or bug
- **Low**: Nice-to-have, minor improvement

#### Issue Statuses

Statuses are organized into categories:

- **To Do**: Not started
- **In Progress**: Currently being worked on
- **Done**: Completed

Custom statuses can be created and configured in workflow schemes.

### Sprint Management

#### Creating Sprints

1. Go to **Agile Sprint** list
2. Click **New**
3. Fill in:
   - **Sprint Name**: e.g., "Sprint 1"
   - **Project**: Select your agile project
   - **Start Date** and **End Date**
   - **Sprint Goal**: What you want to achieve
4. Save

#### Sprint States

- **Future**: Created but not started
- **Active**: Currently running
- **Completed**: Finished

#### Sprint Planning

1. **Add Issues to Sprint**:
   - Go to Project → View Backlog
   - Select issues to add to sprint
   - Use **Add to Sprint** action
   - Or drag issues from backlog to sprint in board view

2. **Sprint Capacity**:
   - Consider team velocity from previous sprints
   - Account for holidays and time off
   - Leave buffer for unexpected work

#### Sprint Execution

1. **Daily Standups**: Use the board to track progress
2. **Burndown Monitoring**: Check burndown charts daily
3. **Scope Management**: Add/remove issues as needed
4. **Sprint Review**: Demo completed work
5. **Sprint Retrospective**: Identify improvements

### Backlog Management

#### Backlog Organization

The product backlog contains all issues not currently in a sprint:

1. **Prioritization**: Order by business value and effort
2. **Estimation**: Add story points to all items
3. **Refinement**: Ensure items are ready for sprint planning

#### Backlog Refinement

Regular grooming sessions to:

1. **Break Down Stories**: Split large stories into smaller ones
2. **Add Acceptance Criteria**: Define what "done" means
3. **Estimate Effort**: Assign story points
4. **Prioritize**: Order by business value
5. **Remove Outdated Items**: Keep backlog current

### Board Usage

#### Kanban Board

The board provides a visual representation of your workflow:

1. **Columns**: Represent workflow statuses
2. **Cards**: Represent issues
3. **Drag & Drop**: Move issues between columns
4. **Quick Actions**: Create, edit, and manage issues inline

#### Board Views

- **Sprint View**: Shows issues in current sprint
- **Backlog View**: Shows all unassigned issues

#### Board Filtering

Filter the board by:
- **Assignee**: Show only issues assigned to specific users
- **Issue Type**: Filter by Story, Bug, Task, etc.
- **Priority**: Show only high-priority issues

#### Swimlanes

Organize issues horizontally by:
- **Assignee**: Show who's working on what
- **Issue Type**: Separate Stories, Bugs, Tasks

### Time Tracking

#### Logging Work

1. **From Task Form**:
   - Open the task
   - Click **Log Work** button
   - Enter time spent (e.g., "2h 30m")
   - Add work description
   - Save

2. **Using Timer**:
   - Click **Start Timer** on task
   - Work on the issue
   - Click **Stop Timer** when done
   - Add work description
   - Time is automatically logged

3. **Time Formats**:
   - "2h 30m" - 2 hours 30 minutes
   - "1.5h" - 1.5 hours
   - "90m" - 90 minutes
   - "2h" - 2 hours

#### Time Estimates

Set estimates for planning:

1. **Original Estimate**: Initial time estimate
2. **Remaining Estimate**: Time left to complete
3. **Time Spent**: Actual time logged

#### Time Reports

Access time tracking reports:

1. **Issue Time Report**: See all time logged for an issue
2. **Team Time Report**: Team time tracking summary
3. **Sprint Time Report**: Time spent in current sprint

### GitHub Integration

#### Setting Up Integration

1. **Install GitHub Integration App**:
   ```bash
   bench get-app https://github.com/frappe/github_integration.git
   bench --site your-site.com install-app github_integration
   ```

2. **Configure Project**:
   - Set GitHub Repository (owner/repo format)
   - Enable Auto Create GitHub Issues
   - Set Branch Naming Convention

3. **Link User Accounts**:
   - Add GitHub username to User records
   - This enables proper assignment syncing

#### Syncing Issues

1. **Agile to GitHub**:
   - Create issue in ERPNext
   - Click **Sync to GitHub** button
   - GitHub issue is created with proper labels

2. **GitHub to Agile**:
   - Create issue in GitHub
   - Use **Sync from GitHub** in project
   - Agile task is created automatically

3. **Bulk Sync**:
   - Go to Project form
   - Click **Bulk Sync GitHub Issues**
   - All GitHub issues are synced

#### Branch Management

The system suggests branch names based on your convention:

- `feature/{issue_key}-{summary}` (default)
- `bugfix/{issue_key}-{summary}`
- `hotfix/{issue_key}-{summary}`

### Version Control

#### Creating Versions

Versions are automatically created when important fields change:
- Subject
- Description
- Issue Type
- Priority
- Status
- Story Points
- Sprint

#### Manual Versions

Create manual checkpoints:

```python
from erpnext_agile.version_control import IssueVersionControl

vc = IssueVersionControl('TASK-001')
version = vc.create_version('Before major refactor')
```

#### Restoring Versions

Rollback to previous state:

```python
vc = IssueVersionControl('TASK-001')
vc.restore_version(5)  # Restore to version 5
```

#### Comparing Versions

See what changed:

```python
diff = vc.compare_with_current(3)
for change in diff:
    print(f"{change['field']}: {change['change_type']}")
```

---

## API Reference

### Issue Management

#### `create_agile_issue(issue_data)`

Create a new agile issue.

**Parameters:**
- `issue_data` (dict): Issue details
  - `project` (str): Project name
  - `summary` (str): Issue title
  - `description` (str): Issue description
  - `issue_type` (str): Issue type
  - `issue_priority` (str): Priority level
  - `story_points` (int): Story points
  - `sprint` (str): Sprint name

**Returns:** Task document

**Example:**
```python
frappe.call({
    method: 'erpnext_agile.api.create_agile_issue',
    args: {
        issue_data: {
            project: 'My Project',
            summary: 'Implement login',
            issue_type: 'Story',
            issue_priority: 'High',
            story_points: 5
        }
    }
});
```

#### `transition_issue(task_name, from_status, to_status, comment)`

Transition issue between statuses.

**Parameters:**
- `task_name` (str): Task name
- `from_status` (str): Current status
- `to_status` (str): Target status
- `comment` (str): Optional comment

**Returns:** Updated task document

#### `assign_issue(task_name, assignees, notify)`

Assign issue to users.

**Parameters:**
- `task_name` (str): Task name
- `assignees` (list): List of user emails
- `notify` (bool): Send notifications

**Returns:** Updated task document

### Sprint Management

#### `create_sprint(sprint_data)`

Create a new sprint.

**Parameters:**
- `sprint_data` (dict): Sprint details
  - `project` (str): Project name
  - `sprint_name` (str): Sprint name
  - `start_date` (str): Start date
  - `end_date` (str): End date
  - `sprint_goal` (str): Sprint goal

**Returns:** Sprint document

#### `start_sprint(sprint_name)`

Start a sprint.

**Parameters:**
- `sprint_name` (str): Sprint name

**Returns:** Updated sprint document

#### `complete_sprint(sprint_name)`

Complete a sprint.

**Parameters:**
- `sprint_name` (str): Sprint name

**Returns:** Updated sprint document

#### `get_sprint_report(sprint_name)`

Get comprehensive sprint report.

**Parameters:**
- `sprint_name` (str): Sprint name

**Returns:** Sprint report data

### Backlog Management

#### `get_backlog(project, filters)`

Get project backlog.

**Parameters:**
- `project` (str): Project name
- `filters` (dict): Optional filters

**Returns:** List of backlog items

#### `estimate_backlog_item(task_name, story_points, estimation_method)`

Estimate story points for backlog item.

**Parameters:**
- `task_name` (str): Task name
- `story_points` (int): Story points
- `estimation_method` (str): Estimation method

**Returns:** Success status

### Board Management

#### `get_board_data(project, sprint, view_type)`

Get board data for visualization.

**Parameters:**
- `project` (str): Project name
- `sprint` (str): Sprint name (optional)
- `view_type` (str): 'sprint' or 'backlog'

**Returns:** Board data structure

#### `move_issue(task_name, from_status, to_status, position)`

Move issue on board.

**Parameters:**
- `task_name` (str): Task name
- `from_status` (str): Current status
- `to_status` (str): Target status
- `position` (int): Position in column

**Returns:** Success status

### Time Tracking

#### `log_work(task_name, time_spent, work_description, work_date)`

Log work on an issue.

**Parameters:**
- `task_name` (str): Task name
- `time_spent` (str): Time spent (e.g., "2h 30m")
- `work_description` (str): Work description
- `work_date` (str): Work date (optional)

**Returns:** Log result

#### `start_timer(task_name)`

Start work timer.

**Parameters:**
- `task_name` (str): Task name

**Returns:** Timer details

#### `stop_timer(timer_name, work_description)`

Stop work timer.

**Parameters:**
- `timer_name` (str): Timer name
- `work_description` (str): Work description

**Returns:** Time logged

### GitHub Integration

#### `sync_agile_issue_to_github(task_name)`

Sync agile issue to GitHub.

**Parameters:**
- `task_name` (str): Task name

**Returns:** GitHub issue details

#### `bulk_sync_project_issues(project_name)`

Bulk sync all GitHub issues for a project.

**Parameters:**
- `project_name` (str): Project name

**Returns:** Sync results

### Version Control

#### `create_issue_version(task_name, change_description)`

Create version snapshot.

**Parameters:**
- `task_name` (str): Task name
- `change_description` (str): Description of changes

**Returns:** Version document

#### `restore_issue_version(task_name, version_number)`

Restore issue to previous version.

**Parameters:**
- `task_name` (str): Task name
- `version_number` (int): Version number

**Returns:** Updated task document

#### `get_version_history(task_name)`

Get version history.

**Parameters:**
- `task_name` (str): Task name

**Returns:** List of versions

---

## Developer Guide

### Architecture Overview

The ERPNext Agile system is built using ERPNext's framework and follows these architectural patterns:

#### Core Components

1. **Manager Classes**: Business logic handlers
   - `AgileIssueManager`: Issue lifecycle management
   - `AgileSprintManager`: Sprint operations
   - `AgileBacklogManager`: Backlog management
   - `AgileBoardManager`: Board visualization
   - `AgileTimeTracking`: Time tracking
   - `AgileGitHubIntegration`: GitHub sync

2. **DocTypes**: Data models
   - Core entities (Sprint, Issue Status, etc.)
   - Activity tracking (Work Log, Activity, Timer)
   - Configuration (Workflow Scheme, Permission Scheme)

3. **API Layer**: `api.py` with whitelisted methods
4. **Frontend**: JavaScript enhancements for Task/Project forms
5. **Scheduled Tasks**: Automated metrics and cleanup

#### Data Flow

```
User Action → Frontend JS → API Endpoint → Manager Class → DocType → Database
                ↓
            Response ← Manager ← DocType ← Database
```

### Extending the System

#### Adding New Issue Types

1. Create new DocType:
   ```python
   # In erpnext_agile/erpnext_agile/doctype/agile_issue_type/agile_issue_type.py
   class AgileIssueType(Document):
       def validate(self):
           # Custom validation logic
           pass
   ```

2. Add to workflow schemes
3. Update board filtering options

#### Custom Workflows

1. Create workflow scheme:
   ```python
   workflow_scheme = frappe.get_doc({
       'doctype': 'Agile Workflow Scheme',
       'scheme_name': 'Custom Workflow',
       'project': 'My Project'
   })
   ```

2. Define statuses and transitions
3. Assign to projects

#### Custom Reports

Create new reports in `erpnext_agile/erpnext_agile/report/`:

```python
# sprint_velocity_report.py
import frappe

def execute(filters=None):
    columns = [
        {'fieldname': 'sprint', 'label': 'Sprint', 'fieldtype': 'Link'},
        {'fieldname': 'velocity', 'label': 'Velocity', 'fieldtype': 'Float'}
    ]
    
    data = frappe.db.sql("""
        SELECT name as sprint, velocity
        FROM `tabAgile Sprint`
        WHERE sprint_state = 'Completed'
        ORDER BY end_date DESC
    """, as_dict=True)
    
    return columns, data
```

#### Custom API Endpoints

Add to `api.py`:

```python
@frappe.whitelist()
def custom_endpoint(param1, param2):
    """Custom endpoint description"""
    # Implementation
    return {'result': 'success'}
```

### Testing

#### Unit Tests

Create test files in each DocType folder:

```python
# test_agile_sprint.py
import frappe
import unittest

class TestAgileSprint(unittest.TestCase):
    def setUp(self):
        self.sprint = frappe.get_doc({
            'doctype': 'Agile Sprint',
            'sprint_name': 'Test Sprint',
            'project': 'Test Project',
            'start_date': '2024-01-01',
            'end_date': '2024-01-14'
        })
    
    def test_sprint_creation(self):
        self.sprint.insert()
        self.assertTrue(self.sprint.name)
    
    def test_sprint_validation(self):
        # Test validation logic
        pass
```

#### Integration Tests

Test API endpoints:

```python
def test_create_issue_api():
    response = frappe.call('erpnext_agile.api.create_agile_issue', {
        'issue_data': {
            'project': 'Test Project',
            'summary': 'Test Issue',
            'issue_type': 'Story'
        }
    })
    assert response.get('issue_key')
```

### Performance Optimization

#### Database Indexing

Add indexes for frequently queried fields:

```python
# In DocType JSON
"indexes": [
    {"fields": ["project", "is_agile"]},
    {"fields": ["current_sprint", "issue_status"]}
]
```

#### Caching

Use ERPNext's caching for expensive operations:

```python
@frappe.whitelist()
def get_cached_data():
    cache_key = f"agile_data_{frappe.session.user}"
    cached = frappe.cache().get_value(cache_key)
    
    if not cached:
        cached = expensive_operation()
        frappe.cache().set_value(cache_key, cached, expires_in_sec=3600)
    
    return cached
```

#### Bulk Operations

For large datasets, use bulk operations:

```python
def bulk_update_issues(issues, updates):
    """Bulk update multiple issues"""
    for issue in issues:
        frappe.db.set_value('Task', issue, updates)
    
    frappe.db.commit()
```

### Security Considerations

#### Permission Checks

Always validate permissions:

```python
@frappe.whitelist()
def secure_endpoint(task_name):
    # Check if user can access this task
    if not frappe.has_permission('Task', 'read', task_name):
        frappe.throw("Permission denied")
    
    # Proceed with operation
    pass
```

#### Input Validation

Validate all inputs:

```python
def validate_issue_data(issue_data):
    required_fields = ['project', 'summary', 'issue_type']
    
    for field in required_fields:
        if not issue_data.get(field):
            frappe.throw(f"Field {field} is required")
    
    # Validate project exists and is agile-enabled
    if not frappe.db.get_value('Project', issue_data['project'], 'enable_agile'):
        frappe.throw("Project is not agile-enabled")
```

#### SQL Injection Prevention

Use parameterized queries:

```python
# Good
frappe.db.sql("""
    SELECT * FROM `tabTask` 
    WHERE project = %s AND is_agile = 1
""", (project,))

# Bad - vulnerable to SQL injection
frappe.db.sql(f"""
    SELECT * FROM `tabTask` 
    WHERE project = '{project}' AND is_agile = 1
""")
```

### Deployment

#### Production Deployment

1. **Backup Database**:
   ```bash
   bench --site your-site.com backup
   ```

2. **Update App**:
   ```bash
   bench update --pull
   bench --site your-site.com migrate
   bench restart
   ```

3. **Verify Installation**:
   ```bash
   bench --site your-site.com console
   # Test in console
   ```

#### Monitoring

Set up monitoring for:

- **Scheduled Tasks**: Ensure hourly/daily tasks run
- **API Performance**: Monitor response times
- **Database Performance**: Watch for slow queries
- **Error Rates**: Monitor failed operations

#### Scaling

For large teams:

1. **Database Optimization**:
   - Add appropriate indexes
   - Use read replicas for reports
   - Archive old data

2. **Caching**:
   - Cache frequently accessed data
   - Use Redis for session storage

3. **Background Jobs**:
   - Move heavy operations to background jobs
   - Use job queues for bulk operations

---

## Configuration

### Project Configuration

#### Agile Settings

In Project DocType, configure:

- **Enable Agile**: Turn on agile functionality
- **Project Key**: Used for issue keys (e.g., "PROJ" for PROJ-123)
- **Workflow Scheme**: Define status transitions
- **Permission Scheme**: Control access permissions
- **Burndown Enabled**: Enable burndown chart generation

#### GitHub Integration

- **GitHub Repository**: Repository in owner/repo format
- **Auto Create GitHub Issues**: Automatically create GitHub issues
- **Auto Create Branches**: Suggest branch names
- **Branch Naming Convention**: Template for branch names

### Workflow Configuration

#### Issue Statuses

Create custom statuses in **Agile Issue Status**:

```json
{
    "status_name": "In Review",
    "status_category": "In Progress",
    "color": "#ff9900",
    "sort_order": 3
}
```

#### Workflow Schemes

Define workflows in **Agile Workflow Scheme**:

1. Create scheme
2. Add statuses
3. Define transitions
4. Assign to projects

#### Permission Schemes

Control access in **Agile Permission Scheme**:

1. Create scheme
2. Define roles and permissions
3. Assign to projects

### Notification Configuration

#### Email Notifications

Configure in Project settings:

- **Enable Email Notifications**: Turn on email alerts
- **Notification Recipients**: Who gets notified
- **Notification Events**: What triggers notifications

#### Notification Templates

Customize email templates:

1. Go to **Email Template**
2. Create templates for:
   - Issue created
   - Issue assigned
   - Status changed
   - Sprint started/completed

### Time Tracking Configuration

#### Time Formats

Supported formats:
- "2h 30m" - Hours and minutes
- "1.5h" - Decimal hours
- "90m" - Minutes only
- "2h" - Hours only

#### Timer Settings

Configure work timers:

- **Auto-stop Timers**: Stop timers after inactivity
- **Timer Notifications**: Remind users of running timers
- **Time Rounding**: Round logged time to nearest interval

### Board Configuration

#### Column Settings

Customize board columns:

1. Go to Project → View Board
2. Click **Configure Board**
3. Set column properties:
   - Column name
   - WIP limits
   - Column color

#### Swimlane Options

Configure swimlanes:

- **By Assignee**: Show who's working on what
- **By Issue Type**: Separate Stories, Bugs, Tasks

### Reporting Configuration

#### Burndown Charts

Configure burndown generation:

- **Update Frequency**: How often to create data points
- **Ideal Line**: Show ideal burndown line
- **Scope Changes**: Track scope additions/removals

#### Velocity Tracking

Set up velocity calculations:

- **Sprint History**: How many sprints to include
- **Velocity Method**: Average or trend-based
- **Capacity Planning**: Factor in team capacity

---

## Troubleshooting

### Common Issues

#### Issue Keys Not Generated

**Problem**: New issues don't get issue keys like PROJ-123

**Solution**:
1. Check Project has **Project Key** set
2. Verify **Enable Agile** is checked
3. Ensure **Is Agile** is checked on Task

#### Sprint Not Starting

**Problem**: Can't start a sprint

**Solution**:
1. Check sprint state is "Future"
2. Verify no other active sprints in project
3. Ensure sprint dates are valid
4. Check user has permission to start sprints

#### Board Not Loading

**Problem**: Board view shows empty or errors

**Solution**:
1. Check project has workflow scheme configured
2. Verify issue statuses exist
3. Clear browser cache
4. Check JavaScript console for errors

#### Time Tracking Not Working

**Problem**: Can't log work or start timers

**Solution**:
1. Verify task is agile-enabled
2. Check time format is correct
3. Ensure user has permission to log work
4. Check for JavaScript errors

#### GitHub Sync Failing

**Problem**: GitHub integration not working

**Solution**:
1. Verify GitHub Integration app is installed
2. Check repository format (owner/repo)
3. Ensure GitHub API tokens are configured
4. Check user has GitHub username set

### Performance Issues

#### Slow Board Loading

**Solutions**:
1. Add database indexes:
   ```sql
   ALTER TABLE `tabTask` ADD INDEX `project_agile_idx` (`project`, `is_agile`);
   ALTER TABLE `tabTask` ADD INDEX `sprint_status_idx` (`current_sprint`, `issue_status`);
   ```

2. Reduce board data:
   - Filter by assignee
   - Limit to current sprint only
   - Use pagination for large datasets

#### Slow Reports

**Solutions**:
1. Add indexes for report queries
2. Use caching for expensive calculations
3. Run reports as background jobs
4. Archive old data

#### Memory Issues

**Solutions**:
1. Increase server memory
2. Optimize database queries
3. Use pagination for large datasets
4. Clear caches regularly

### Database Issues

#### Missing DocTypes

**Problem**: DocTypes not created after installation

**Solution**:
```bash
# Reinstall the app
bench --site your-site.com uninstall-app erpnext_agile
bench --site your-site.com install-app erpnext_agile
bench --site your-site.com migrate
```

#### Data Corruption

**Problem**: Data inconsistencies or corruption

**Solution**:
1. Restore from backup
2. Run data validation scripts
3. Check for orphaned records
4. Rebuild indexes

### Integration Issues

#### GitHub API Limits

**Problem**: GitHub API rate limiting

**Solution**:
1. Implement request throttling
2. Use webhooks instead of polling
3. Cache GitHub data
4. Use GitHub App instead of personal tokens

#### Email Notifications Not Sending

**Solution**:
1. Check email settings in ERPNext
2. Verify SMTP configuration
3. Check spam folders
4. Test with simple email first

### Debugging

#### Enable Debug Mode

```python
# In hooks.py or console
frappe.conf.developer_mode = 1
frappe.conf.logging = 2
```

#### Check Logs

```bash
# View application logs
tail -f logs/bench.log

# View error logs
tail -f logs/error.log

# View worker logs
tail -f logs/worker.log
```

#### Database Queries

```python
# In console
frappe.db.sql("""
    SELECT COUNT(*) as total_issues
    FROM `tabTask` 
    WHERE is_agile = 1
""")

# Check for issues without issue keys
frappe.db.sql("""
    SELECT name, subject 
    FROM `tabTask` 
    WHERE is_agile = 1 AND (issue_key IS NULL OR issue_key = '')
""")
```

#### JavaScript Debugging

1. Open browser developer tools
2. Check Console tab for errors
3. Use Network tab to see API calls
4. Add console.log() statements in JavaScript files

### Getting Help

#### Documentation

- Check this documentation first
- Review ERPNext documentation
- Look at GitHub issues and discussions

#### Community Support

- ERPNext Community Forum
- GitHub Issues
- Stack Overflow (tag: erpnext)

#### Professional Support

For enterprise support:
- Contact the development team
- Hire ERPNext consultants
- Consider paid support plans

---

## Contributing

### Development Setup

#### Prerequisites

- ERPNext development environment
- Git
- Python 3.10+
- Node.js and npm

#### Setup Steps

1. **Fork the Repository**:
   ```bash
   git clone https://github.com/your-username/erpnext_agile.git
   cd erpnext_agile
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. **Run Tests**:
   ```bash
   bench run-tests --app erpnext_agile
   ```

### Contribution Guidelines

#### Code Style

Follow ERPNext coding standards:

- **Python**: Use Black formatter, follow PEP 8
- **JavaScript**: Use ESLint, follow Airbnb style guide
- **SQL**: Use parameterized queries, avoid raw SQL
- **Documentation**: Use clear, concise language

#### Commit Messages

Use conventional commit format:

```
feat: add new sprint burndown chart
fix: resolve issue key generation bug
docs: update installation guide
test: add unit tests for time tracking
```

#### Pull Request Process

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Test Changes**:
   ```bash
   bench run-tests --app erpnext_agile
   bench --site test-site.com migrate
   ```

4. **Submit Pull Request**:
   - Clear description
   - Link to related issues
   - Include screenshots if UI changes

#### Testing Requirements

All contributions must include tests:

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test API endpoints
- **UI Tests**: Test frontend functionality

#### Documentation Updates

Update documentation for:

- New features
- API changes
- Configuration options
- Breaking changes

### Areas for Contribution

#### High Priority

- **Performance Optimization**: Database queries, caching
- **UI/UX Improvements**: Board interface, mobile responsiveness
- **Additional Integrations**: GitLab, Azure DevOps, Jira
- **Advanced Reporting**: Custom dashboards, analytics

#### Medium Priority

- **Workflow Customization**: More workflow options
- **Notification System**: More notification types
- **Time Tracking**: Advanced time tracking features
- **Mobile App**: Native mobile application

#### Low Priority

- **Themes**: Custom board themes
- **Plugins**: Extension system
- **Import/Export**: Data migration tools
- **API Extensions**: More API endpoints

### Code Review Process

#### Review Criteria

- **Functionality**: Does it work as intended?
- **Code Quality**: Is the code clean and maintainable?
- **Performance**: Are there performance implications?
- **Security**: Are there security concerns?
- **Testing**: Are there adequate tests?
- **Documentation**: Is documentation updated?

#### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests
2. **Peer Review**: At least one team member reviews
3. **Testing**: Reviewer tests the changes
4. **Approval**: Changes approved and merged

### Release Process

#### Version Management

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Changelog**: Document all changes
- **Release Notes**: User-friendly change summary

#### Release Steps

1. **Prepare Release**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Update Version**:
   ```bash
   # Update version in __init__.py
   # Update changelog
   # Update release notes
   ```

3. **Create Release**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **Publish**:
   - Create GitHub release
   - Update documentation
   - Announce to community

### Community Guidelines

#### Code of Conduct

- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow the project's coding standards

#### Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Chat**: Join ERPNext community chat
- **Email**: Use email for sensitive matters

#### Recognition

Contributors will be recognized in:

- **Contributors List**: GitHub contributors page
- **Release Notes**: Mentioned in release notes
- **Documentation**: Listed in contributors section
- **Community**: Highlighted in community posts

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:

- **Documentation**: This file and inline code documentation
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Community**: ERPNext Community Forum
- **Email**: tamocha44@gmail.com

## Acknowledgments

- ERPNext team for the excellent framework
- Jira for inspiration on agile workflows
- All contributors who have helped improve this project
- The open-source community for tools and libraries

---

*Last updated: January 2024*
*Version: 1.0.0*



## Required File Structure

```
erpnext_agile/
├── erpnext_agile/
│   ├── __init__.py
│   ├── hooks.py
│   ├── patches/
│   │   └── after_install.py
│   ├── erpnext_agile/
│   │   └── doctype/
│   │       ├── agile_sprint/
│   │       │   ├── __init__.py
│   │       │   ├── agile_sprint.json
│   │       │   ├── agile_sprint.py
│   │       │   └── test_agile_sprint.py
│   │       ├── agile_issue_status/
│   │       ├── agile_issue_priority/
│   │       ├── agile_issue_type/
│   │       ├── agile_issue_activity/
│   │       │   ├── __init__.py
│   │       │   ├── agile_issue_activity.json
│   │       │   ├── agile_issue_activity.py
│   │       │   └── test_agile_issue_activity.py
│   │       ├── agile_work_timer/
│   │       │   ├── __init__.py
│   │       │   ├── agile_work_timer.json
│   │       │   ├── agile_work_timer.py
│   │       │   └── test_agile_work_timer.py
│   │       ├── agile_sprint_burndown/
│   │       │   ├── __init__.py
│   │       │   ├── agile_sprint_burndown.json
│   │       │   ├── agile_sprint_burndown.py
│   │       │   └── test_agile_sprint_burndown.py
│   │       ├── agile_issue_work_log/
│   │       │   ├── __init__.py
│   │       │   ├── agile_issue_work_log.json
│   │       │   └── agile_issue_work_log.py
│   │       ├── agile_issue_version/
│   │       │   ├── __init__.py
│   │       │   ├── agile_issue_version.json
│   │       │   ├── agile_issue_version.py
│   │       │   └── test_agile_issue_version.py
│   │       ├── agile_workflow_scheme/
│   │       ├── agile_permission_scheme/
│   │       └── ...
│   ├── agile_issue_manager.py
│   ├── agile_sprint_manager.py
│   ├── agile_backlog_manager.py
│   ├── agile_board_manager.py
│   ├── agile_time_tracking.py
│   ├── agile_github_integration.py
│   ├── agile_doctype_controllers.py
│   ├── version_control.py
│   ├── utils.py
│   ├── api.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── hourly.py
│   │   └── daily.py
│   └── public/
│       ├── js/
│       │   ├── task_agile.js
│       │   ├── project_agile.js
│       │   └── agile_utils.js
│       └── css/
│           └── erpnext_agile.css
├── setup.py
├── requirements.txt
└── README.md
```