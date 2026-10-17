# Your recorded voice for home calls

Hume's API shuts down on 2026-11-13. Home goal calls and the starting lineup
now play in Josh's own recorded voice, joined from 40 short clips recorded on
2026-10-15. Away goals still play from the Hume pieces.

## What plays when

**Settings → Announcer → "Home goals + lineup voice"** has two choices:

- **My recordings**: the call is joined from your clips. If a
  clip is missing (for example a new player, or a renamed one), that call
  falls back to Hume, the same way it did before.
- **Hume** (the default since 2026-10-17): the Hume cache, unchanged. Nothing
  was deleted, so switching back is instant. Josh switched back because the
  joined car takes sounded off; he'll re-record on a new mic.

The goal dialog shows **🎙 Your voice — plays offline** when a call will use
your recordings.

## The clips

They live in `~/.hockey_music/voice/josh/`, outside the repo, because they
contain players' names.

| File | Line |
|---|---|
| `A1`–`A3` | "Patriots GOAL!!" (three takes; a goal picks one at random) |
| `A4`–`A7` | "Scored by", "Assisted by", "and", "Unassisted!" |
| `A8` | "Now, please welcome your Patriots!" |
| `B1`–`B17` | "Number 7, Alexander Mellen!", landing: scorer, last assist, lineup |
| `C1`–`C17` | "number 7, Alexander Mellen", rising: first of two assists |

`manifest.json` maps each spoken line to its file(s). A line's key is the exact
text `announcements.home_goal_pieces()` and `lineup_sequence()` produce, so a
roster name or nickname change orphans that player's clips. That's on purpose:
the clip says the old name.

The other files there: `takes/` (every take, untouched), `takes.json`
(which take was picked), `listen.html` (compare takes), `joined/` (calls
already assembled), `tools/` (the one-off scripts that split and leveled the
recording).

Clips are leveled to match the Hume cache's loudness, so home and away calls
come out at the same volume.

## Adding a player or re-recording a line

Record the two lines for the player ("Number N, Name!" landing, then "number
N, Name…" rising), each said twice, in a Voice Memo. Use the same spot and
energy as the original session. Hand it to Claude to split, level and add to
the manifest. The scripts in `tools/` show how the first batch was done; they
aren't a polished command.

## Not covered

- **Players with a position** in the roster: the lineup line becomes
  "Number 7, C, Name!", which has no clip, so that player's lineup line uses Hume.
- **Numbers not on the roster**: no recording exists, so those calls use Hume.
- **Final score**: still Hume (skipped on purpose for now).
