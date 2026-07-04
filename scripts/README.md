# Orbit Panel Script Automation

Orbit Panel can run a Python script file per item.

For browser automation scripts, install Playwright first:

```bash
pip install playwright
python -m playwright install chromium
```

Recommended starting point:

- keep your automation scripts under `scripts/`
- import `orbit_context.py`
- use `load_context()` to read the current item
- use `build_logger()` so logs land in the Orbit Panel log directory

Useful card settings:

- `Run Mode = Target Only`
  target only, no automation
- `Run Mode = Target Then Script`
  open the target first, then run the script
- `Run Mode = Script Only`
  let the Python script own the full workflow

Most web login automations should use `Script Only` so the script controls browser startup and selectors end to end.

## Naver example

Use `scripts/examples/naver_login.py` as a starting point for Naver automation.

Recommended card setup:

- `Type = URL`
- `Target = https://www.naver.com/`
- `Script Type = Python File`
- `Script = scripts/examples/naver_login.py`
- `Run Mode = Script Only`

Recommended environment variables:

- `ORBIT_NAVER_ID`
- `ORBIT_NAVER_PASSWORD`
- `ORBIT_NAVER_KEEP_OPEN=true`

The script opens the Naver login page directly when credentials are present, fills `#id` and `#pw`, clicks the current login button `#log.login`, then moves to the final target URL.
