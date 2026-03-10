import os
import re
import glob
import subprocess
import sys
import argparse

# --- CONFIGURATION & TEXT ---
SCRIPT_NAME = "steam-launch-optimizer"
DESCRIPTION = "Bulk-apply launch options like gamemoderun, mangohud, and gamescope to your Steam library."

def is_steam_running():
    try:
        output = subprocess.check_output(["pgrep", "steam"]).decode().strip()
        return len(output) > 0
    except subprocess.CalledProcessError:
        return False

def get_distro():
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.split("=")[1].strip().strip('"')
    except:
        pass
    return "unknown"

def install_dependencies(tools):
    distro = get_distro()
    pkg_map = {
        "arch": {"gamemode": "gamemode", "mangohud": "mangohud", "gamescope": "gamescope", "lib32-gamemode": "lib32-gamemode", "lib32-mangohud": "lib32-mangohud"},
        "fedora": {"gamemode": "gamemode", "mangohud": "mangohud", "gamescope": "gamescope"},
        "ubuntu": {"gamemode": "gamemode", "mangohud": "mangohud", "gamescope": "gamescope"},
        "debian": {"gamemode": "gamemode", "mangohud": "mangohud", "gamescope": "gamescope"},
        "cachyos": {"gamemode": "gamemode", "mangohud": "mangohud", "gamescope": "gamescope", "lib32-gamemode": "lib32-gamemode", "lib32-mangohud": "lib32-mangohud"}
    }
    
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
            if t in pkg_map[distro]: pkgs.append(pkg_map[distro][t])
            if f"lib32-{t}" in pkg_map[distro]: pkgs.append(pkg_map[distro][f"lib32-{t}"])
        install_cmd.extend(pkgs)
    elif distro == "fedora":
        install_cmd = ["sudo", "dnf", "install"] + [pkg_map[distro][t] for t in tools if t in pkg_map[distro]]
    elif distro in ["ubuntu", "debian"]:
        install_cmd = ["sudo", "apt", "install"] + [pkg_map[distro][t] for t in tools if t in pkg_map[distro]]

    if not install_cmd or len(install_cmd) <= 3:
        return False

    print(f"Running: {' '.join(install_cmd)}")
    try:
        subprocess.run(install_cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_tools(selected_tools):
    missing = []
    for tool in selected_tools:
        cmd = "gamemoderun" if tool == "gamemode" else tool
        if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
            missing.append(tool)
    return missing

def find_block_range(content, block_name, start_pos=0):
    """Finds the start and end indices of a named block in a VDF file using brace counting."""
    # We must match exactly the key name with quotes
    pattern = re.compile(rf'"{block_name}"\s*\{{', re.IGNORECASE)
    match = pattern.search(content, start_pos)
    if not match:
        return None
    
    start_index = match.start()
    brace_start = content.find('{', start_index)
    
    count = 0
    for i in range(brace_start, len(content)):
        if content[i] == '{':
            count += 1
        elif content[i] == '}':
            count -= 1
            if count == 0:
                return (start_index, i + 1)
    return None

def update_vdf(file_path, new_options_str, replace_existing=False):
    print(f"Processing: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: {e}")
        return

    # To find the REAL apps block, we must traverse the structure:
    # Software -> Valve -> Steam -> apps
    soft_range = find_block_range(content, "Software")
    if not soft_range:
        print(f"Could not find 'Software' block in {file_path}")
        return
    
    valve_range = find_block_range(content, "Valve", soft_range[0])
    if not valve_range:
        print(f"Could not find 'Valve' block in {file_path}")
        return
        
    steam_range = find_block_range(content, "Steam", valve_range[0])
    if not steam_range:
        print(f"Could not find 'Steam' block in {file_path}")
        return
        
    apps_range = find_block_range(content, "apps", steam_range[0])
    if not apps_range:
        print(f"Could not find 'apps' block in {file_path}")
        return

    apps_start, apps_end = apps_range
    # Skip the "apps" { part
    apps_header_end = content.find('{', apps_start) + 1
    apps_body = content[apps_header_end : apps_end - 1]
    
    new_apps_body = ""
    current_pos = 0
    # Process each AppID block inside the apps body
    while True:
        # Match "AppID" {
        match = re.search(r'"(\d+)"\s*\{', apps_body[current_pos:])
        if not match:
            new_apps_body += apps_body[current_pos:]
            break
        
        # Add everything before the match
        new_apps_body += apps_body[current_pos : current_pos + match.start()]
        
        appid_start = current_pos + match.start()
        brace_start = apps_body.find('{', appid_start)
        
        # Brace count to find end of AppID block
        count = 0
        appid_end = -1
        for i in range(brace_start, len(apps_body)):
            if apps_body[i] == '{':
                count += 1
            elif apps_body[i] == '}':
                count -= 1
                if count == 0:
                    appid_end = i + 1
                    break
        
        if appid_end == -1:
            new_apps_body += apps_body[appid_start:]
            break
            
        appid_block = apps_body[appid_start:appid_end]
        
        # 1. Strip ALL existing LaunchOptions entries in this AppID block
        appid_block = re.sub(r'[ \t]*"LaunchOptions"[ \t]+"[^"]*"[ \t]*\n?', '', appid_block)
        
        # 2. Add the clean LaunchOptions
        last_brace_idx = appid_block.rfind('}')
        # Find indent of closing brace
        line_start = appid_block.rfind('\n', 0, last_brace_idx)
        if line_start == -1: line_start = 0
        else: line_start += 1
        
        indent = ""
        for char in appid_block[line_start:last_brace_idx]:
            if char in " \t": indent += char
            else: break
        
        inner_indent = indent + "\t"
        new_entry = f'\n{inner_indent}"LaunchOptions"\t\t"{new_options_str}"'
        # Construct updated block
        appid_block = appid_block[:last_brace_idx].rstrip() + new_entry + "\n" + indent + "}"
        
        new_apps_body += appid_block
        current_pos = appid_end

    new_content = content[:apps_header_end] + new_apps_body + content[apps_end - 1:]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def run_optimizer(options):
    if is_steam_running():
        return False, "Steam is running. Close it first to avoid file conflicts."

    selected_tools = [t for t in ['gamemode', 'mangohud', 'gamescope'] if options.get(t)]
    missing = check_tools(selected_tools)
    if missing and not install_dependencies(missing):
        return False, f"Missing: {', '.join(missing)}"

    parts = []
    if options.get('gamemode'): parts.append("gamemoderun")
    if options.get('mangohud'): parts.append("mangohud")
    if options.get('gamescope'): parts.append("gamescope --")
    parts.append("%command%")
    launch_str = " ".join(parts)

    steam_paths = [
        "~/.steam/steam/userdata/*/config/localconfig.vdf",
        "~/.local/share/Steam/userdata/*/config/localconfig.vdf",
        "~/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata/*/config/localconfig.vdf"
    ]

    found = False
    for path_pattern in steam_paths:
        for vdf_file in glob.glob(os.path.expanduser(path_pattern)):
            found = True
            os.system(f'cp "{vdf_file}" "{vdf_file}.bak"')
            update_vdf(vdf_file, launch_str, options.get('replace', True))
    
    return (True, "Success! Restart Steam to see changes.") if found else (False, "Could not find localconfig.vdf.")

def start_gui():
    try:
        import tkinter as tk
        from tkinter import messagebox
    except:
        run_cli()
        return

    root = tk.Tk()
    root.title(SCRIPT_NAME)
    root.geometry("400x320")

    tk.Label(root, text=SCRIPT_NAME, font=("Arial", 14, "bold")).pack(pady=10)
    
    gm_v = tk.BooleanVar(value=True)
    mh_v = tk.BooleanVar(value=True)
    gs_v = tk.BooleanVar(value=False)
    rp_v = tk.BooleanVar(value=False)

    tk.Checkbutton(root, text="GameMode (gamemoderun)", variable=gm_v).pack(anchor="w", padx=60)
    tk.Checkbutton(root, text="MangoHud (Performance Overlay)", variable=mh_v).pack(anchor="w", padx=60)
    tk.Checkbutton(root, text="Enable Gamescope", variable=gs_v).pack(anchor="w", padx=60)
    tk.Checkbutton(root, text="Overwrite existing options?", variable=rp_v).pack(anchor="w", padx=60, pady=(10,0))

    def on_run():
        opts = {'gamemode': gm_v.get(), 'mangohud': mh_v.get(), 'gamescope': gs_v.get(), 'replace': rp_v.get()}
        success, msg = run_optimizer(opts)
        (messagebox.showinfo if success else messagebox.showerror)("Result", msg)

    tk.Button(root, text="Apply to All Games", command=on_run, bg="#1793d1", fg="white", font=("Arial", 10, "bold"), padx=20, pady=10).pack(pady=20)
    root.mainloop()

def run_cli():
    print(f"\n--- {SCRIPT_NAME} ---")
    if is_steam_running():
        print("Error: Steam is running. Close it first.")
        return

    gm = input("Enable GameMode? (Y/n): ").lower() != 'n'
    mh = input("Enable MangoHud? (Y/n): ").lower() != 'n'
    gs = input("Enable Gamescope? (y/N): ").lower() == 'y'
    rp = input("Overwrite existing? (y/N): ").lower() == 'y'

    success, msg = run_optimizer({'gamemode': gm, 'mangohud': mh, 'gamescope': gs, 'replace': rp})
    print(msg)

if __name__ == "__main__":
    if len(sys.argv) > 1 or "DISPLAY" not in os.environ:
        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('--gamemode', action='store_true', help='Enable gamemoderun')
        parser.add_argument('--mangohud', action='store_true', help='Enable mangohud')
        parser.add_argument('--gamescope', action='store_true', help='Enable gamescope')
        parser.add_argument('--replace', action='store_true', help='Overwrite existing options')
        parser.add_argument('--cli', action='store_true', help='Force CLI mode')
        args = parser.parse_args()

        if any([args.gamemode, args.mangohud, args.gamescope]):
            success, msg = run_optimizer(vars(args))
            print(msg)
        else:
            run_cli()
    else:
        start_gui()
