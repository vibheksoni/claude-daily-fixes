# Claude Code Workarounds

A collection of daily workarounds and fixes for common issues when using Claude Code.

## Overview

This repository contains scripts and utilities to solve frequent problems encountered while using Claude Code. Each tool addresses specific limitations or bugs that affect daily workflow.

## Current Tools

### wsl-paste-workaround.py
Enables image pasting when using Claude Code through WSL.

**What it does:**
- Captures images from Windows clipboard when using Shift+Insert
- Automatically saves images to a `sharedclaude` folder
- Pastes the correct `@sharedclaude/filename.png` format into terminal

**When to use:**
- Working with Claude Code in WSL environment
- Need to paste images from Windows clipboard
- Want automatic image organization in shared folder

**Installation:**
```bash
pip install -r requirements.txt
```

**Usage:**
```bash
# Run with admin privileges (recommended)
python wsl-paste-workaround.py /path/to/your/project

# Or provide path interactively
python wsl-paste-workaround.py
```

**How it works:**
- If path doesn't end with `sharedclaude`, creates that subdirectory automatically
- Press Shift+Insert to capture clipboard image
- Images auto-delete after 5 minutes
- Press Ctrl+C to stop

### UpdateFix.sh
Fixes Claude update issues when it claims another instance is updating.

**When to use:**
- Claude says it's outdated but update fails
- Gets "another instance is updating" error when no other instance exists

**Usage:**
```bash
./UpdateFix.sh
```

**What it does:**
- Cleans up stuck update locks
- Runs Claude update
- Removes outdated Claude binaries
- Refreshes shell cache

## Installation

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make shell scripts executable:
   ```bash
   chmod +x UpdateFix.sh
   ```

## Requirements

- Python 3.6+
- Windows (for WSL paste workaround)
- WSL environment (for paste workaround)
- Claude Code installed

## Contributing Your Workarounds

**Have your own Claude Code fixes?** We'd love to include them!

Submit your workarounds via:
- Pull requests with your scripts and documentation
- Issues describing problems and solutions you've found
- Suggestions for improvements to existing tools

Each contribution should include:
- Clear description of the problem it solves
- Installation instructions
- Usage examples
- When to use it

## Adding New Workarounds

This repository will be updated with additional workarounds and fixes as they are developed for daily Claude Code usage.

## Support This Project

If these tools help your Claude Code workflow:

⭐ **Star this repository** to help others discover these fixes  
🔄 **Share with colleagues** who use Claude Code  
🤝 **Contribute your own workarounds** to help the community  

## Notes

- Run `wsl-paste-workaround.py` with administrator privileges for best results
- Images are automatically cleaned up after 5 minutes to save disk space
- Backup your work before running any fix scripts

---

**Found this helpful?** Star the repo and share it with other Claude Code users! 