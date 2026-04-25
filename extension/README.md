# Extension Bridge MVP

This folder contains the Phase 11 extension bridge skeleton:

- `manifest.json` (MV3)
- `content-script.js` (field detection + mapping request + in-tab fill + telemetry)
- `background.js` (bridge context/session handling + telemetry fan-out)
- `popup.html` / `popup.js` (trigger "Execute fill in browser tab")
- `options.html` / `options.js` (configure web app origin)

## Load locally

1. Open Chromium extensions page (`chrome://extensions`).
2. Enable Developer mode.
3. Load unpacked extension from this `extension/` folder.
4. Open the web app and log in.
5. Open a job application tab and click **Execute fill in browser tab** from popup.

## Security notes

- Auth token bridge context is stored in `chrome.storage.session` (not persistent local storage).
- Telemetry payloads are non-secret and can be persisted in `chrome.storage.local`.
- The web app sync message is restricted to same-window origin and bridge source tags.
