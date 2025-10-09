# ERPNext Agile - Installation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Post-Installation Setup](#post-installation-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Upgrading](#upgrading)
8. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

- **ERPNext Version**: v15.0.0 or higher
- **Python**: 3.10 or higher
- **Node.js**: 16.x or higher
- **Database**: MySQL 8.0+ or MariaDB 10.6+
- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 10GB free space

### Required Apps

- **ERPNext**: Core ERPNext installation
- **GitHub Integration** (optional): For GitHub sync functionality

### Bench Setup

Ensure you have a working ERPNext bench installation:

```bash
# Verify bench is installed
bench --version

# Verify ERPNext is installed
bench --site your-site.com list-apps
```

---

## Installation Methods

### Method 1: Install from GitHub (Recommended)

#### Step 1: Download the App

```bash
# Navigate to your bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/your-username/erpnext_agile.git
```

#### Step 2: Install to Your Site

```bash
# Install the app to your site
bench --site your-site.com install-app erpnext_agile

# Migrate the database
bench --site your-site.com migrate

# Restart the server
bench restart
```

### Method 2: Install from Local Source

#### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-username/erpnext_agile.git
cd erpnext_agile
```

#### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

#### Step 3: Install to Bench

```bash
# Navigate to bench directory
cd ~/frappe-bench

# Create symlink to app
ln -s /path/to/erpnext_agile apps/erpnext_agile

# Install to site
bench --site your-site.com install-app erpnext_agile
bench --site your-site.com migrate
bench restart
```

### Method 3: Install from Release Package

#### Step 1: Download Release

```bash
# Download latest release
wget https://github.com/your-username/erpnext_agile/releases/download/v1.0.0/erpnext_agile-v1.0.0.tar.gz

# Extract
tar -xzf erpnext_agile-v1.0.0.tar.gz
cd erpnext_agile-v1.0.0
```

#### Step 2: Install

```bash
# Navigate to bench directory
cd ~/frappe-bench

# Copy app to bench
cp -r /path/to/erpnext_agile-v1.0.0 apps/erpnext_agile

# Install to site
bench --site your-site.com install-app erpnext_agile
bench --site your-site.com migrate
bench restart
```

---

## Post-Installation Setup

### Automatic Setup

The app automatically performs these setup tasks during installation:

1. **Creates DocTypes**: All required DocTypes are created
2. **Sets up Custom Fields**: Task and Project forms are enhanced
3. **Installs JavaScript**: Frontend enhancements are loaded
4. **Configures Scheduled Tasks**: Automated tasks are set up
5. **Creates Default Data**: Basic issue types, priorities, and statuses

### Manual Verification

Verify the installation completed successfully:

```bash
# Check if app is installed
bench --site your-site.com list-apps | grep erpnext_agile

# Check DocTypes
bench --site your-site.com console
>>> frappe.get_meta('Agile Sprint')
>>> frappe.get_meta('Agile Issue Status')
```

### Database Verification

Check that all tables were created:

```sql
-- Connect to your database
mysql -u root -p

-- Check for agile tables
SHOW TABLES LIKE '%agile%';

-- Verify key tables exist
DESCRIBE `tabAgile Sprint`;
DESCRIBE `tabAgile Issue Status`;
```

---

## Configuration

### Step 1: Enable Agile for Projects

1. **Navigate to Project List**:
   ```
   ERPNext → Projects → Project
   ```

2. **Open a Project**:
   - Select an existing project or create a new one
   - Click on the project name to open

3. **Enable Agile**:
   - Check the **Enable Agile** checkbox
   - Set **Project Key** (e.g., "PROJ" for PROJ-123 issue keys)
   - Save the project

### Step 2: Configure Workflow Scheme

1. **Create Issue Statuses**:
   ```
   ERPNext → Erpnext Agile → Agile Issue Status → New
   ```
   
   Create statuses like:
   - **Open** (To Do category)
   - **In Progress** (In Progress category)
   - **Done** (Done category)
   - **Blocked** (In Progress category)

2. **Create Workflow Scheme**:
   ```
   ERPNext → Erpnext Agile → Agile Workflow Scheme → New
   ```
   
   - Set **Scheme Name**
   - Add statuses and define transitions
   - Assign to projects

### Step 3: Configure Permission Scheme

1. **Create Permission Scheme**:
   ```
   ERPNext → Erpnext Agile → Agile Permission Scheme → New
   ```

2. **Define Permissions**:
   - Set role-based permissions
   - Configure workflow transition permissions
   - Assign to projects

### Step 4: Set Up Issue Types and Priorities

1. **Create Issue Types**:
   ```
   ERPNext → Erpnext Agile → Agile Issue Type → New
   ```
   
   Common types:
   - **Story**: User-facing features
   - **Task**: Technical work
   - **Bug**: Defects to fix
   - **Epic**: Large features
   - **Spike**: Research work

2. **Create Priorities**:
   ```
   ERPNext → Erpnext Agile → Agile Issue Priority → New
   ```
   
   Common priorities:
   - **Critical**: System down, security issues
   - **High**: Major features, important bugs
   - **Medium**: Standard work
   - **Low**: Nice-to-have items

### Step 5: Configure GitHub Integration (Optional)

#### Install GitHub Integration App

```bash
# Get GitHub Integration app
bench get-app https://github.com/frappe/github_integration.git

