# Steam Launch Options Optimizer 🚀

A simple Python-based tool to automatically apply performance-enhancing launch options to all your Steam games at once. No more manually editing every game in your library!

## Features

-   **One-Click Optimization:** Add `gamemoderun`, `mangohud`, and `gamescope` to all your games.
-   **Graphical Interface:** Easy-to-use GUI for selecting exactly which options you want.
-   **Smart Appending:** Doesn't overwrite your existing launch options (unless you ask it to). It intelligently appends new tools and ensures `%command%` remains at the end.
-   **Dependency Helper:** Automatically detects if you're missing `gamemode` or `mangohud` and offers to install them (supports Arch, CachyOS, Fedora, Ubuntu, and Debian).
-   **Safety First:**
    -   Checks if Steam is running to prevent file corruption.
    -   Automatically creates `.bak` backups of your configuration before making any changes.
-   **CLI Fallback:** Works in the terminal for servers or users who prefer the command line.

## Prerequisites

The script requires **Python 3** and **Tkinter** (for the GUI). You can install them with:

-   **Arch / CachyOS:** `sudo pacman -S python tk`
-   **Fedora:** `sudo dnf install python3 tkinter`
-   **Ubuntu / Debian:** `sudo apt install python3 python3-tk`

## How to Use

1.  **Download the script:**
    ```bash
    wget https://raw.githubusercontent.com/Azteriisk/steam-launch-optimizer/main/configure_steam.py
    ```

2.  **Run it:**
    ```bash
    python3 configure_steam.py
    ```

3.  **Select your options** and click **Apply to All Games**.

4.  **Restart Steam** to see the changes.

## Options Explained

-   **GameMode (`gamemoderun`):** Tells your CPU to stay in "high performance" mode while the game is running.
-   **MangoHud:** A powerful performance overlay that shows FPS, temperatures, and frame times.
-   **Gamescope:** Valve's micro-compositor that allows for better upscaling (FSR), HDR support, and improved frame pacing.

## Contributing

Feel free to open issues or submit pull requests for new features (like more distro support or additional launch tools).

---
*Created with 🐧 for the Linux gaming community.*
