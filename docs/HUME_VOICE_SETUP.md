# Hume Voice Setup

The PA announcer uses a **custom Hume AI voice** — one you record yourself, so
the goal calls sound like a real arena announcer rather than a robot.

---

## 1. Create the voice

1. Sign up at [hume.ai](https://www.hume.ai).
2. Create a **custom voice** and record the sample prompts. Record them the way
   you want goals called: energy, projection, arena cadence.
3. Note the **voice name** exactly as it appears in the dashboard.
4. Copy your **API key**.

---

## 2. Store the key

Preferred — outside the repo, so it can never be committed and so a `.app`
bundle you hand to another parent doesn't carry your key:

```bash
mkdir -p ~/.hockey_music
cat > ~/.hockey_music/.env <<'EOF'
HUME_API_KEY=your_api_key_here
HUME_VOICE_ID=Hockey Goal Announcer
EOF
```

A `.env` in the project directory also works; `~/.hockey_music/.env` wins if both
exist.

> ⚠️ `HUME_VOICE_ID` is the **voice name**, not a UUID. The app requests it with
> `provider='CUSTOM_VOICE'`, which tells Hume to look in your custom voices
> rather than its stock library.

Then install the SDK:

```bash
pip install hume python-dotenv
```

> ⚠️ Never commit `.env`. It is gitignored, but gitignore does not untrack a file
> that has already been committed. If a key lands in a commit, **rotate it** —
> scrubbing history is not enough once it's been pushed.

---

## 3. Pre-render before game day

**This is the step that matters.** Rink wifi is unreliable, and a goal call that
arrives ten seconds late is worse than none.

Open **🎙 Pre-render voice** and pick a scope:

| Scope | Lines for an 18-player roster | Covers |
|---|---|---|
| Starting lineup only | 19 | Pre-game lineup |
| Lineup + unassisted goal calls | 37 | Most common calls |
| Everything, incl. single assists | 343 | Nearly every real call |

Rendered audio goes to `~/.hockey_music/tts_cache/`. Cached lines play
**instantly, with no network at all**, and never cost another API call.

Anything not cached still synthesises live — a smaller scope only costs you
latency on the rarer calls, never the call itself.

The goal dialog tells you which state you're in before you commit:

```
⚡ Cached — plays instantly, no wifi needed
☁️ Not cached — will render from Hume (needs wifi)
```

---

## 4. Test it

1. Launch the app.
2. Press **A** (or **📢 Goal Announcement**).
3. Enter a scorer number and check the preview — that is the exact text that
   will be spoken.
4. **🎤 ANNOUNCE GOAL**.

The status line reports which path was used.

---

## Fallback behaviour

The app degrades rather than going silent:

1. **Cached audio** if the line has been rendered — instant, offline.
2. **Live Hume synthesis** otherwise (timeout in Settings → Announcer, default 20s).
3. **macOS `say`** if Hume is unreachable or the SDK isn't installed.

v2 skipped the announcement entirely when Hume failed. v3 always says something.

---

## Cache management

**Settings → Announcer** shows the cache size and has a **Clear cache** button.

Editing announcement wording in `hockeymusic/announcements.py` invalidates every
cached line for it — the cache is keyed on a hash of the voice and the exact
text. Re-render after any copy change.

---

## Troubleshooting

**"Voice not found"** — `HUME_VOICE_ID` must match the dashboard voice name
exactly, including spaces and capitalisation.

**Falls back to the macOS voice** — check `pip install hume python-dotenv`, then
confirm the key is loading: the goal dialog header shows either the Hume voice
name or the reason it's unavailable.

**Announcements are slow** — they're rendering live. Pre-render them.

**Rendering fails partway** — usually the network. The pre-render dialog reports
`N failed`; just run it again, since already-cached lines are skipped.