# Install to site
bench --site your-site.com install-app github_integration
bench --site your-site.com migrate
bench restart
```

#### Configure GitHub Settings

1. **In Project Settings**:
   - Set **GitHub Repository** (format: owner/repo)
   - Enable **Auto Create GitHub Issues**
   - Set **Branch Naming Convention** (e.g., "feature/{issue_key}-{summary}")

2. **Configure User GitHub Usernames**:
   ```
   ERPNext → Users and Permissions → User → [Select User]
   ```
   - Add **GitHub Username** field
   - Set GitHub username for each user

3. **Set Up GitHub API Access**:
   - Create GitHub Personal Access Token
   - Configure in GitHub Integration app settings

---

## Verification

### Step 1: Test Basic Functionality

1. **Create a Test Issue**:
   ```
   ERPNext → Projects → Task → New
   ```
   - Fill in Subject and Description
   - Check **Is Agile** checkbox
   - Set Issue Type, Priority, Story Points
   - Save

2. **Verify Issue Key Generation**:
   - Check that issue key is generated (e.g., PROJ-1)
   - Verify issue appears in agile views

### Step 2: Test Sprint Management

1. **Create a Sprint**:
   ```
   ERPNext → Erpnext Agile → Agile Sprint → New
   ```
   - Set Sprint Name, Project, Dates
   - Save

2. **Start the Sprint**:
   - Open the sprint
   - Click **Start Sprint** button
   - Verify sprint state changes to "Active"

### Step 3: Test Board View

1. **Access Board**:
   - Go to Project form
   - Click **View Board** button
   - Verify board loads with columns

2. **Test Issue Movement**:
   - Drag an issue between columns
   - Verify status changes
   - Check issue updates in database

### Step 4: Test Time Tracking

1. **Log Work**:
   - Open a task
   - Click **Log Work** button
   - Enter time and description
   - Save

2. **Start Timer**:
   - Click **Start Timer** on a task
   - Wait a few seconds
   - Click **Stop Timer**
   - Verify work is logged

### Step 5: Test GitHub Integration (If Configured)

1. **Sync Issue to GitHub**:
   - Open an agile issue
   - Click **Sync to GitHub** button
   - Verify GitHub issue is created

2. **Check GitHub Issue**:
   - Visit GitHub repository
   - Verify issue exists with proper labels
   - Check issue body contains ERPNext details

---

## Troubleshooting

### Common Installation Issues

#### Issue: App Installation Fails

**Symptoms**: Error during `bench install-app`

**Solutions**:
```bash
# Check ERPNext version
bench --site your-site.com console
>>> frappe.__version__

# Update ERPNext if needed
bench update

# Try installation again
bench --site your-site.com install-app erpnext_agile --force
```

#### Issue: DocTypes Not Created

**Symptoms**: Agile DocTypes missing after installation

**Solutions**:
```bash
# Reinstall the app
bench --site your-site.com uninstall-app erpnext_agile
bench --site your-site.com install-app erpnext_agile
bench --site your-site.com migrate

# Check DocTypes manually
bench --site your-site.com console
>>> frappe.get_meta('Agile Sprint')
```

#### Issue: JavaScript Errors

**Symptoms**: Board not loading, console errors

**Solutions**:
```bash
# Rebuild assets
bench build

# Clear cache
bench --site your-site.com clear-cache

# Restart server
bench restart
```

#### Issue: Database Migration Errors

**Symptoms**: Migration fails with SQL errors

**Solutions**:
```bash
# Check database connection
bench --site your-site.com mariadb

# Backup database first
bench --site your-site.com backup

