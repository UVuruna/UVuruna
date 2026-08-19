# BUILD — build & release rules

For installable desktop/mobile apps. Websites and pure libraries do not use this
pipeline. Full procedure: `howto/ship.md`.

## The Release Law (owner verdict 2026-08-19)

1. **"Build" means the installer on GitHub Releases** — the thing any user can
   download. A file in `dist/` is HALF a job; a turn that stops there has not
   done what he asked. · `gate.py stop` blocks a turn where a build ran and no
   release went out.
2. **No build starts without his word.** His word once in a session covers that
   session, including a conditional one ("kad završiš sve, uradi build"). ·
   `gate.py pre` blocks `build.py`, `pyinstaller`, `makensis`,
   `gradlew assemble|bundle`, `dotnet publish`, `msbuild /t:Publish`,
   `gh release create|upload` until any owner message of the session says
   `build · release · bild · bilduj · bill · rilis · objavi · apk`. Reading
   about the build (`grep`, `sed`, `cat`) is never a build.
3. **Then it runs to the end, in one go, without asking.** Build → verify →
   **emulator smoke (Android, owner decree 2026-08-20: headless AVD, install
   Success + process alive after launch + 0 FATAL in logcat + a screenshot the
   agent OPENED; the one thing it cannot prove is a Play Protect verdict —
   Google cloud heuristics — so say that instead of claiming it)** →
   push → tag → `gh release create`. No confirmation between the steps, no
   second question, no report that stops at "BUILD COMPLETE".
4. **Nobody raises the subject before he does.** No `## BUILD & RELEASE?`
   heading, no standing question at the end of a turn, no reminder. He says
   when he wants it. A change that is worth shipping waits in the repo.
5. **Sub-agents and parallel agents never build.** Build is the main session's
   job, at the end, once. · `gate.py pre` (a sub-agent transcript never gets
   permission).

Self-update inside applications is unchanged; only WHO decides to publish
changed. History → `history/release-law.md`.

## When he says build

1. Version comes from the single version source (`setup/app_info.json`), bumped
   per the constitution's commit convention; tag is `v{version}`; an existing
   tag is never re-released.
2. `python setup/build.py` runs the seven steps: SVG→ICO · version info from
   `app_info.json` + root `company.json` · PyInstaller `--onedir --windowed` ·
   sign the exe · NSIS installer · **sign the installer too** · verify.
3. **Step 7 verify is fail-closed** — every earlier step can fail silently, so
   `verify_build()` asserts on the OUTPUT and exits 1 unless the exe's
   `CompanyName` matches `company.json`, its `FileVersion` carries the project
   version, and BOTH exe and installer are signed when a cert is configured.
4. Release only what THIS session built and verified: `git push origin HEAD` →
   `git tag v{version}` → `git push origin v{version}` →
   `gh release create v{version} "dist/{Project}_Setup.exe" --title "v{version}"
   --notes "$(git log --oneline {prev_tag}..HEAD)"`.
5. Hidden projects never reach GitHub — they build, they do not release. A
   project with no repo yet builds; creating the repo is his call.

## Metadata and certificate

- `setup/app_info.json` (version, name, description, exe/installer names) +
  root `company.json` (company, developer, copyright) — never duplicated per
  project; `copyright_year` is bumped once a year, in the first build of it.
- `assets/logo.svg` is required (optional `logo-setup.svg` for the wizard), with
  a copy at root `logos/{Project}.svg`.
- One-time per project: `python setup/create_cert.py` → self-signed 5-year cert
  in `setup/cert/` (gitignored — back it up externally).

## Self-update (owner decree 2026-07-22)

Every installable app checks the LATEST GitHub release at startup and OFFERS an
in-app update; `None` is a normal result (up to date, disabled, dev checkout,
any network failure) and is logged at info, never raised. The check runs off the
UI path; config `update: { "repo": "<owner>/<repo>", "check": true }`. Ecosystem
apps update downhill: only the hub touches the internet. Reference
implementations: `Applications/VibeCoder/server/updates.py`,
`Gadgets/Ultra Vivid/core/updates.py`.
