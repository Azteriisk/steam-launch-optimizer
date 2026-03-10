# steam-launch-optimizer

A small script to bulk-apply launch options like `gamemoderun`, `mangohud`, and `gamescope` to your entire Steam library. Instead of right-clicking every single game to add these, you can just run this once.

## Functionality

- **Interactive:** Running the script without flags will ask you which options to enable.
- **Flags:** You can skip the prompts by passing flags (e.g., `--gamemode --mangohud`).
- **Safe updates:** It appends to your existing options and ensures `%command%` stays at the end. It also creates `.bak` backups of your config files.
- **Auto-install:** Can attempt to install missing tools via your package manager (Arch, Fedora, Debian/Ubuntu).

## Getting Started

### Prerequisites
Python 3 is required. For the GUI, you'll need Tkinter:

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
3. (Optional) Run directly with flags:
   ```bash
   python3 configure_steam.py --gamemode --mangohud --replace
   ```
4. **Restart Steam** for changes to take effect.

> **Note:** Games must be launched at least once for Steam to create the necessary configuration entries. If a newly installed game isn't being updated, launch it once and then run the script again.

## Options

- **GameMode:** CPU governor optimizations for gaming.
- **MangoHud:** Performance and hardware monitoring overlay.
- **Gamescope:** Valve's micro-compositor for upscaling and frame pacing.

## Contributing
Open a PR if you want to add more distro support or additional tools.
