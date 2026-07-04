# Publishing Orbit Panel to winget

Once published, users install with:

```powershell
winget install JinmyeongKim.OrbitPanel
```

## One-time prerequisites

- A GitHub release with the built `Orbit Panel.exe` attached
  (GitHub renames the asset to `Orbit.Panel.exe` in the download URL).
- The [winget CLI](https://learn.microsoft.com/windows/package-manager/winget/) for local validation.

## Release steps

1. Build the EXE:

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools/build_release.ps1
   ```

2. Create a GitHub release tagged `v<VERSION>` (e.g. `v1.2.0`) and upload `dist/Orbit Panel.exe`.

3. Generate the filled manifests (computes the SHA256 automatically):

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools/make_winget_manifests.ps1 -Version 1.2.0
   ```

4. Validate locally:

   ```powershell
   winget validate --manifest packaging/winget/out/1.2.0
   ```

5. Submit to [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs):
   copy the folder to `manifests/j/JinmyeongKim/OrbitPanel/1.2.0/` in a fork and open a PR.

   Alternatively, let `wingetcreate` handle the fork and PR:

   ```powershell
   wingetcreate submit packaging/winget/out/1.2.0
   ```

## Notes

- The package uses the `portable` installer type: winget copies the EXE into its
  packages directory and exposes an `orbit-panel` alias on PATH. Runtime data still
  lives in `%AppData%\Orbit Panel`, so upgrades keep user config.
- For each new release, repeat steps 1-5 with the new version number.
