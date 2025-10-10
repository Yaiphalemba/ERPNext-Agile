# ERPNext Agile - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Issue Management](#issue-management)
3. [Sprint Management](#sprint-management)
4. [Backlog Management](#backlog-management)
5. [Board Usage](#board-usage)
6. [Time Tracking](#time-tracking)
7. [GitHub Integration](#github-integration)
8. [Reports and Analytics](#reports-and-analytics)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### What is ERPNext Agile?

ERPNext Agile is a comprehensive project management system that brings Jira-like functionality to ERPNext. It provides:

- **Issue Tracking**: Create, manage, and track issues with unique keys
- **Sprint Management**: Plan and execute development sprints
- **Backlog Organization**: Manage product backlog with prioritization
- **Visual Boards**: Kanban-style boards for workflow visualization
- **Time Tracking**: Log work time and track estimates
- **GitHub Integration**: Sync issues with GitHub repositories
- **Reporting**: Comprehensive analytics and metrics

### Key Concepts

#### Issues
Issues are the fundamental unit of work in agile. They can be:
- **Stories**: User-facing features
- **Tasks**: Technical work
- **Bugs**: Defects to fix
- **Epics**: Large features spanning multiple sprints
- **Spikes**: Research or investigation work

#### Sprints
Sprints are time-boxed iterations (typically 1-4 weeks) where teams work on a set of issues to deliver value.

#### Backlog
The product backlog contains all issues not currently in a sprint, prioritized by business value.

#### Board
The board provides a visual representation of your workflow, showing issues moving through different statuses.

### Your First Steps

1. **Enable Agile for Your Project**:
   - Go to Project list
   - Open your project
   - Check "Enable Agile"
   - Set a Project Key (e.g., "PROJ")

2. **Create Your First Issue**:
   - Go to Task list
   - Create a new task
   - Check "Is Agile"
   - Fill in agile fields

3. **View the Board**:
   - Go to your project
   - Click "View Board"
   - See your issues organized by status

---

## Issue Management

### Creating Issues

#### From Task Form

1. **Navigate to Tasks**:
   ```
   ERPNext → Projects → Task → New
   ```

2. **Fill Basic Information**:
   - **Subject**: Clear, descriptive title
   - **Description**: Detailed description of the work
   - **Project**: Select your agile project

3. **Enable Agile**:
   - Check **Is Agile** checkbox
   - This reveals agile-specific fields

4. **Set Agile Fields**:
   - **Issue Type**: Story, Task, Bug, Epic, or Spike
   - **Issue Priority**: Critical, High, Medium, or Low
   - **Story Points**: Effort estimate (optional)
   - **Sprint**: Assign to current sprint (optional)

5. **Add Details**:
   - **Original Estimate**: Time estimate (e.g., "8h")
   - **Components**: System components affected
   - **Fix Versions**: Target release versions
   - **Watchers**: Users to notify of changes

6. **Save**:
   - Issue key is automatically generated (e.g., PROJ-123)
   - Issue appears in agile views

#### From Board (Quick Create)

1. **Open Board**:
   - Go to Project → View Board

2. **Quick Create**:
   - Click **Quick Create** button in any column
   - Fill in issue details inline
   - Issue is created and added to the column

#### From Backlog

1. **Open Backlog**:
   - Go to Project → View Backlog

2. **Create Issue**:
   - Click **New Issue** button
   - Fill in details
   - Issue is added to backlog

### Issue Types

#### Story
- **Purpose**: User-facing features or functionality
- **Format**: "As a [user], I want [feature] so that [benefit]"
- **Example**: "As a customer, I want to reset my password so that I can regain access to my account"

#### Task
- **Purpose**: Technical work, maintenance, or non-user-facing features
- **Example**: "Refactor authentication module for better performance"

#### Bug
- **Purpose**: Defects or issues that need to be fixed
- **Example**: "Login fails when using special characters in password"

#### Epic
- **Purpose**: Large features that span multiple sprints
- **Example**: "User Authentication System" (contains multiple stories)

#### Spike
- **Purpose**: Research, investigation, or proof-of-concept work
- **Example**: "Research OAuth2 implementation options"

### Issue Priorities

#### Critical
- System is down or unusable
- Security vulnerabilities
- Data loss or corruption
- **Response Time**: Immediate

#### High
- Major features for current release
- Important bugs affecting users
- Performance issues
- **Response Time**: Within sprint

#### Medium
- Standard features and improvements
- Minor bugs
- Technical debt
- **Response Time**: Next sprint

#### Low
- Nice-to-have features
- Minor improvements
- Documentation updates
- **Response Time**: Future releases

### Issue Statuses

#### To Do Category
- **Open**: Not started
- **Backlog**: In product backlog
- **Selected for Development**: Ready for sprint

#### In Progress Category
- **In Progress**: Currently being worked on
- **In Review**: Under code review
- **Testing**: Being tested
- **Blocked**: Cannot proceed due to dependencies

#### Done Category
- **Done**: Completed and verified
- **Closed**: Issue is resolved
- **Cancelled**: No longer needed

### Managing Issues

#### Updating Issues

1. **Open the Issue**:
   - Click on issue key or title
   - Issue form opens

2. **Make Changes**:
   - Update any field
   - Add comments
   - Change status

3. **Save Changes**:
   - Changes are automatically tracked
   - Watchers are notified

#### Assigning Issues

1. **Single Assignment**:
   - Use **Assigned To** field
   - Select team member

2. **Multiple Assignment**:
   - Use **Assigned To Users** table
   - Add multiple team members
   - Each gets notifications

#### Adding Watchers

1. **Add Watchers**:
   - Use **Watchers** table
   - Add users who need updates
   - They receive email notifications

2. **Automatic Watchers**:
   - Reporter is automatically added
   - Assignees are automatically added

#### Linking Issues

1. **Parent-Child Relationships**:
   - Set **Parent Issue** field
   - Creates hierarchical structure
   - Useful for breaking down large work

### Issue Lifecycle

#### Typical Flow

1. **Creation**: Issue created in backlog
2. **Refinement**: Details added, estimated
3. **Sprint Planning**: Added to sprint
4. **Development**: Work begins, status changes
5. **Review**: Code review and testing
6. **Done**: Completed and verified

#### Status Transitions

- **Open** → **In Progress**: Work starts
- **In Progress** → **In Review**: Code ready for review
- **In Review** → **Testing**: Code approved, ready for testing
- **Testing** → **Done**: Testing passed
- **Any Status** → **Blocked**: Cannot proceed

---

## Sprint Management

### Creating Sprints

#### Basic Sprint Creation

1. **Navigate to Sprints**:
   ```
   ERPNext → Erpnext Agile → Agile Sprint → New
   ```

2. **Fill Sprint Details**:
   - **Sprint Name**: Descriptive name (e.g., "Sprint 1")
   - **Project**: Select your project
   - **Start Date**: Sprint start date
   - **End Date**: Sprint end date
   - **Sprint Goal**: What you want to achieve

3. **Save Sprint**:
   - Sprint is created in "Future" state
   - Ready for planning

#### Sprint Planning

1. **Add Issues to Sprint**:
   - Go to Project → View Backlog
   - Select issues to add
   - Use **Add to Sprint** action
   - Or drag issues to sprint in board view

2. **Consider Capacity**:
   - Review team velocity from previous sprints
   - Account for holidays and time off
   - Leave buffer for unexpected work

3. **Set Sprint Goal**:
   - Define what success looks like
   - Communicate to stakeholders
   - Use for decision making during sprint

### Sprint States

#### Future
- Sprint is created but not started
- Issues can be added or removed
- Planning can be adjusted

#### Active
- Sprint is currently running
- Issues are being worked on
- Burndown charts are updated
- Scope changes should be minimal

#### Completed
- Sprint has ended
- Final metrics are calculated
- Incomplete issues are moved to backlog
- Sprint retrospective can be conducted

### Starting Sprints

#### Start Process

1. **Open Sprint**:
   - Go to Agile Sprint list
   - Open the sprint to start

2. **Start Sprint**:
   - Click **Start Sprint** button
   - Confirm start date
   - Sprint state changes to "Active"

3. **Automatic Actions**:
   - Any other active sprints in project are completed
   - Burndown chart baseline is created
   - Team notifications are sent

#### Sprint Kickoff

1. **Sprint Planning Meeting**:
   - Review sprint goal
   - Confirm issue assignments
   - Identify dependencies
   - Set expectations

2. **Daily Standups**:
   - What did you do yesterday?
   - What will you do today?
   - Are there any blockers?

### Managing Active Sprints

#### Daily Management

1. **Monitor Progress**:
   - Check burndown charts
   - Review board status
   - Identify blockers early

2. **Scope Management**:
   - Avoid adding new work
   - Remove work if needed
   - Communicate changes to team

3. **Issue Management**:
   - Move issues through workflow
   - Update estimates as needed
   - Log work time

#### Handling Blockers

1. **Identify Blockers**:
   - Issues stuck in same status
   - Dependencies not resolved
   - External factors

2. **Resolve Blockers**:
   - Escalate to management
   - Find alternative approaches
   - Adjust sprint scope

3. **Update Status**:
   - Mark issues as "Blocked"
   - Add blocker description
   - Notify stakeholders

### Completing Sprints

#### Completion Process

1. **Sprint Review**:
   - Demo completed work
   - Gather stakeholder feedback
   - Celebrate achievements

2. **Complete Sprint**:
   - Click **Complete Sprint** button
   - Confirm completion
   - Sprint state changes to "Completed"

3. **Automatic Actions**:
   - Incomplete issues moved to backlog
   - Final metrics calculated
   - Burndown chart finalized

#### Sprint Retrospective

1. **What Went Well**:
   - Identify successes
   - Recognize team efforts
   - Document best practices

2. **What Could Improve**:
   - Identify challenges
   - Discuss solutions
   - Plan improvements

3. **Action Items**:
   - Assign improvement tasks
   - Set deadlines
   - Track progress

### Sprint Metrics

#### Velocity
- **Definition**: Story points completed per sprint
- **Calculation**: Sum of completed story points
- **Usage**: Predict future sprint capacity

#### Burndown
- **Definition**: Visual representation of work remaining
- **Ideal Line**: Straight line from total to zero
- **Actual Line**: Shows real progress

#### Scope Changes
- **Added Work**: Issues added during sprint
- **Removed Work**: Issues removed during sprint
- **Impact**: Affects burndown chart

---

## Backlog Management

### Understanding the Backlog

#### Product Backlog
The product backlog contains all issues not currently in a sprint:
- **Stories**: User-facing features
- **Tasks**: Technical work
- **Bugs**: Defects to fix
- **Epics**: Large features

#### Backlog Characteristics
- **Prioritized**: Ordered by business value
- **Estimated**: Story points assigned
- **Refined**: Ready for sprint planning
- **Dynamic**: Continuously updated

### Backlog Organization

#### Prioritization Methods

1. **Value-Effort Matrix**:
   - High value, low effort: Do first
   - High value, high effort: Plan carefully
   - Low value, low effort: Do later
   - Low value, high effort: Avoid

2. **Business Value**:
   - Revenue impact
   - User satisfaction
   - Strategic importance
   - Risk mitigation

3. **Dependencies**:
   - Technical dependencies
   - Business dependencies
   - Resource dependencies

### Backlog Refinement

#### Refinement Process

1. **Regular Sessions**:
   - Weekly refinement meetings
   - 1-2 hours duration
   - Include product owner and team

2. **Refinement Activities**:
   - Break down large stories
   - Add acceptance criteria
   - Estimate story points
   - Prioritize items

3. **Definition of Ready**:
   - Clear acceptance criteria
   - Estimated story points
   - Dependencies identified
   - Ready for sprint planning

#### Story Splitting

1. **When to Split**:
   - Stories too large for one sprint
   - Multiple user types involved
   - Different technical components
   - Sequential dependencies

2. **Splitting Techniques**:
   - **By User Type**: Different user personas
   - **By Workflow**: Different user journeys
   - **By Data**: Different data sets
   - **By Interface**: Different UI components

3. **Splitting in ERPNext**:
   - Use **Split Story** function
   - Create sub-tasks
   - Distribute story points
   - Maintain parent-child relationships

### Estimation

#### Story Points

1. **What are Story Points?**:
   - Relative measure of effort
   - Include complexity, risk, and uncertainty
   - Not time-based
   - Team-specific scale

2. **Common Scales**:
   - **Fibonacci**: 1, 2, 3, 5, 8, 13, 21
   - **Powers of 2**: 1, 2, 4, 8, 16
   - **T-shirt sizes**: XS, S, M, L, XL

3. **Estimation Process**:
   - **Planning Poker**: Team estimates together
   - **T-shirt Sizing**: Quick relative sizing
   - **Affinity Mapping**: Group by size

#### Estimation in ERPNext

1. **Individual Estimation**:
   - Open issue
   - Set **Story Points** field
   - Save

2. **Bulk Estimation**:
   - Use **Estimate Backlog Item** API
   - Apply estimation templates
   - Use planning poker results

3. **Estimation Tracking**:
   - Track estimation accuracy
   - Adjust estimates based on actuals
   - Improve estimation process

### Backlog Health

#### Health Metrics

1. **Estimation Coverage**:
   - Percentage of items estimated
   - Target: 80%+ estimated
   - Focus on top-priority items

2. **Refinement Status**:
   - Items with acceptance criteria
   - Items ready for sprint
   - Definition of ready compliance

3. **Size Distribution**:
   - Mix of small, medium, large items
   - Avoid too many large items
   - Ensure sprintable items

#### Backlog Maintenance

1. **Regular Reviews**:
   - Weekly backlog review
   - Remove outdated items
   - Update priorities
   - Add new items

2. **Stakeholder Input**:
   - Product owner input
   - Customer feedback
   - Market changes
   - Technical insights

3. **Team Input**:
   - Technical feasibility
   - Effort estimates
   - Dependencies
   - Risks

---

## Board Usage

### Understanding the Board

#### Board Purpose
The board provides a visual representation of your workflow:
- **Columns**: Represent workflow statuses
- **Cards**: Represent issues
- **Flow**: Issues move from left to right
- **Transparency**: Everyone can see progress

#### Board Types

1. **Sprint Board**:
   - Shows issues in current sprint
   - Focused on sprint execution
   - Real-time updates

2. **Backlog Board**:
   - Shows all unassigned issues
   - Focused on backlog management
   - Planning view

### Board Navigation

#### Accessing the Board

1. **From Project**:
   - Go to Project list
   - Open your project
   - Click **View Board** button

2. **From Sprint**:
   - Go to Agile Sprint list
   - Open active sprint
   - Click **View Board** button

3. **Direct URL**:
   - Bookmark board URL
   - Share with team members
   - Use in daily standups

#### Board Interface

1. **Columns**:
   - Each column represents a status
   - Issues are organized by status
   - Columns can be collapsed/expanded

2. **Issue Cards**:
   - Show issue key and title
   - Display assignee and story points
   - Color-coded by priority
   - Click to open issue

3. **Controls**:
   - **Filter**: Filter by assignee, type
   - **Refresh**: Update board data
   - **Settings**: Configure board options

### Using the Board

#### Moving Issues

1. **Drag and Drop**:
   - Click and hold issue card
   - Drag to target column
   - Drop to move issue
   - Status updates automatically

2. **Quick Actions**:
   - Right-click issue card
   - Select target status
   - Issue moves immediately

3. **Bulk Actions**:
   - Select multiple issues
   - Use bulk move action
   - Move all at once

#### Creating Issues

1. **Quick Create**:
   - Click **Quick Create** in any column
   - Fill in issue details
   - Issue created and added to column

2. **Inline Editing**:
   - Click issue card
   - Edit details inline
   - Save changes

3. **Template Creation**:
   - Use issue templates
   - Pre-fill common fields
   - Speed up creation

### Board Filtering

#### Filter Options

1. **By Assignee**:
   - Show only issues assigned to specific users
   - Useful for individual work tracking
   - Hide unassigned issues

2. **By Issue Type**:
   - Filter by Story, Task, Bug, etc.
   - Useful for type-specific work
   - Separate different work types

3. **By Priority**:
   - Show only high-priority issues
   - Useful for urgent work
   - Focus on important items

#### Using Filters

1. **Apply Filters**:
   - Click **Filter** button
   - Select filter criteria
   - Apply to board

2. **Combine Filters**:
   - Use multiple filters together
   - Narrow down view
   - Focus on specific work

3. **Save Filters**:
   - Save frequently used filters
   - Quick access to common views
   - Share with team

### Swimlanes

#### Swimlane Types

1. **By Assignee**:
   - Show who's working on what
   - Balance workload
   - Identify bottlenecks

2. **By Issue Type**:
   - Separate Stories, Bugs, Tasks
   - Different work types
   - Type-specific workflows

#### Using Swimlanes

1. **Enable Swimlanes**:
   - Click **Swimlanes** button
   - Select swimlane type
   - Board reorganizes

2. **Navigate Swimlanes**:
   - Scroll horizontally
   - Expand/collapse lanes
   - Focus on specific lanes

3. **Move Between Lanes**:
   - Drag issues between lanes
   - Update assignee
   - Maintain organization

### Board Configuration

#### Column Settings

1. **Add Columns**:
   - Add new status columns
   - Customize workflow
   - Match team process

2. **Remove Columns**:
   - Hide unused statuses
   - Simplify view
   - Focus on active statuses

3. **Reorder Columns**:
   - Drag columns to reorder
   - Match workflow sequence
   - Improve usability

#### WIP Limits

1. **Set WIP Limits**:
   - Limit issues per column
   - Prevent bottlenecks
   - Improve flow

2. **Monitor WIP**:
   - Visual indicators when limit exceeded
   - Alert team to bottlenecks
   - Encourage completion

3. **Adjust WIP**:
   - Increase limits as needed
   - Decrease to improve flow
   - Balance capacity

### Board Metrics

#### Cycle Time
- **Definition**: Time from start to completion
- **Measurement**: Average time in each status
- **Improvement**: Reduce cycle time

#### Throughput
- **Definition**: Issues completed per time period
- **Measurement**: Issues completed per day/week
- **Improvement**: Increase throughput

#### Lead Time
- **Definition**: Time from creation to completion
- **Measurement**: Total time in system
- **Improvement**: Reduce lead time

---

## Time Tracking

### Understanding Time Tracking

#### Purpose
Time tracking helps:
- **Estimate Accuracy**: Compare estimates to actuals
- **Capacity Planning**: Understand team capacity
- **Billing**: Track billable hours
- **Process Improvement**: Identify inefficiencies

#### Time Concepts

1. **Original Estimate**:
   - Initial time estimate
   - Set during planning
   - Used for capacity planning

2. **Time Spent**:
   - Actual time worked
   - Logged by team members
   - Used for accuracy analysis

3. **Remaining Estimate**:
   - Time left to complete
   - Updated as work progresses
   - Used for sprint planning

### Logging Work

#### Manual Time Logging

1. **From Issue Form**:
   - Open the issue
   - Click **Log Work** button
   - Fill in time and description
   - Save

2. **Time Formats**:
   - **Hours and Minutes**: "2h 30m"
   - **Decimal Hours**: "2.5h"
   - **Minutes Only**: "150m"
   - **Hours Only**: "2h"

3. **Work Description**:
   - Describe what was done
   - Include technical details
   - Note any challenges
   - Reference code changes

#### Using Timers

1. **Start Timer**:
   - Click **Start Timer** on issue
   - Timer begins counting
   - Visual indicator shows running timer

2. **Work on Issue**:
   - Focus on the issue
   - Timer tracks time automatically
   - Switch between issues as needed

3. **Stop Timer**:
   - Click **Stop Timer** when done
   - Add work description
   - Time is automatically logged

#### Bulk Time Logging

1. **Daily Logging**:
   - Log all work at end of day
   - Use consistent format
   - Include all issues worked on

2. **Weekly Logging**:
   - Review week's work
   - Log remaining time
   - Update estimates

### Time Estimates

#### Setting Estimates

1. **Original Estimate**:
   - Set during sprint planning
   - Based on story points
   - Include all work types

2. **Estimate Components**:
   - **Development**: Coding time
   - **Testing**: Testing time
   - **Review**: Code review time
   - **Documentation**: Documentation time

3. **Estimate Accuracy**:
   - Start with rough estimates
   - Refine based on experience
   - Track accuracy over time

#### Updating Estimates

1. **Remaining Estimate**:
   - Update as work progresses
   - Reflect current understanding
   - Used for sprint planning

2. **Estimate Changes**:
   - Document reason for change
   - Communicate to team
   - Learn from changes

3. **Estimate Reviews**:
   - Review estimates regularly
   - Compare to actuals
   - Improve estimation process

### Time Reports

#### Individual Reports

1. **Issue Time Report**:
   - View all time logged for issue
   - See estimate vs actual
   - Track work progress

2. **Personal Time Report**:
   - View your time across issues
   - See daily/weekly totals
   - Track productivity

#### Team Reports

1. **Sprint Time Report**:
   - View team time in sprint
   - See capacity utilization
   - Identify bottlenecks

2. **Project Time Report**:
   - View time across project
   - See team productivity
   - Track project progress

#### Management Reports

1. **Velocity Reports**:
   - Track team velocity
   - See trends over time
   - Predict future capacity

2. **Efficiency Reports**:
   - Compare estimates to actuals
   - Identify improvement areas
   - Track process maturity

### Time Tracking Best Practices

#### Accurate Logging

1. **Log Regularly**:
   - Log time daily
   - Don't wait until end of week
   - Use timers for accuracy

2. **Be Specific**:
   - Log actual time worked
   - Don't include breaks
   - Separate different activities

3. **Include Context**:
   - Describe what was done
   - Note any challenges
   - Reference related work

#### Estimate Improvement

1. **Track Accuracy**:
   - Compare estimates to actuals
   - Identify patterns
   - Learn from mistakes

2. **Refine Process**:
   - Update estimation process
   - Share learnings with team
   - Improve over time

3. **Consider Factors**:
   - Complexity of work
   - Team experience
   - External dependencies
   - Technical challenges

---

## GitHub Integration

### Setting Up Integration

#### Prerequisites

1. **GitHub Integration App**:
   - Install GitHub Integration app
   - Configure API access
   - Set up repositories

2. **Project Configuration**:
   - Link project to GitHub repository
   - Enable auto-sync options
   - Set branch naming conventions

3. **User Configuration**:
   - Add GitHub usernames to users
   - Configure API permissions
   - Test connectivity

#### Configuration Steps

1. **Install GitHub Integration**:
   ```bash
   bench get-app https://github.com/frappe/github_integration.git
   bench --site your-site.com install-app github_integration
   ```

2. **Configure Project**:
   - Open project settings
   - Set **GitHub Repository** (owner/repo format)
   - Enable **Auto Create GitHub Issues**
   - Set **Branch Naming Convention**

3. **Configure Users**:
   - Open user records
   - Add **GitHub Username** field
   - Set GitHub username for each user

### Syncing Issues

#### Agile to GitHub

1. **Automatic Sync**:
   - Issues created automatically sync to GitHub
   - Labels are created based on issue type/priority
   - Assignees are synced if GitHub usernames are set

2. **Manual Sync**:
   - Click **Sync to GitHub** button on issue
   - Issue is created/updated in GitHub
   - Labels and assignees are updated

3. **Bulk Sync**:
   - Use **Bulk Sync** from project
   - All issues are synced at once
   - Progress is tracked

#### GitHub to Agile

1. **Automatic Sync**:
   - GitHub issues are synced to agile
   - Issue keys are generated
   - Labels are parsed for type/priority

2. **Manual Sync**:
   - Use **Sync from GitHub** function
   - Select GitHub issues to sync
   - Agile tasks are created

3. **Webhook Sync**:
   - Set up GitHub webhooks
   - Changes sync automatically
   - Real-time updates

### Branch Management

#### Branch Naming

1. **Conventions**:
   - **Feature**: `feature/PROJ-123-user-login`
   - **Bugfix**: `bugfix/PROJ-124-login-error`
   - **Hotfix**: `hotfix/PROJ-125-security-patch`

2. **Configuration**:
   - Set branch naming convention in project
   - Use placeholders for issue key and summary
   - Ensure consistency across team

3. **Automatic Suggestions**:
   - System suggests branch names
   - Based on issue key and title
   - Follows project convention

#### Branch Creation

1. **Manual Creation**:
   - Create branch manually in GitHub
   - Use suggested naming convention
   - Link to issue

2. **Automatic Creation**:
   - Branches created automatically
   - When issues are created
   - Based on naming convention

### Commit Integration

#### Commit Linking

1. **Automatic Linking**:
   - Commits that reference issue keys are linked
   - Format: "PROJ-123: Implement login"
   - Links appear in issue

2. **Manual Linking**:
   - Manually link commits to issues
   - Use commit SHA or message
   - Track development progress

3. **PR Integration**:
   - Pull requests are linked to issues
   - PR status updates issue
   - Code review integration

#### Commit Messages

1. **Best Practices**:
   - Include issue key in commit message
   - Use descriptive messages
   - Reference related issues

2. **Format**:
   - `PROJ-123: Implement user login`
   - `PROJ-123: Fix login validation`
   - `PROJ-123: Add login tests`

### Label Management

#### Automatic Labels

1. **Issue Type Labels**:
   - `type:story`, `type:task`, `type:bug`
   - Based on issue type
   - Consistent across repository

2. **Priority Labels**:
   - `priority:critical`, `priority:high`
   - Based on issue priority
   - Visual priority indicators

3. **Sprint Labels**:
   - `sprint:sprint-1`, `sprint:sprint-2`
   - Based on current sprint
   - Track sprint progress

#### Custom Labels

1. **Component Labels**:
   - `component:auth`, `component:ui`
   - Based on issue components
   - Organize by system area

3. **Status Labels**:
   - `status:in-progress`, `status:blocked`
   - Based on issue status
   - Visual status indicators

### Integration Best Practices

#### Synchronization

1. **Regular Sync**:
   - Sync issues regularly
   - Keep both systems updated
   - Avoid conflicts

2. **Conflict Resolution**:
   - Handle conflicts gracefully
   - Prefer ERPNext as source of truth
   - Communicate changes to team

3. **Data Consistency**:
   - Ensure data consistency
   - Validate sync results
   - Monitor for errors

#### Team Coordination

1. **Workflow Integration**:
   - Integrate with development workflow
   - Use issue keys in commits
   - Link PRs to issues

2. **Communication**:
   - Communicate sync status
   - Share integration updates
   - Train team on process

3. **Monitoring**:
   - Monitor sync performance
   - Track integration health
   - Address issues promptly

---

## Reports and Analytics

### Sprint Reports

#### Sprint Summary

1. **Sprint Overview**:
   - Sprint name and dates
   - Team members
   - Sprint goal
   - Current status

2. **Issue Statistics**:
   - Total issues planned
   - Issues completed
   - Issues in progress
   - Issues blocked

3. **Story Points**:
   - Total points planned
   - Points completed
   - Points remaining
   - Velocity achieved

#### Burndown Charts

1. **Ideal Burndown**:
   - Straight line from total to zero
   - Shows planned progress
   - Reference for actual progress

2. **Actual Burndown**:
   - Shows real progress
   - Updated daily
   - Reveals sprint health

3. **Scope Changes**:
   - Shows added/removed work
   - Explains burndown deviations
   - Tracks scope creep

#### Sprint Metrics

1. **Velocity**:
   - Story points completed
   - Historical average
   - Trend analysis

2. **Cycle Time**:
   - Time from start to completion
   - Average per issue
   - Improvement opportunities

3. **Throughput**:
   - Issues completed per day
   - Team productivity
   - Capacity planning

### Backlog Reports

#### Backlog Health

1. **Estimation Coverage**:
   - Percentage of items estimated
   - Focus on top priorities
   - Planning readiness

2. **Size Distribution**:
   - Mix of small/medium/large items
   - Sprintable items available
   - Balanced backlog

3. **Refinement Status**:
   - Items with acceptance criteria
   - Ready for sprint planning
   - Definition of ready compliance

### Team Reports

#### Team Velocity

1. **Historical Velocity**:
   - Velocity over time
   - Trend analysis
   - Seasonal patterns

2. **Team Comparison**:
   - Velocity by team member
   - Contribution analysis
   - Capacity planning

3. **Predictions**:
   - Future sprint capacity
   - Delivery estimates
   - Risk assessment

#### Time Tracking

1. **Time Spent**:
   - Time by issue
   - Time by team member
   - Time by activity

2. **Estimate Accuracy**:
   - Estimate vs actual
   - Accuracy trends
   - Improvement areas

3. **Productivity**:
   - Time per story point
   - Efficiency metrics
   - Process improvement

### Project Reports

#### Project Overview

1. **Project Status**:
   - Overall progress
   - Key milestones
   - Current sprint

2. **Issue Summary**:
   - Total issues
   - Issues by status
   - Issues by type

3. **Team Summary**:
   - Team members
   - Active sprints
   - Recent activity

#### Release Reports

1. **Release Planning**:
   - Features planned
   - Timeline estimates
   - Risk assessment

2. **Release Progress**:
   - Features completed
   - Remaining work
   - Delivery prediction

3. **Release Metrics**:
   - Scope changes
   - Quality metrics
   - Delivery performance

### Custom Reports

#### Creating Reports

1. **Report Builder**:
   - Use ERPNext report builder
   - Create custom queries
   - Add filters and grouping

2. **Dashboard Creation**:
   - Create custom dashboards
   - Add charts and metrics
   - Share with team

3. **Automated Reports**:
   - Schedule regular reports
   - Email to stakeholders
   - Track key metrics

#### Report Sharing

1. **Team Sharing**:
   - Share reports with team
   - Regular review meetings
   - Action item tracking

2. **Stakeholder Reports**:
   - Executive summaries
   - Progress updates
   - Risk reports

3. **External Sharing**:
   - Export to PDF/Excel
   - Share via email
   - Publish to intranet

---

## Best Practices

### Issue Management

#### Writing Good Issues

1. **Clear Titles**:
   - Use action verbs
   - Be specific and concise
   - Include user perspective

2. **Detailed Descriptions**:
   - Provide context and background
   - Include acceptance criteria
   - Add screenshots or mockups

3. **Proper Categorization**:
   - Choose appropriate issue type
   - Set realistic priority

#### Issue Lifecycle

1. **Creation**:
   - Create issues early
   - Include all necessary details
   - Set up proper relationships

2. **Refinement**:
   - Regular backlog refinement
   - Add acceptance criteria
   - Estimate story points

3. **Execution**:
   - Update status regularly
   - Log work time
   - Communicate progress

### Sprint Management

#### Sprint Planning

1. **Capacity Planning**:
   - Consider team velocity
   - Account for holidays
   - Leave buffer for unexpected work

2. **Goal Setting**:
   - Set clear sprint goals
   - Communicate to stakeholders
   - Use for decision making

3. **Scope Management**:
   - Avoid scope changes
   - Communicate changes early
   - Document decisions

#### Sprint Execution

1. **Daily Management**:
   - Regular standups
   - Monitor burndown
   - Address blockers quickly

2. **Quality Focus**:
   - Don't compromise quality
   - Include testing time
   - Code review process

3. **Communication**:
   - Regular team communication
   - Stakeholder updates
   - Transparent progress

### Team Collaboration

#### Communication

1. **Regular Meetings**:
   - Daily standups
   - Sprint planning
   - Retrospectives

2. **Documentation**:
   - Document decisions
   - Share knowledge
   - Maintain process docs

3. **Feedback**:
   - Regular feedback sessions
   - Continuous improvement
   - Team building

#### Process Improvement

1. **Retrospectives**:
   - Regular retrospectives
   - Identify improvements
   - Implement changes

2. **Metrics Tracking**:
   - Track key metrics
   - Analyze trends
   - Make data-driven decisions

3. **Experimentation**:
   - Try new approaches
   - Measure results
   - Adapt based on outcomes

### Tool Usage

#### ERPNext Agile

1. **Consistent Usage**:
   - Use features consistently
   - Follow established processes
   - Maintain data quality

2. **Training**:
   - Train new team members
   - Share best practices
   - Regular tool updates

3. **Customization**:
   - Customize for team needs
   - Configure workflows
   - Set up integrations

#### Integration

1. **GitHub Integration**:
   - Use issue keys in commits
   - Link PRs to issues
   - Maintain sync

2. **Other Tools**:
   - Integrate with CI/CD
   - Connect to monitoring
   - Link to documentation

---

## Troubleshooting

### Common Issues

#### Issue Keys Not Generated

**Problem**: New issues don't get PROJ-123 style keys

**Solutions**:
1. Check Project has **Enable Agile** checked
2. Verify **Project Key** is set (e.g., "PROJ")
3. Ensure **Is Agile** is checked on Task
4. Check for JavaScript errors in browser console

#### Board Not Loading

**Problem**: Board view shows empty or errors

**Solutions**:
1. Verify project has workflow scheme configured
2. Check issue statuses exist
3. Clear browser cache
4. Check JavaScript console for errors
5. Verify user has permissions

#### Sprint Not Starting

**Problem**: Can't start sprint, validation errors

**Solutions**:
1. Check sprint state is "Future"
2. Verify no other active sprints in project
3. Ensure sprint dates are valid
4. Check user has permission to start sprints
5. Verify project is agile-enabled

#### Time Tracking Not Working

**Problem**: Can't log work or start timers

**Solutions**:
1. Verify task is agile-enabled
2. Check time format is correct
3. Ensure user has permission to log work
4. Check for JavaScript errors
5. Verify timer isn't already running

### Performance Issues

#### Slow Board Loading

**Solutions**:
1. Add database indexes
2. Reduce board data (use filters)
3. Limit to current sprint only
4. Use pagination for large datasets
5. Clear browser cache

#### Slow Reports

**Solutions**:
1. Add indexes for report queries
2. Use caching for expensive calculations
3. Run reports as background jobs
4. Archive old data
5. Optimize database queries

### Integration Issues

#### GitHub Sync Failing

**Solutions**:
1. Verify GitHub Integration app is installed
2. Check repository format (owner/repo)
3. Ensure GitHub API tokens are configured
4. Check user has GitHub username set
5. Verify repository exists and is accessible

#### Email Notifications Not Sending

**Solutions**:
1. Check email settings in ERPNext
2. Verify SMTP configuration
3. Check spam folders
4. Test with simple email first
5. Verify notification settings in project

### Getting Help

#### Self-Help Resources

1. **Documentation**: This user guide and API reference
2. **ERPNext Docs**: ERPNext documentation
3. **Community Forum**: ERPNext community
4. **GitHub Issues**: Report bugs and request features

#### Contact Support

1. **Email**: tamocha44@gmail.com
2. **GitHub Issues**: Create detailed issue reports
3. **Community**: Ask questions in ERPNext community
4. **Professional Support**: Hire ERPNext consultants

#### Reporting Issues

When reporting issues, include:
1. **Steps to Reproduce**: Detailed steps
2. **Expected Behavior**: What should happen
3. **Actual Behavior**: What actually happens
4. **Environment**: ERPNext version, browser, etc.
5. **Screenshots**: Visual evidence of the issue

---

*Last updated: January 2024*
*Version: 1.0.0*
