# The Release Law — automatic (2026-07-23) and its reversal (2026-08-18)

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="release-law"></a>

## THE RELEASE LAW (owner decree 2026-07-23, SHOUTED)

**Every session that produces a successful build of an installable app MUST
immediately create a GIT RELEASE. Do NOT ask — this is standing, durable
authorization.** The owner installs and updates ONLY through the official GitHub
release (the self-update path below); local `dist/` is a build by-product, never
the deliverable. A build that is not released is invisible to the update
mechanism and therefore useless.

- Build → verify → tag → push → `gh release create`, in ONE unbroken flow.
  Never release an artifact the current session did not just build and verify.
- Version comes from the single version source, bumped per the commit
  convention (zero-padded patch); tag is `v{version}`; never re-release an
  existing tag — bump first. Release notes = commits since the previous tag.
- Scope: every installable app WITH a GitHub repo. No repo yet → still build;
  creating the repo is the owner's call (surface it, don't stall). Hidden
  projects (never on GitHub) are the only ones that skip the release.
- This is outward-facing publishing the owner has PERMANENTLY authorized — the
  general "confirm outward-facing actions" guidance does not apply to this one
  decreed action.

---


---

## The reversal (owner verdict 2026-08-18)

The owner reversed the standing authorization above on his rework ballot
(`.claude/reports/agent-rework-2026-08-17.html`, chapter 5, accepted whole).
No build and no release starts without his explicit word IN THAT SESSION; a
session that changed an installable app's code ends with the heading
`## BUILD & RELEASE?` — the list of changes and the exact command — and stops.
Sub-agents and parallel agents never build; build is the main session's job,
at the end, once. Consequence he accepted knowingly: a session he does not
answer leaves no installer, and the ledger carries a `[?] BUILD` task so the
question is not lost. Self-update inside applications is unchanged — that is
product; only WHO decides to publish changed.

The rule text now lives in `rules/BUILD.md`; the procedure in
`rules/howto/ship.md`.
