# desktopUI

A premium, modular top status bar and interactive widget popup control center designed for Linux Wayland desktop environments, optimized for **Hyprland** and built using **Python 3**, **GTK 3**, and the **Fabric** library.

`desktopUI` brings a clean, modern aesthetic with high customizability, dynamic theme compilation, and a fully reactive UI components system.

---

## 🚀 Features

- **Modular Desktop Bar (`UserModuleBar`)**:
  - **Left Section**: Quick-access User Letter Button, Time/Calendar Widget, and MPRIS Media Controller.
  - **Center Section**: Hyprland Workspaces indicator with dynamic styling.
  - **Right Section**: Keyboard Language Layout selector, interactive Wi-Fi Monitor, Battery Status Pill, and Settings Button.
- **Interactive Control Center Popups**:
  - **User Popup**: Premium user profile drawer.
  - **Settings Popup**: Quick-toggle panel integrating wallpapers, weather info, and system actions.
- **Dynamic SCSS/CSS Styling**: Live stylesheet reloading and automated compiling using Sass/CSS utilities.
- **Singleton Services Architecture**: Decoupled, thread-safe backends (WiFi, MPRIS, Workspace Apps, Weather, Wallpapers, and event-driven Hyprland Displays) built on a `SingletonService` pattern to optimize resource consumption and listen to dynamic event streams.

---

## 🛠️ Prerequisites & Dependencies

Most dependencies are system-level packages for PyGObject and GTK 3.

### System Dependencies (Arch Linux / Hyprland example)
Ensure you have the following system libraries and tools installed:
```bash
sudo pacman -S gtk3 gobject-introspection python-gobject libdbus mpris-playerctl networkmanager hyprland swww matugen
```

### Python Environment
Create a virtual environment and install the required Python packages (including the `fabric` library):
```bash
# Clone the repository
git clone https://github.com/yourusername/desktopUI.git
cd desktopUI

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Configuration & Environment Variables

`desktopUI` reads several environment variables to adjust behavior and integrate with your specific configuration:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `DESKTOPUI_TERMINAL` / `TERMINAL` | Terminal emulator executable used when launching interactive Wi-Fi controls. | Auto-detected |
| `DESKTOPUI_WEATHER_LOCATION` | Custom location string for the weather widget service. | Auto-detected |
| `DESKTOPUI_SKIP_MATUGEN` | Set to any non-empty value to skip generating themes via Matugen. | Disabled |
| `DESKTOPUI_MATUGEN_CONFIG` | Path to a custom Matugen configuration file. | Config default |
| `DESKTOPUI_MATUGEN_MODE` | Color generation mode for Matugen (`light` or `dark`). | `dark` |
| `DESKTOPUI_SWWW_ARGS` | Additional argument strings to pass to the `swww` wallpaper daemon. | None |
| `DESKTOPUI_DEBUG_BLOCKING` | Set to `1`, `true`, or `yes` to enable main-thread blocking diagnostics. | Disabled |

---

## 📂 Project Structure

```
desktopUI/
├── main.py              # Main entrypoint; initializes widgets & runs Fabric Application loop
├── base.py              # Contains SingletonService base class
├── requirements.txt     # Python virtual environment dependencies
├── style.css            # Compiled base stylesheet
├── colors.css           # Automatically generated Matugen color palettes
├── modules/
│   └── config.py        # Bar layout configuration, size limits, and Window classes
├── widgets/             # Individual GTK widgets (Time, Battery, WiFi, Media, Workspaces...)
├── services/            # Background services handling DBus, Hyprland states/displays, and API calls
└── utils/               # SCSS compilation engines, asset fetchers, and debugging utilities
```

---

## 🏃 Running the Application

To start the status bar, simply execute:

```bash
# Ensure your virtual environment is active
source .venv/bin/activate

# Run the bar
./main.py
```

To run in debug mode, prefix your execution:

```bash
DESKTOPUI_DEBUG_BLOCKING=true python3 main.py
```

---

## 🎨 Customizing Styles

Custom styling is written using CSS/SCSS and auto-compiled. Modify standard style sheets under the root or relevant widgets:
1. `style.css` contains the core UI tokens, borders, gradients, and font declarations.
2. If `Matugen` is installed and not skipped, changing your wallpaper will automatically extract color schemes and write them to `colors.css`.
