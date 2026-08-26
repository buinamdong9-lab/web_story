import os
import sys
import subprocess
from health_check import run_health_check
from build_library import build_all_library

if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

def run_deploy(commit_message=None):
    """Executes full automated build, verification, and deployment to GitHub"""
    print("==================================================")
    print("        WEB STORY 1-CLICK DEPLOY PIPELINE         ")
    print("==================================================")

    # 1. Build and Minify
    print("\n[STEP 1/3] Building library & minifying payloads...")
    build_all_library()

    # 2. Health check
    print("\n[STEP 2/3] Verifying library integrity...")
    is_healthy = run_health_check()
    if not is_healthy:
        print("[WARNING] Health check flagged warnings, continuing deployment...")

    # 3. Git commit & push
    print("\n[STEP 3/3] Committing and pushing to GitHub...")
    if not commit_message:
        commit_message = "feat: update stories library and assets"

    try:
        subprocess.run(["git", "add", "."], check=True)
        # Check if there are changes to commit
        status_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status_proc.stdout.strip():
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
        else:
            print("-> No uncommitted changes.")

        subprocess.run(["git", "push"], check=True)
        print("\n==================================================")
        print("[SUCCESS] Deployed successfully to GitHub Pages!")
        print("Live URL: https://buinamdong9-lab.github.io/web_story/")
        print("==================================================")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Git deployment failed: {e}")

if __name__ == '__main__':
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    run_deploy(msg)
