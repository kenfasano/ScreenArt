#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd):
    """Helper to run shell commands and catch errors."""
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {' '.join(cmd)}: {e}")
        sys.exit(1)

def main():
    # 1. Ensure we are in the right directory
    # Expanding user for Mac Mini compatibility (~/ vs /home/kenfasano)
    repo_path = os.path.expanduser("~/Scripts/ScreenArt")
    os.chdir(repo_path)

    print(f"--- Updating ScreenArt at {repo_path} ---")

    # 2. Stage all changes (Git will automatically skip the ignored Images folder)
    run_command(["git", "add", "."])

    # 3. Prompt for commit message
    print("\n[ Git Commit ]")
    commit_msg = input("Enter update message (or press Enter for 'Auto-update'): ").strip()
    
    if not commit_msg:
        # Default message if you're in a hurry
        commit_msg = f"Auto-update: {subprocess.check_output(['date', '+%Y-%m-%d %H:%M']).decode().strip()}"

    # 4. Commit
    run_command(["git", "commit", "-m", commit_msg])

    # 5. Push to GitHub
    print("\n[ Pushing to GitHub... ]")
    run_command(["git", "push"])

    print("\nDone! Repository is up to date.")

if __name__ == "__main__":
    main()
