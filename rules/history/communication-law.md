# Communication with the owner — the story

History file — moved out of the rulebooks by the 2026-08-18 rework.
Agents doing tasks do not read this; whoever writes a rule does.

<a id="communication"></a>

## Communication with the Owner (owner decree 2026-08-02)

Born from a real breakdown: an agent pasted raw Mermaid into chat (the owner's
interface shows diagram source as unrendered garbage) and asked three one-line
questions with zero explanation — total mutual incomprehension, a session spent
on apologies instead of progress. Both patterns are now banned and enforced.

1. **A visual is OBLIGATORY, and it must render in the owner's eyes — LAW.**
   Presenting an algorithm, a GUI element, or a config-file structure ALWAYS
   carries a visual representation next to the detailed prose walkthrough
   (numbered steps, full sentences, in Serbian) — visuals are the default,
   never a rarity to be avoided. The MEDIUM scales with complexity:
   - **Simple** → a Unicode box-drawing / ASCII sketch directly in the chat
     message (plain text renders as-is in every interface — this is what
     "rendered normally" for the owner before).
   - **Complex** → a RENDERED page the owner opens: an Artifact or an HTML
     file — real diagram, not source.
   - **A rendered page commits to ONE explicit color scheme — LAW (owner
     2026-08-03).** Born from a real breakdown: a proposal page styled with
     adaptive light/dark theme tokens (`prefers-color-scheme` media queries /
     host theme stamping) rendered as white-on-white garbage in the artifact
     viewer — the host displayed the light palette inside a dark shell. A
     rendered page NEVER relies on the viewer's theme detection: it declares
     one scheme (dark, matching the owner's environment, unless he asks
     otherwise) and sets background AND text color together, explicitly, on
     the page body — never inheriting either half of the pair from the host.
   - **NEVER** Mermaid/graphviz source pasted into a chat message — the
     owner's interface shows it as raw code garbage. Diagram source lives only
     inside doc FILES (`__flow/`, per [Docs Rules](../DOCS.md)), where viewers
     render it.
2. **Detailed questions only — LAW.** Every question to the owner is a full
   block: (a) context — what the agent is working on and where the decision
   arises, (b) the question itself in complete sentences, (c) why it matters
   and what depends on the answer, (d) the options with their concrete
   consequences, (e) the agent's recommendation. FORBIDDEN: enumerated
   one-liners — "(1) ok? (2) ok? (3) ok? — give me a YES". A question the owner
   cannot understand without asking back is a defect, not a question.
3. **Pictures arrive as LINKS, grouped by topic — LAW (owner decree
   2026-08-08).** When the owner is shown images — above all for a visual
   decision — every image name is a CLICKABLE link and the message also
   links the FOLDER that groups them; he clicks, he does not hunt a file
   tree by hand. The folder is a TOPIC folder whose name says what was
   being worked on (`shots/decision-dark-theme/` — see
   [GUI → Zubi v2](../GUI.md#zubi-v2)). A visual question with no picture, no
   page and no link is not a question he can answer, and does not end a
   turn.
   **A link that opens nothing is not a link — LAW (owner decree
   2026-08-13).** Born from a real failure: an agent wrote
   `[plain_vs_upscaler.png](plain_vs_upscaler.png)`, the guard saw brackets
   and passed it, and the owner's click did nothing — the file lived four
   folders deeper. "Clickable" is a fact about the OWNER'S CLICK, not about
   markdown syntax. So every image and folder target is:
   - a path **relative to the monorepo root** (`u:/Coding/UVuruna`, the
     folder his editor has open) — `Applications/Foo/.claude/shots/topic/
     plain_vs_upscaler.png` — or a full absolute path; **never** a bare file
     name and never a path relative to the subfolder the agent happened to
     be standing in;
   - written with **forward slashes**, outside backticks (a path in
     backticks is text, not a link);
   - **verified to exist on disk** before the message is sent — the agent
     that wrote the file knows its real path and has no excuse for guessing.
   The folder link ends in `/` and points at the topic folder itself.
   — **GATE**, `rules/hooks/communication_guard.py` (Stop): every image or
   folder target in the turn is resolved from the monorepo root, and a
   target that does not exist blocks the turn.
4. **A page that PROPOSES carries a BALLOT — LAW (owner decree 2026-08-10).**
   Born from a real habit: the owner was opening proposal pages in a screenshot
   gallery, drawing green circles and red crosses over them by hand, and typing
   his comments beside the picture — because the page gave him no way to
   answer inside itself. From now on, ANY rendered page whose purpose is to let
   the owner choose (naming options, GUI variants, algorithm alternatives,
   design directions) is not a poster, it is a BALLOT:
   - **Every proposal is selectable.** One tick box per option, and the card
     shows visibly that it is picked. Alternatives that exclude each other sit
     in a group where the tick moves; options that can be combined are freely
     multi-selected — the owner routinely wants *two* of the four variants.
   - **Every proposal has its own comment field** directly under it. His
     corrections are almost always attached to ONE option ("this halo, but the
     glow inside instead of outside"), and a single comment box at the end
     loses which one he meant.
   - **The page ends with a ballot block**: a large free-text field for
     instructions that no option covers, a **Copy verdict** button, and a
     plain-text verdict box. The button assembles CHOSEN / NOT CHOSEN BUT
     COMMENTED / INSTRUCTIONS as plain text and puts it on the clipboard — the
     owner pastes ONE message into the chat and the round continues. Selections
     survive a page reload (`localStorage`), because he reads long pages in
     more than one sitting.
   - **The reference implementation is `rules/templates/decision_page.html`** —
     copy it, keep the `data-option` / `data-group` / `#ballot` contract, and
     replace only the content. The fixed dark scheme of point 1 still applies.
   - A proposal page shipped without the ballot is an unfinished deliverable:
     it forces the owner into the screenshot-and-marker workflow this rule
     exists to end.
5. **Teeth:** `rules/hooks/communication_guard.py`, wired MACHINE-WIDE in
   `~/.claude/settings.json` (applies in every project, no per-project
   migration). The Stop hook blocks ending any turn whose chat text contains
   diagram source or a terse enumerated ask; the PreToolUse hook on
   AskUserQuestion blocks questions below minimum substance (question ≥ 100
   chars of context, every option description ≥ 40 chars of consequence); the
   PreToolUse hook on Artifact (added 2026-08-04, after the white-on-white
   law of 2026-08-03 was violated AGAIN by an agent following generic
   artifact styling guidance over this rulebook) blocks publishing any page
   whose stylesheet contains adaptive theme tokens (`prefers-color-scheme`,
   `data-theme`) or that never sets its own background — the page must carry
   ONE fixed explicit scheme. Since 2026-08-08 the Stop hook also blocks a
   turn that names image files as bare text instead of links, and a
   `WAITING_ON_OWNER` turn that asks a visual question with no image, page
   or link in it.
   Honesty note: the hook measures substance by length — whether an
   explanation actually EXPLAINS stays on session discipline and the owner's
   review.

---

