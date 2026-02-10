#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd, capture=False):
    """Helper to run shell commands and catch errors."""
    try:
        if capture:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
        subprocess.run(cmd, check=True, text=True)
        return None
    except subprocess.CalledProcessError as e:
        # If it's a commit error and the message says 'nothing to commit', we handle it gracefully
        if "nothing to commit" in str(e.output if capture else ""):
            return "CLEAN"
        print(f"Error executing {' '.join(cmd)}: {e}")
        sys.exit(1)

def main():
    repo_path = os.path.expanduser("~/Scripts/ScreenArt")
    os.chdir(repo_path)

    print(f"--- Updating ScreenArt at {repo_path} ---")

    # 1. Stage changes
    run_command(["git", "add", "."])

    # 2. Check if there are actually changes to commit
    # 'git status --porcelain' is empty if there are no changes
    status = run_command(["git", "status", "--porcelain"], capture=True)
    
    if not status:
        print("Everything is already up to date. Nothing to do!")
        return

    # 3. Prompt for commit message
    print("\n[ Git Commit ]")
    commit_msg = input("Enter update message (or press Enter for 'Auto-update'): ").strip()
    
    if not commit_msg:
        commit_msg = f"Auto-update: {run_command(['date', '+%Y-%m-%d %H:%M'], capture=True)}"

    # 4. Commit and Push
    run_command(["git", "commit", "-m", commit_msg])
    
    print("\n[ Pushing to GitHub... ]")
    run_command(["git", "push"])

    print("\nDone! Repository is up to date.")

if __name__ == "__main__":
    main()
