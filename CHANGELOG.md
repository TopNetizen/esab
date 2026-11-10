# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org).

## [0.4.0a1] — 2026-11-10

First public release. Renamed from the internal `struct-agent-bridge` working name to **ESAB**
(Engineering Software Agent Bridge).

### Added

- Product resolution layer for CAD: `esab_shim/cad.py` probes `AutoCAD.Application` and falls back to
  `GstarCAD.Application` / `GCAD.Application` / `ZWCAD.Application` / `BricsCAD.Application`, redirecting
  requests for the generic ProgID to whichever product is actually installed. Every connect performs a
  real COM round trip (`app.Version`) before returning.
- `connect_cad()` injected into the `python_executor` environment, so skills can call it directly.
- Adapter audit tooling: `tools/adapter_audit.py` (calls all 15 connection entries in isolated
  subprocesses, 45 s timeout) and `tools/false_positive_probe.py` (four controlled experiments that try
  to make the bridge report a false success).
- `docs/cad-integration-report.md`: end-to-end GstarCAD 2027 test plus a full false-connection audit of
  all 15 adapters.

### Fixed

- **CAD false success.** `connect_cad()` returned `ok=True` whenever pyautocad's constructor did not
  raise, but pyautocad 0.2.0 constructs lazily — `_app` stays `None` until first access, so "connected"
  was reported with no CAD present at all.
- **`connect_official()` treated an error string as success.** A returned `str` is now a failure signal,
  never a live connection.
- **PlantS wrapper reported `connected: True` from a process name alone**, with no instance and no MCP
  service behind it. Now goes through the same discovery plus MCP handshake as the runtime path, and
  raises instead of guessing.
- **`connect_pkpm_calc()` returned `None` silently** when the expected object was missing. It now raises
  and prints the keys that `details` actually has.
- **Rhino preferred `EnsureDispatch`**, which spawns a new process while the message claimed an existing
  instance was attached. Attach (`GetActiveObject`) is now tried first, and the message distinguishes
  "attached" from "started".
- **`AutoCAD-Link/SKILL.md` mismatched pyautocad 0.2.0.** It documented `acad.connection`,
  `acad.constants` and custom exception classes that do not exist in the declared dependency. Rewritten
  against the real interface, with the four genuine error classes documented.
- **Worker transport broke on non-UTF-8 Windows locales.** The persistent Python worker spoke
  line-delimited JSON over pipes opened with the locale default encoding, so on an English Windows
  install (cp1252) any Chinese diagnostic or skill body raised `UnicodeDecodeError` in the parent and
  surfaced as "worker exited before returning a result". Both sides now pin UTF-8
  (`PYTHONIOENCODING`, `encoding="utf-8"`, `reconfigure()` in the worker). Reported by CI on
  `windows-latest`; reproducible on POSIX with `LANG=C`.
- **`_connect_csi` dropped its diagnostics when `comtypes` was missing**, returning a message without
  the helper ProgID and object name the other branches include.

### Changed

- Project, package and CLI renamed: `struct-agent-bridge` → `esab`, `struct_agent_bridge` → `esab`,
  `structbridge_shim` → `esab_shim`, `struct-bridge` → `esab`, `STRUCT_BRIDGE_*` → `ESAB_*`,
  MCP tool prefix `struct_bridge_` → `esab_`.
- Runtime MCP server identity is now `esab-runtime`, and both servers report the package version instead
  of hard-coded strings.

### Known issues

- `PKPM-Link/SKILL.md` imports `RunPKPMAnalyse` from `pkpm_calc.py`, where it does not exist —
  `ImportError` at that line.
- SAP2000 / ETABS, STAAD.Pro and MIDAS connection criteria could not be falsified on the reference
  machine (software not installed). Re-check steps are in the integration report, §9.4.