# Try migration with verbose output
bench --site your-site.com migrate --verbose
```

### Configuration Issues

#### Issue: Issue Keys Not Generated

**Symptoms**: New issues don't get PROJ-123 style keys

**Solutions**:
1. Check Project has **Enable Agile** checked
2. Verify **Project Key** is set (e.g., "PROJ")
3. Ensure **Is Agile** is checked on Task
4. Check for JavaScript errors in browser console

#### Issue: Board Not Loading

**Symptoms**: Board view shows empty or errors

**Solutions**:
1. Verify project has workflow scheme configured
2. Check issue statuses exist
3. Clear browser cache
4. Check JavaScript console for errors
5. Verify user has permissions

#### Issue: Sprint Not Starting

**Symptoms**: Can't start sprint, validation errors

**Solutions**:
1. Check sprint state is "Future"
2. Verify no other active sprints in project
3. Ensure sprint dates are valid
4. Check user has permission to start sprints
5. Verify project is agile-enabled

### Performance Issues

#### Issue: Slow Board Loading

**Solutions**:
```sql
-- Add database indexes
ALTER TABLE `tabTask` ADD INDEX `project_agile_idx` (`project`, `is_agile`);
ALTER TABLE `tabTask` ADD INDEX `sprint_status_idx` (`current_sprint`, `issue_status`);
```

#### Issue: Memory Issues

**Solutions**:
1. Increase server memory
2. Optimize database queries
3. Use pagination for large datasets
4. Clear caches regularly

### GitHub Integration Issues

#### Issue: GitHub Sync Failing

**Symptoms**: GitHub issues not created or updated

**Solutions**:
1. Verify GitHub Integration app is installed
2. Check repository format (owner/repo)
3. Ensure GitHub API tokens are configured
4. Check user has GitHub username set
5. Verify repository exists and is accessible

#### Issue: GitHub API Rate Limiting

**Symptoms**: GitHub API errors, rate limit exceeded

**Solutions**:
1. Implement request throttling
2. Use webhooks instead of polling
3. Cache GitHub data
4. Use GitHub App instead of personal tokens

### Getting Help

#### Check Logs

```bash
# Application logs
tail -f logs/bench.log

# Error logs
tail -f logs/error.log

# Worker logs
tail -f logs/worker.log
```

#### Debug Mode

```bash
# Enable debug mode
bench --site your-site.com set-config developer_mode 1
bench --site your-site.com set-config logging 2
bench restart
```

#### Community Support

- **GitHub Issues**: Report bugs and request features
- **ERPNext Community**: Ask questions and get help
- **Documentation**: Check this guide and API reference

---

## Upgrading

### Backup Before Upgrade

```bash
# Backup database
bench --site your-site.com backup

# Backup files
bench --site your-site.com backup --with-files
```

### Upgrade Process

#### Method 1: Update from GitHub

```bash
# Navigate to app directory
cd ~/frappe-bench/apps/erpnext_agile

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt
npm install

# Migrate database
bench --site your-site.com migrate

# Restart server
bench restart
```

#### Method 2: Reinstall App

```bash
# Uninstall current version
bench --site your-site.com uninstall-app erpnext_agile

# Get latest version
bench get-app https://github.com/your-username/erpnext_agile.git --overwrite

# Install new version
bench --site your-site.com install-app erpnext_agile
bench --site your-site.com migrate
bench restart
```

### Post-Upgrade Verification

1. **Check Version**:
   ```bash
   bench --site your-site.com console
   >>> import erpnext_agile
   >>> erpnext_agile.__version__
   ```

2. **Test Functionality**:
   - Create a test issue
   - Start a test sprint
   - Verify board works
   - Check time tracking

3. **Check for Breaking Changes**:
   - Review changelog
   - Test custom configurations
   - Verify integrations work

---

## Uninstallation

### Backup Data

```bash
# Backup before uninstallation
bench --site your-site.com backup
```

### Uninstall App

```bash
# Uninstall the app
bench --site your-site.com uninstall-app erpnext_agile

# Remove from bench
rm -rf ~/frappe-bench/apps/erpnext_agile

# Restart server
bench restart
```

### Clean Up (Optional)

#### Remove Custom Fields

```bash
# Connect to database
bench --site your-site.com mariadb

# Remove custom fields
DELETE FROM `tabCustom Field` WHERE `dt` IN ('Task', 'Project') AND `module` = 'Erpnext Agile';
```

#### Remove DocTypes

```bash
# Remove DocTypes (WARNING: This will delete all data)
bench --site your-site.com console
>>> frappe.delete_doc('DocType', 'Agile Sprint')
# ... repeat for all agile DocTypes
```

### Verify Uninstallation

```bash
# Check app is removed
bench --site your-site.com list-apps | grep erpnext_agile

# Check DocTypes are removed
bench --site your-site.com console
>>> frappe.get_meta('Agile Sprint')  # Should raise error
```

---

## Support

### Getting Help

- **Documentation**: This installation guide and main documentation
- **GitHub Issues**: Report bugs and request features
- **ERPNext Community**: Ask questions and get community help
- **Email Support**: tamocha44@gmail.com

### Professional Support

For enterprise installations and support:
- Contact the development team
- Hire ERPNext consultants
- Consider paid support plans

---

*Last updated: January 2024*
*Version: 1.0.0*
