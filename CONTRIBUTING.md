# Contributing

Thanks for considering a contribution. This project has one non-negotiable rule, and everything else is
ordinary Python work.

## The one rule: never report success you cannot prove

Every connection entry returns a `ConnectResult`. Setting `ok=True` or `live_verified=True` requires a
round trip that the target program actually answered:

- COM: read a real property back (`app.Version`, `GetConnectionStatus()`) — construction is not
  connection. pyautocad and pythonnet both construct lazily.
- MCP: `initialize` **and** `list_tools` must both succeed against a discovered port.
- TCP/REST: validate the response, not just the status code — a 200 with an empty body is not a
  connection.
- Never map "did not raise" to "connected". Never map a returned error string to success.

PRs that add a probe which passes because nothing threw will be rejected, however small the diff.

## Adding a product adapter

1. Add an entry to `CATALOG` in `src/esab/adapters/hosts.py`, with `software`, `kind`, `entry`,
   `evidence` and the live-verification status.
2. Implement `connect_<product>()` in the same file. Return a diagnostic `ConnectResult` on failure —
   the specific error (`REGDB_E_CLASSNOTREG`, errno 10061, missing environment variable), not
   "connection failed".
3. Inject anything skills need into the executor environment via `src/esab/runtime/builtins.py`.
4. Add a skill under `src/esab/data/skills/<Product>-Link/` with `SKILL.md`, referenced only against the
   dependency versions actually declared in `pyproject.toml`. Documenting an API your dependency does not
   have is how the AutoCAD skill broke.
5. Run the audit and paste the result into your PR:

   ```bash
   python tools/adapter_audit.py
   ```

If your product was not installed on your machine, say so in the PR. A graded "requires on-site
re-check" is an acceptable result; a confident `ok=True` from an unverified probe is not.

## Development setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest tests -q
```

Windows-only extras (`comtypes`, `pywin32`, `pyautocad`, `pythonnet`) are only needed for the COM and
.NET adapters; `pip install -e ".[test,win32,tekla]"` on Windows.

Tests must pass on macOS and Linux too. Mechanical-only tests are not an excuse for a red suite — mark
platform-specific tests with `pytest.mark.skipif`.

## Style

- Python 3.11+, `from __future__ import annotations`, type hints on public functions.
- Comments and identifiers in English. User-facing strings and skill content may be Chinese; keep them
  consistent within a file rather than half-translating.
- No new runtime dependency without justification — the base install is `mcp` and nothing else.
- Do not commit `.db` indexes or API dumps larger than the existing ones without discussing it first.

## Commits and PRs

- One logical change per commit; imperative subject line (`fix: resolve GstarCAD ProgID before connect`).
- Describe the failing behaviour you observed, how you reproduced it, and the evidence that it is fixed.
- New adapters: include the audit output.

## Reporting bugs

Include: OS and Python version, target software and its version, the `ConnectResult` you got (with
`evidence`), and whether `tools/adapter_audit.py` reproduces it. A bug report that says "connection
fails" without the diagnostic message cannot be acted on.

## License

Contributions are accepted under the MIT license, see [LICENSE](LICENSE).
