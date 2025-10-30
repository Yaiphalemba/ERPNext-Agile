# Workflow Condition Examples

## 📋 Common Workflow Conditions

### 1. **Issue Type Based Transitions**

```python
# Only Epics can go directly to "Released"
doc.issue_type == "Epic"

# Stories and Bugs can be marked as "Ready for QA"
doc.issue_type in ["Story", "Bug"]

# Only Tasks (not Epics) can be "In Progress"
doc.issue_type != "Epic"
```

### 2. **Story Points Based Transitions**

```python
# Only high-effort items (5+ points) need "Tech Review"
doc.story_points and doc.story_points >= 5

# Small items (< 3 points) can skip review
doc.story_points and doc.story_points < 3

# Items with no story points need estimation before "In Progress"
not doc.story_points or doc.story_points == 0
```

### 3. **Assignment Based Transitions**

```python
# Must be assigned before moving to "In Progress"
len(doc.assigned_to_users) > 0

# Must have at least 2 assignees for pair programming
len(doc.assigned_to_users) >= 2

# Must be unassigned to go to "Backlog"
len(doc.assigned_to_users) == 0
```

### 4. **Priority Based Transitions**

```python
# Critical issues can skip "In Progress" and go to "Urgent"
doc.issue_priority == "Critical"

# Only low priority can go to "Deferred"
doc.issue_priority == "Low"

# High/Critical must go through "Code Review"
doc.issue_priority in ["High", "Critical"]
```

### 5. **Sprint Based Transitions**

```python
# Must be in a sprint to move to "In Progress"
doc.current_sprint

# Can only close if sprint is completed
not doc.current_sprint or exists("Agile Sprint", doc.current_sprint, {"sprint_state": "Completed"})

# Only items not in sprint can go to "Backlog"
not doc.current_sprint
```

### 6. **Sub-tasks / Parent Issue Based**

```python
# Only issues without parent can be "Released"
not doc.parent_issue

# Child tasks must wait for parent
not doc.parent_issue or get_value("Task", doc.parent_issue, "issue_status") == "Done"

# Epics with children can't be closed until all children are done
doc.issue_type != "Epic" or not exists("Task", {"parent_issue": doc.name, "issue_status": ["!=", "Done"]})
```

### 7. **Time Based Transitions**

```python
# Can only close if created more than 1 day ago
(today() - doc.creation.date()).days > 1

# Urgent issues must be less than 3 days old
doc.issue_priority == "Critical" and (today() - doc.creation.date()).days < 3
```

### 8. **Linked Items Based**

```python
# Must have test cases linked before "Ready for QA"
exists("Test Case Link", {"link_doctype": "Task", "link_name": doc.name})

# Must have PR linked before "Code Review"
doc.github_pr_number and doc.github_pr_number > 0

# All linked test cases must pass
not exists("Test Execution", {
    "test_case": ["in", [tc.test_case for tc in frappe.get_all("Test Case Link", 
        filters={"link_doctype": "Task", "link_name": doc.name}, pluck="parent")]],
    "status": ["!=", "Pass"]
})
```

### 9. **Project Based Transitions**

```python
# Only certain projects allow "Production Deploy"
doc.project in ["PROD-Project", "Client-Facing"]

# Internal projects skip "Client Review"
doc.project not in ["Client-Project-A", "Client-Project-B"]
```

### 10. **Combined Conditions**

```python
# Complex: Ready for production
(
    doc.issue_type == "Story" and 
    doc.story_points and doc.story_points < 8 and
    len(doc.assigned_to_users) > 0 and
    doc.current_sprint and
    exists("Test Case Link", {"link_doctype": "Task", "link_name": doc.name})
)

# Must meet all criteria for deployment
(
    doc.issue_status == "Code Review" and
    doc.github_pr_number and
    not exists("Test Execution", {"status": "Fail"}) and
    doc.issue_priority != "Critical"
)
```

---

## 🎯 Real-World Workflow Examples

### Example 1: **Scrum Workflow with Conditional Logic**

| From Status | To Status | Transition Name | Condition | Required Permission |
|-------------|-----------|-----------------|-----------|---------------------|
| Backlog | Ready for Dev | Mark Ready | `doc.story_points and doc.story_points > 0` | Project Manager |
| Ready for Dev | In Progress | Start Work | `len(doc.assigned_to_users) > 0` | Developer |
| In Progress | Code Review | Submit for Review | `doc.github_pr_number and doc.github_pr_number > 0` | Developer |
| Code Review | Ready for QA | Approve | `True` | Project Manager |
| Ready for QA | In QA | Start Testing | `exists("Test Case Link", {"link_doctype": "Task", "link_name": doc.name})` | Tester |
| In QA | Done | Mark Complete | `True` | Tester |
| In QA | In Progress | Reopen | `True` | Tester |

