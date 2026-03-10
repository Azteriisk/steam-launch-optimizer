# steam-launch-optimizer

A small script to bulk-apply launch options like `gamemoderun`, `mangohud`, and `gamescope` to your entire Steam library. Instead of right-clicking every single game to add these, you can just run this once.

## What it does

- **GUI or CLI:** Use the simple window if you're on desktop, or run it with `--cli` if you're in a terminal.
- **Doesn't break things:** It won't overwrite your existing launch options; it just appends the new ones and keeps `%command%` at the end where it belongs.
- **Safety checks:** It'll warn you if Steam is still open (to avoid file conflicts) and creates `.bak` backups automatically.
- **Dependency help:** It can try to install `gamemode` or `mangohud` for you if they're missing (supports Arch, Fedora, and Debian/Ubuntu).

## Getting Started

### Prerequisites
You'll need Python 3 and Tkinter installed for the GUI to work.

- **Arch:** `sudo pacman -S python tk`
- **Fedora:** `sudo dnf install python3 tkinter`
- **Ubuntu / Debian:** `sudo apt install python3 python3-tk`

### Usage
1. Grab the script:
   ```bash
   wget https://raw.githubusercontent.com/Azteriisk/steam-launch-optimizer/main/configure_steam.py
   ```
2. Run it:
   ```bash
   python3 configure_steam.py
   ```
3. Pick your tools and hit **Apply**. 
4. **Restart Steam** for the changes to take effect.

## Why these options?

- **GameMode:** Forces your CPU into high-performance mode while you play.
- **MangoHud:** Shows FPS and system stats in a customizable overlay.
- **Gamescope:** Valve's compositor for better upscaling (FSR) and frame pacing.

## Contributing
If you want to add support for other distros or more launch tools, feel free to open a PR.
