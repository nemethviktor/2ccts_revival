import subprocess
import os
import re
from datetime import date

# Determine the project root (one level up from this script in ./tools)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

def get_git_info():
    try:
        def run_git(args):
            return subprocess.check_output(['git'] + args, cwd=ROOT_DIR, stderr=subprocess.STDOUT).decode().strip()

        # Get display version (e.g., 3.3-alpha0-12-g1a9ed03d_dirty)
        display_version = run_git(['describe', '--tags', '--dirty', '--always'])
        display_version = display_version.replace("-dirty", "_dirty")
        
        # Get full hash
        repo_hash = run_git(['rev-parse', 'HEAD'])
        
        # Calculate days since 2000-01-01 (Matches findversion.sh VERSION logic) [cite: 1]
        git_ts = run_git(['log', '-1', '--format=%at'])
        commit_date = date.fromtimestamp(int(git_ts))
        newgrf_version = (commit_date - date(2000, 1, 1)).days

        return {
            'hash': repo_hash,
            'newgrf_version': str(newgrf_version),
            'display_version': display_version
        }
    except Exception:
        return {'hash': '', 'newgrf_version': '0', 'display_version': 'noRev'}

def update_pnml_header(new_version):
    pnml_path = os.path.join(ROOT_DIR, 'src', 'header.pnml')
    
    if not os.path.exists(pnml_path):
        print(f"Warning: {pnml_path} not found.")
        return

    try:
        with open(pnml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            # Anchor to the start of the line or whitespace to ensure we only hit "version:"
            # and NOT "min_compatible_version:"
            if re.search(r'^\s*version:', line):
                # Replace the value but keep leading tabs/spaces [cite: 1]
                line = re.sub(r'(^\s*version:\s+)([^\s;]+)', r'\g<1>' + new_version, line)
            new_lines.append(line)

        with open(pnml_path, 'w', encoding='utf-8', newline='') as f:
            f.writelines(new_lines)
        print(f"Updated header.pnml 'version:' to: {new_version}")
    except Exception as e:
        print(f"Error updating PNML: {e}")

def generate_version_file():
    # Metadata from project context [cite: 2]
    project_title = "2cc Trains In NML (Revival)"
    filename = "2ccts_revival.grf"
    
    info = get_git_info()
    update_pnml_header(info['newgrf_version'])
    
    # Save to custom_tags.txt in the root directory
    output_path = os.path.join(ROOT_DIR, 'custom_tags.txt')
    lines = [
        f"VERSION        :{info['display_version']}",
        f"VERSION_STRING :{info['display_version']}",
        f"TITLE          :{project_title} {info['display_version']}",
        f"FILENAME       :{filename}",
        f"REPO_HASH      :{info['hash']}",
        f"NEWGRF_VERSION :{info['newgrf_version']}"
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Done. Metadata written to: {output_path}")

if __name__ == "__main__":
    generate_version_file()