### Example 2: **Bug Workflow with Severity-Based Rules**

| From Status | To Status | Transition Name | Condition | Required Permission |
|-------------|-----------|-----------------|-----------|---------------------|
| Open | In Progress | Start Fix | `len(doc.assigned_to_users) > 0` | Developer |
| Open | Deferred | Defer | `doc.issue_priority == "Low"` | Project Manager |
| In Progress | Code Review | Submit Fix | `doc.github_pr_number > 0` | Developer |
| Code Review | In QA | Approve Fix | `True` | Project Manager |
| Code Review | In Progress | Request Changes | `True` | Project Manager |
| In QA | Resolved | Verify Fix | `True` | Tester |
| In QA | Reopened | Reopen Bug | `True` | Tester |
| Resolved | Closed | Close | `(today() - doc.modified.date()).days > 1` | Project Manager |

### Example 3: **Epic Workflow with Child Task Validation**

| From Status | To Status | Transition Name | Condition | Required Permission |
|-------------|-----------|-----------------|-----------|---------------------|
| Backlog | Planning | Start Planning | `doc.issue_type == "Epic"` | Project Manager |
| Planning | In Progress | Start Epic | `exists("Task", {"parent_issue": doc.name})` | Project Manager |
| In Progress | Review | Ready for Review | `not exists("Task", {"parent_issue": doc.name, "issue_status": ["not in", ["Done", "Closed"]]})` | Project Manager |
| Review | Done | Complete | `True` | Project Manager |

---

## 🛠️ Setup Instructions

### 1. Create Workflow Scheme

```python
# Via Data Import or Script
workflow_scheme = frappe.get_doc({
    "doctype": "Agile Workflow Scheme",
    "scheme_name": "Standard Scrum Workflow",
    "description": "Standard workflow for Scrum projects with conditional transitions"
})

# Add transitions
workflow_scheme.append("transitions", {
    "from_status": "Backlog",
    "to_status": "Ready for Dev",
    "transition_name": "Mark Ready",
    "condition": "doc.story_points and doc.story_points > 0",
    "required_permission": "Project Manager"
})

workflow_scheme.insert()
```

### 2. Assign to Project

```python
project = frappe.get_doc("Project", "My Project")
project.workflow_scheme = "Standard Scrum Workflow"
project.save()
```

### 3. Test Workflow

Use the **"Test Workflow"** button in the Workflow Scheme form to validate transitions against actual tasks.

---

## 🎨 UI Features

### Task Form:
- **Workflow Menu**: Shows only allowed transitions
- **Status Dropdown**: Filtered to show only reachable statuses
- **Transition Dialog**: Allows adding comments during transition
- **Workflow Indicator**: Shows how many statuses are available

### Workflow Scheme Form:
- **Test Workflow**: Select a task and see available transitions
- **Visualize Workflow**: See a diagram of all transitions
- **Condition Helper**: Shows available variables when editing conditions

---

## 🔒 Security Notes

1. **Condition Evaluation**: 
   - Runs in restricted Python environment
   - No file system access
   - No network access
   - Safe for user-defined conditions

2. **Permission Checks**:
   - Conditions evaluate first
   - Then permission checks
   - Both must pass for transition

3. **Error Handling**:
   - Invalid conditions are caught during save
   - Runtime errors deny transition (safe default)
   - All errors logged for debugging

---

## 📝 Best Practices

1. **Keep Conditions Simple**: Easy to understand and maintain
2. **Use Meaningful Transition Names**: "Mark Ready" not "Transition 1"
3. **Document Complex Logic**: Add notes in scheme description
4. **Test Thoroughly**: Use "Test Workflow" button before deploying
5. **Start Simple**: Add complexity gradually
6. **Consider Performance**: Avoid expensive database queries in conditions
7. **Handle Edge Cases**: Check for None/empty values

---

## 🚀 Advanced Tips

### Custom Functions in Conditions

You can create helper functions in your hooks.py:

```python
# In hooks.py
def check_all_tests_passed(doc):
    """Check if all linked tests passed"""
    test_links = frappe.get_all("Test Case Link", 
        filters={"link_doctype": "Task", "link_name": doc.name},
        pluck="parent"
    )
    
    if not test_links:
        return False
    
    failed = frappe.db.count("Test Execution", {
        "test_case": ["in", test_links],
        "status": "Fail"
    })
    
    return failed == 0

# In condition:
# check_all_tests_passed(doc)
```

This gives you maximum flexibility! 🎉