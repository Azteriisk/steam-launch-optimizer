import os
import re
import glob
import subprocess
import sys
from pathlib import Path

# --- CONFIGURATION & TEXT ---
SCRIPT_NAME = "Steam Launch Options Optimizer"
DESCRIPTION = "Add gamemoderun, mangohud, and more to all Steam games easily."
# ---------------------

def is_steam_running():
    """Checks if Steam is currently running."""
    try:
        output = subprocess.check_output(["pgrep", "steam"]).decode().strip()
        return len(output) > 0
    except subprocess.CalledProcessError:
        return False

def get_distro():
    """Detects the current Linux distribution."""
    try:
        with open("/etc/os-release") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().strip('"')
                if line.startswith("ID_LIKE="):
                    return line.split("=")[1].strip().strip('"')
    except:
        return "unknown"
    return "unknown"

def install_dependencies(tools):
    """Offers to install missing tools based on the distro."""
    distro = get_distro()
    pkg_map = {
        "arch": {
            "gamemode": "gamemode", 
            "mangohud": "mangohud", 
            "gamescope": "gamescope",
            "lib32-gamemode": "lib32-gamemode", 
            "lib32-mangohud": "lib32-mangohud"
        },
        "fedora": {
            "gamemode": "gamemode", 
            "mangohud": "mangohud",
            "gamescope": "gamescope"
        },
        "ubuntu": {
            "gamemode": "gamemode", 
            "mangohud": "mangohud",
            "gamescope": "gamescope"
        },
        "debian": {
            "gamemode": "gamemode", 
            "mangohud": "mangohud",
            "gamescope": "gamescope"
        },
        "cachyos": {
            "gamemode": "gamemode", 
            "mangohud": "mangohud", 
            "gamescope": "gamescope",
            "lib32-gamemode": "lib32-gamemode", 
            "lib32-mangohud": "lib32-mangohud"
        }
    }
    
    # Generic arch-like check
    if distro not in pkg_map and "arch" in distro:
        distro = "arch"

    if distro not in pkg_map:
        print(f"Unsupported distro for auto-install: {distro}. Please install {', '.join(tools)} manually.")
        return False

    install_cmd = []
    if distro in ["arch", "cachyos"]:
        install_cmd = ["sudo", "pacman", "-S", "--needed"]
        pkgs = []
        for t in tools:
            if t in pkg_map[distro]:
                pkgs.append(pkg_map[distro][t])
            if f"lib32-{t}" in pkg_map[distro]:
                pkgs.append(pkg_map[distro][f"lib32-{t}"])
        install_cmd.extend(pkgs)
    elif distro == "fedora":
        install_cmd = ["sudo", "dnf", "install"] + [pkg_map[distro][t] for t in tools if t in pkg_map[distro]]
    elif distro in ["ubuntu", "debian"]:
        install_cmd = ["sudo", "apt", "install"] + [pkg_map[distro][t] for t in tools if t in pkg_map[distro]]

    if not install_cmd or len(install_cmd) <= 3: # 3 is index for sudo, pkg_mgr, command
         return False

    print(f"Running: {' '.join(install_cmd)}")
    try:
        subprocess.run(install_cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_tools(selected_tools):
    """Verifies if the selected tools are installed."""
    missing = []
    for tool in selected_tools:
        cmd = "gamemoderun" if tool == "gamemode" else tool
        if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
            missing.append(tool)
    return missing

def update_vdf(file_path, new_options_str, replace_existing=False):
    """Core logic to update the localconfig.vdf file."""
    print(f"Processing: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    # Regex to find the apps block
    apps_match = re.search(r'([ \t]*"apps"\s*\{)(.*?)(\n[ \t]*\}\n[ \t]*"LastPlayedTimesSyncTime"|\n[ \t]{3,4}\}(?=\n))', content, re.IGNORECASE | re.DOTALL)
    
    if not apps_match:
        print(f"Could not find 'apps' block in {file_path}")
        return

    prefix = apps_match.group(1)
    apps_block = apps_match.group(2)
    suffix = apps_match.group(3)
    
    app_pattern = re.compile(r'([ \t]*"\d+"\s*\{)(.*?)(\n[ \t]*\})', re.DOTALL)
    
    def modify_app_block(match):
        start = match.group(1)
        inner = match.group(2)
        end = match.group(3)
        
        if '"LaunchOptions"' in inner:
            if replace_existing:
                inner = re.sub(r'("LaunchOptions"[ \t]+)"[^"]*"', rf'\1"{new_options_str}"', inner)
            else:
                existing_match = re.search(r'"LaunchOptions"[ \t]+"([^"]*)"', inner)
                if existing_match:
                    existing = existing_match.group(1)
                    # Don't add if already there, but ensure %command% is at the end
                    # Clean up existing to remove %command% temporarily for check
                    base_existing = existing.replace("%command%", "").strip()
                    if new_options_str.replace("%command%", "").strip() not in base_existing:
                        # Construct new string: [existing parts] [new parts] %command%
                        clean_new = new_options_str.replace("%command%", "").strip()
                        new_val = f"{base_existing} {clean_new} %command%".strip()
                        inner = re.sub(r'("LaunchOptions"[ \t]+)"[^"]*"', rf'\1"{new_val}"', inner)
        else:
            indent = end.replace('\n', '').replace('}', '') + '\t'
            inner += f'\n{indent}"LaunchOptions"\t\t"{new_options_str}"'

        return start + inner + end

    new_apps_block = app_pattern.sub(modify_app_block, apps_block)
    new_content = content[:apps_match.start()] + prefix + new_apps_block + suffix + content[apps_match.end():]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def run_optimizer(options):
    """Main execution logic."""
    if is_steam_running():
        return False, "Steam is currently running. Please close Steam completely before continuing to avoid file conflicts."

    selected_tools = []
    if options['gamemode']: selected_tools.append('gamemode')
    if options['mangohud']: selected_tools.append('mangohud')
    if options['gamescope']: selected_tools.append('gamescope')

    missing = check_tools(selected_tools)
    if missing:
        print(f"Missing tools: {', '.join(missing)}")
        if not install_dependencies(missing):
            return False, f"Failed to install or skipped installing: {', '.join(missing)}"

    # Construct the launch option string
    parts = []
    if options['gamemode']: parts.append("gamemoderun")
    if options['mangohud']: parts.append("mangohud")
    if options['gamescope']: parts.append("gamescope --") # gamescope needs -- before the command
    parts.append("%command%")
    
    launch_str = " ".join(parts)

    steam_paths = [
        os.path.expanduser("~/.steam/steam/userdata/*/config/localconfig.vdf"),
        os.path.expanduser("~/.local/share/Steam/userdata/*/config/localconfig.vdf"),
        os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata/*/config/localconfig.vdf")
    ]

    found = False
    for path_pattern in steam_paths:
        files = glob.glob(path_pattern)
        for vdf_file in files:
            found = True
            os.system(f'cp "{vdf_file}" "{vdf_file}.bak"')
            update_vdf(vdf_file, launch_str, options['replace'])
    
    if not found:
        return False, "Could not find localconfig.vdf. Ensure Steam is installed and you have logged in at least once."
    
    return True, "Success! Launch options updated. Backups created as .vdf.bak"

# --- GUI CODE ---
def start_gui():
    try:
        import tkinter as tk
        from tkinter import messagebox
    except (ImportError, Exception):
        print("Tkinter/Graphics initialization failed. Falling back to CLI.")
        run_cli()
        return

    root = tk.Tk()
    root.title(SCRIPT_NAME)
    root.geometry("400x350")

    tk.Label(root, text=SCRIPT_NAME, font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(root, text=DESCRIPTION, wraplength=350).pack(pady=5)

    gamemode_var = tk.BooleanVar(value=True)
    mangohud_var = tk.BooleanVar(value=True)
    gamescope_var = tk.BooleanVar(value=False)
    replace_var = tk.BooleanVar(value=False)

    tk.Checkbutton(root, text="Enable GameMode (gamemoderun)", variable=gamemode_var).pack(anchor="w", padx=50)
    tk.Checkbutton(root, text="Enable MangoHud (Performance Overlay)", variable=mangohud_var).pack(anchor="w", padx=50)
    tk.Checkbutton(root, text="Enable Gamescope (Micro-compositor)", variable=gamescope_var).pack(anchor="w", padx=50)
    tk.Separator(root, orient='horizontal').pack(fill='x', pady=10, padx=20)
    tk.Checkbutton(root, text="Overwrite existing launch options?", variable=replace_var).pack(anchor="w", padx=50)

    def on_run():
        options = {
            'gamemode': gamemode_var.get(),
            'mangohud': mangohud_var.get(),
            'gamescope': gamescope_var.get(),
            'replace': replace_var.get()
        }
        success, message = run_optimizer(options)
        if success:
            messagebox.showinfo("Done", message)
        else:
            messagebox.showerror("Error", message)

    tk.Button(root, text="Apply to All Games", command=on_run, bg="#1793d1", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10).pack(pady=20)

    root.mainloop()

def run_cli():
    print(f"--- {SCRIPT_NAME} ---")
    if is_steam_running():
        print("ERROR: Steam is running. Please close it first.")
        return

    print("Options:")
    gm = input("Enable GameMode? (Y/n): ").lower() != 'n'
    mh = input("Enable MangoHud? (Y/n): ").lower() != 'n'
    gs = input("Enable Gamescope? (y/N): ").lower() == 'y'
    rp = input("Overwrite existing options? (y/N): ").lower() == 'y'

    options = {'gamemode': gm, 'mangohud': mh, 'gamescope': gs, 'replace': rp}
    success, message = run_optimizer(options)
    print(message)

if __name__ == "__main__":
    # Check for --cli flag or lack of DISPLAY
    if "--cli" in sys.argv or "DISPLAY" not in os.environ:
        run_cli()
    else:
        start_gui()
