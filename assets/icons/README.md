# Icons

- `orbit_panel.ico`: Windows app / PyInstaller icon for Orbit Panel
- `orbit_panel.png`: preview export of the app icon artwork

Regenerate both files with:

```bash
python tools/generate_app_icon.py
```

For PyInstaller packaging, point `--icon` to `assets/icons/orbit_panel.ico`.
