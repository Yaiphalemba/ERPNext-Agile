# Agile Issue Version Control - Complete Guide

## Overview

The Version Control feature provides comprehensive change tracking and rollback capabilities for agile issues, similar to Git for code. Every significant change to an issue is automatically captured, allowing you to:

- View complete history of changes
- Compare different versions
- Restore to any previous version
- Track who made what changes and when
- Audit trail for compliance

## Features

### 1. Automatic Version Creation

Versions are automatically created when these fields change:
- Subject
- Description
- Issue Type
- Issue Priority
- Issue Status
- Story Points
- Sprint

### 2. Manual Version Creation

Create snapshots manually for important milestones:
```python
from erpnext_agile.version_control import IssueVersionControl

vc = IssueVersionControl('TASK-PROJ-123')
version = vc.create_version('Before major refactor')
```

### 3. Version Restoration

Restore an issue to any previous state:
```python
vc = IssueVersionControl('TASK-PROJ-123')
vc.restore_version(5)  # Restore to version 5
```

### 4. Version Comparison

Compare any two versions or compare with current state:
```python
# Compare two versions
diff = vc.get_version_diff('version1', 'version2')

# Compare version with current
diff = vc.compare_with_current(3)
```

## API Reference

### Core Methods

#### `create_version(change_description)`
Creates a new version snapshot.

**Parameters:**
- `change_description` (str, optional): Description of changes

**Returns:** Version document

**Example:**
```python
version = vc.create_version('Added acceptance criteria')
print(f"Created version {version.version_number}")
```

#### `get_version_history()`
Get list of all versions for the issue.

**Returns:** List of version records

**Example:**
```python
history = vc.get_version_history()
for v in history:
    print(f"v{v['version_number']} by {v['created_by']} at {v['created_at']}")
```

#### `restore_version(version_number)`
Restore issue to a specific version.

**Parameters:**
- `version_number` (int): Version to restore

**Returns:** Updated task document

**Example:**
```python
task = vc.restore_version(3)
print(f"Restored to version 3: {task.subject}")
```

#### `get_version_diff(version1, version2)`
Compare two versions.

**Parameters:**
- `version1` (str): First version name
- `version2` (str): Second version name

**Returns:** Dictionary of differences

**Example:**
```python
diff = vc.get_version_diff('TASK-001-v1', 'TASK-001-v2')
for field, changes in diff.items():
    print(f"{field}: {changes['old']} → {changes['new']}")
```

#### `compare_with_current(version_number)`
Compare a version with current state.

**Parameters:**
- `version_number` (int): Version to compare

**Returns:** List of differences

**Example:**
```python
diff = vc.compare_with_current(3)
for change in diff:
    print(f"{change['field']}: {change['change_type']}")
```

#### `get_version_details(version_number)`
Get detailed information about a version.

**Parameters:**
- `version_number` (int): Version number

**Returns:** Version details dictionary

**Example:**
```python
details = vc.get_version_details(5)
print(f"Version {details['version_number']} data: {details['data']}")
```

#### `delete_version(version_number)`
Delete a specific version (use with caution).

**Parameters:**
- `version_number` (int): Version to delete

**Returns:** Boolean success status

#### `cleanup_old_versions(keep_latest)`
Clean up old versions, keeping only recent ones.

**Parameters:**
- `keep_latest` (int, default=10): Number of versions to keep

**Returns:** Number of versions deleted

**Example:**
```python
deleted = vc.cleanup_old_versions(keep_latest=5)
print(f"Deleted {deleted} old versions")
```

### Whitelisted API Endpoints

All methods are accessible via Frappe's RPC API:

#### `erpnext_agile.version_control.create_issue_version`
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.create_issue_version',
    args: {
        task_name: 'TASK-001',
        change_description: 'Milestone reached'
    },
    callback: function(r) {
        console.log('Version created:', r.message);
    }
});
```

#### `erpnext_agile.version_control.get_version_history`
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.get_version_history',
    args: { task_name: 'TASK-001' },
    callback: function(r) {
        console.log('History:', r.message);
    }
});
```

#### `erpnext_agile.version_control.restore_issue_version`
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

#### `erpnext_agile.version_control.compare_with_current`
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.compare_with_current',
    args: {
        task_name: 'TASK-001',
        version_number: 5
    },
    callback: function(r) {
        let diff = r.message;
        // Display differences
    }
});
```

#### `erpnext_agile.version_control.get_version_statistics`
```javascript
frappe.call({
    method: 'erpnext_agile.version_control.get_version_statistics',
    args: { task_name: 'TASK-001' },
    callback: function(r) {
        let stats = r.message;
        console.log(`Total versions: ${stats.total_versions}`);
        console.log(`Contributors: ${stats.unique_contributors}`);
    }
});
```

## Usage Scenarios

### Scenario 1: Before Major Changes

```python
# Before making major changes, create a snapshot
vc = IssueVersionControl('TASK-PROJ-123')
vc.create_version('Before requirements change')

# Make changes
task = frappe.get_doc('Task', 'TASK-PROJ-123')
task.description = 'New requirements...'
task.story_points = 13
task.save()

# If changes are wrong, restore
vc.restore_version(previous_version_number)
```

### Scenario 2: Audit Trail

```python
# View complete history
history = vc.get_version_history()

for version in history:
    print(f"""
    Version {version['version_number']}
    Changed by: {version['created_by']}
    When: {version['created_at']}
    What: {version['change_description']}
    """)
```

### Scenario 3: Compare Changes

```python
# See what changed between two versions
diff = vc.compare_with_current(5)

for change in diff:
    if change['change_type'] == 'modified':
        print(f"{change['field']} changed:")
        print(f"  Old: {change['old_value']}")
        print(f"  New: {change['new_value']}")
```

### Scenario 4: Bulk Version Creation

```python
# Create versions for multiple issues
from erpnext_agile.version_control import batch_create_versions

issues = ['TASK-001', 'TASK-002', 'TASK-003']
results = batch_create_versions(issues, 'Sprint planning complete')

print(f"Success: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")
```

### Scenario 5: Export Version History

```python
# Export as JSON
json_export = export_version_history('TASK-001', format='json')

# Export as CSV
csv_export = export_version_history('TASK-001', format='csv')
```