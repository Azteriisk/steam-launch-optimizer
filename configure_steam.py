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

def update_vdf(file_path, new_options_str, replace_existing=False):
    print(f"Processing: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error: {e}")
        return

    apps_match = re.search(r'([ \t]*"apps"\s*\{)(.*?)(\n[ \t]*\}\n[ \t]*"LastPlayedTimesSyncTime"|\n[ \t]{3,4}\}(?=\n))', content, re.IGNORECASE | re.DOTALL)
    if not apps_match:
        return

    prefix, apps_block, suffix = apps_match.groups()
    app_pattern = re.compile(r'([ \t]*"\d+"\s*\{)(.*?)(\n[ \t]*\})', re.DOTALL)
    
    def modify_app_block(match):
        start, inner, end = match.groups()
        if '"LaunchOptions"' in inner:
            if replace_existing:
                inner = re.sub(r'("LaunchOptions"[ \t]+)"[^"]*"', rf'\1"{new_options_str}"', inner)
            else:
                existing_match = re.search(r'"LaunchOptions"[ \t]+"([^"]*)"', inner)
                if existing_match:
                    existing = existing_match.group(1)
                    base_existing = existing.replace("%command%", "").strip()
                    if new_options_str.replace("%command%", "").strip() not in base_existing:
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
            update_vdf(vdf_file, launch_str, options.get('replace', False))
    
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
    tk.Checkbutton(root, text="Gamescope (Micro-compositor)", variable=gs_v).pack(anchor="w", padx=60)
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
