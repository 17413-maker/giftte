import os

# Root folder
root = "aditya_osint"

# Folder structure
folders = [
    "app",
    "app/core",
    "app/db",
    "app/osint_tools",
    "app/osint_tools/other_tools",
    "app/routers",
    "app/services",
    "app/static/css",
    "app/static/js",
    "app/static/images",
    "app/templates",
    "tests",
    "docs"
]

# Files with optional placeholder content
files = {
    "main.py": "# Entry point for FastAPI app\n",
    "requirements.txt": "# Dependencies placeholder\n",
    ".env": "# Secrets placeholder\n",
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/core/config.py": "# Configs placeholder\n",
    "app/core/security.py": "# Security utils placeholder\n",
    "app/core/email_utils.py": "# Email utils placeholder\n",
    "app/db/__init__.py": "",
    "app/db/database.py": "# Database connection placeholder\n",
    "app/db/models.py": "# DB models placeholder\n",
    "app/db/crud.py": "# CRUD operations placeholder\n",
    "app/osint_tools/__init__.py": "",
    "app/osint_tools/sherlock_integration.py": "# Sherlock integration placeholder\n",
    "app/osint_tools/holehe_integration.py": "# Holehe integration placeholder\n",
    "app/osint_tools/OSN.py": "# Placeholder for future OSINT logic\n",
    "app/osint_tools/other_tools/__init__.py": "",
    "app/routers/__init__.py": "",
    "app/routers/auth_router.py": "# Auth router placeholder\n",
    "app/routers/osint_router.py": "# OSINT router placeholder\n",
    "app/routers/gift_router.py": "# Gift router placeholder\n",
    "app/routers/devmode_router.py": "# DevMode router placeholder\n",
    "app/services/__init__.py": "",
    "app/services/gift_ai.py": "# Gift AI logic placeholder\n",
    "app/services/report_generator.py": "# Report generator placeholder\n",
    "app/static/css/style.css": "/* CSS placeholder */\n",
    "app/static/js/main.js": "// JS placeholder\n",
    "app/templates/index.html": "<!-- Index placeholder -->\n",
    "app/templates/consent.html": "<!-- Consent placeholder -->\n",
    "app/templates/signup.html": "<!-- Signup placeholder -->\n",
    "app/templates/login.html": "<!-- Login placeholder -->\n",
    "app/templates/automatic.html": "<!-- Automatic mode placeholder -->\n",
    "app/templates/manual.html": "<!-- Manual mode placeholder -->\n",
    "app/templates/devmode.html": "<!-- DevMode placeholder -->\n",
    "app/templates/verification.html": "<!-- Email verification placeholder -->\n",
    "tests/__init__.py": "",
    "tests/test_osint.py": "# OSINT tests placeholder\n",
    "tests/test_email.py": "# Email tests placeholder\n",
    "docs/API_DOCS.md": "# API Docs placeholder\n",
    "docs/SETUP_GUIDE.md": "# Setup guide placeholder\n"
}

# Create folders
for folder in folders:
    path = os.path.join(root, folder)
    os.makedirs(path, exist_ok=True)

# Create files with content
for filepath, content in files.items():
    path = os.path.join(root, filepath)
    with open(path, "w") as f:
        f.write(content)

print(f"Folder structure for '{root}' created successfully!")
