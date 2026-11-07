# Cross-platform plan — Hockey Music Controller everywhere

Status: **proposal, nothing built.** Written 2026-11-07. Josh decides.

Goal: run the game-day console on Mac, Windows/PC, iPhone and Android, with
playlist generation and announcement voice generation done by a backend Josh
runs (API keys stay on the server; users may pay for it).

---

## 1. What blocks a straight port today

The current app is macOS-bound in three places, and only three:

| Today (Mac) | Why it doesn't travel | Replacement |
|---|---|---|
| AppleScript → Music.app (`music.py`) | AppleScript exists only on macOS | **MusicKit** (Apple's official SDK: JS for web, native for iOS, an Android SDK) |
| `afplay` / `say` (`announcer.py`) | macOS commands | Browser/OS audio element; device TTS (Web Speech API) as the offline fallback |
| tkinter UI (`ui/`) | Desktop-only, not on phones | One web UI (PWA), optionally wrapped for app stores |

Everything else is plain Python and moves to a backend as-is or nearly:
`announcements.py` (all copy), `hype.py` (chorus detection via LRCLIB),
`gameday.py` (disjoint per-game decks), `playlists.py` (pools, clips,
`EventDeck`, family-safe filter), `roster.py`, `config.py` migration logic.
That is roughly half the 4,500 lines, and it's the half with the ideas in it.

## 2. Recommended architecture

```
 ┌──────────────── one client codebase (TypeScript PWA) ────────────────┐
 │  Mac / PC browser   ·  iPhone  ·  Android   (+ Capacitor store builds) │
 │  Console · Goal panel · Roster · Settings · Event buttons              │
 │  MusicPlayer interface ─┬─ AppleMusicPlayer (MusicKit JS / native)     │
 │                         └─ LocalFilesPlayer (user's own MP3s)          │
 │  Announcement audio cached on-device (service worker) → works offline  │
 └───────────────────────────────┬───────────────────────────────────────┘
                                 │ HTTPS (team data, rendered audio URLs)
 ┌───────────────────────────────┴───────────────────────────────────────┐
 │  Backend: Python FastAPI, reusing hockeymusic/ modules                 │
 │  • accounts, teams, rosters, pools, clip points (Postgres)             │
 │  • announcement text = announcements.py (still the ONE source of copy) │
 │  • TTS render jobs → provider API key held here → audio in object store│
 │  • hype points (LRCLIB) and game-deck dealing                          │
 │  • billing (Stripe) — voice renders are the metered cost               │
 └────────────────────────────────────────────────────────────────────────┘
```

**Why a PWA first, not five native apps:** one codebase covers all four
platforms on day one, no app-store review to iterate, and MusicKit JS gives the
three things the console actually needs: play a specific track, seek to the clip
point (`seekToTime`, or `startTime` in `setQueue`), and set volume (for fades and
ducking). Capacitor wraps the same code into App Store / Play Store builds later.

**Invariants that carry over:**
- *All copy in one place* → server owns `announcements.py`; the client preview
  shows the text the server returns, the same text that was rendered.
- *Never block the UI* → renders are server jobs; the client only downloads files.
- *Verified seeks* → same pattern in JS: play, wait for `nowPlayingItem`, seek,
  read position back, volume held at 0 until it lands.
- *Secrets never in the repo / never in the client* → TTS key lives server-side only.
- *Track identity* → new app keys on Apple Music catalog IDs, with a one-time
  import that matches Josh's existing `"Name | Artist"` clip points (450+) to IDs.

## 3. Music sources — the hard part

| Source | Verdict |
|---|---|
| **Apple Music (MusicKit)** | Primary. Each user needs their own Apple Music subscription; Josh needs the Apple Developer Program ($99/yr) for the MusicKit token. Streams, so it needs rink wifi/cell. |
| **Local files** | Must-have second source. Works everywhere, offline, no subscription. User uploads MP3s/M4As once; cached on device. |
| **Spotify** | **Not viable for a shared app.** Since Feb/Mar 2026 Spotify Development Mode is Premium-only, one Client ID per developer, max **5 authorized users**; wider access needs Extended Quota, which reportedly requires a registered business and ~250k MAU. Fine for Josh alone, dead end for distribution. |
| **TIDAL** | Plausible later. Has official Player SDKs for web, iOS and Android (open source, OAuth per user). At the 2024 launch, web playback was **preview clips only**; full-track access for third parties is unverified. Small US user base among hockey parents. |
| **Amazon Music** | Not available. No public SDK; Web API playback needs Amazon's approval, Widevine DRM and certification. Their old device API is closed to new apps. |
| **YouTube Music** | No playback API at all. |
| **YouTube (regular embedded player)** | Real third option. The IFrame Player API plays a given video, seeks, and sets volume, on every platform. Catches: ads unless the user is signed into YouTube Premium in that browser; the player must stay visible (no background audio-only); music videos can have intros, so clip points are per video. |
| **Spotify desktop app (local control)** | Mac: Spotify's AppleScript dictionary plays a track URI, seeks and sets volume, so it can work the way Music.app does today. Windows: system media controls (SMTC) can play/pause/skip/seek what's playing; starting an exact track means opening a `spotify:` URI. Untested. iPhone: impossible. Android: partial and unreliable. |

Coverage today, all **untested**:

| | Mac | PC | iPhone | Android |
|---|---|---|---|---|
| Apple Music | yes | yes | yes | yes |
| Own files | yes | yes | yes | yes |
| YouTube (Premium) | yes | yes | yes | yes |
| Spotify desktop | yes | maybe | no | no |
| TIDAL | maybe | maybe | maybe | maybe |

**iPhone volume risk.** iOS Safari ignores a web page's attempts to set a media
element's volume (it always reads 1.0); the hardware buttons own it. Fades and
ducking for Apple Music and YouTube may therefore be impossible from a web page
on iPhone. Local files can still fade through Web Audio. Native iOS can duck
other audio while an announcement plays (`AVAudioSession` `.duckOthers`), but
native MusicKit has no app-controlled volume either. The fallback is pause instead
of fade. `docs/spike/` tests exactly this.

**"Connect your own account" is the model already.** MusicKit signs in each
user to their own Apple Music subscription. The limits above are on *the app*
(Josh's developer registration), not the user, so a user's own login doesn't
get around Spotify's 5-user cap. Spotify also allows one Development Mode
Client ID per developer, so "each user registers their own Spotify app" is the
only workaround, and it's clunky and in a grey area under Spotify's terms.

Build the player as a `MusicPlayer` interface (play-at, seek, volume, now
playing) so each service is one adapter: Apple + local files at launch, TIDAL if
full-track access checks out, Spotify if their rules ever reopen.

**Licensing — say it out loud before charging money:** Apple's media terms
limit Apple Music to personal, noncommercial use, and music played to a crowd is
a public performance that needs a venue license (ASCAP/BMI/SESAC in the US).
Most rinks hold those licenses for their PA, but the personal-subscription rule
is still a grey area. A personal tool is low-risk; *selling* an app built around
it is worth a short conversation with a lawyer, and the local-files source keeps
the product useful regardless.

## 4. Voice generation

- Hume account is gone (deleted 2026-10-22), so the cloud voice is a fresh pick:
  ElevenLabs, OpenAI TTS, Cartesia, or Hume again. Choose by a blind listen of
  the same 10 lines. Price check before committing — not verified here.
- Volume is small: a 20-player roster × ~10 lines (lineup, goal, assist,
  penalty, etc.) ≈ 200–300 lines per team per season, rendered once and cached.
  Same cache key idea as today: `sha256(voice_id | text)`.
- Paid tier = premium voices + pre-render; free tier = on-device TTS (Web Speech
  API), which needs no server and works offline.
- Josh's own recorded voice (`voice.py`) ports as "upload your own clips" —
  the joining logic moves server-side.
- Audio is pre-rendered *before* the game and stored on the device, so a dead
  rink connection never costs a goal call.

## 5. Phases

**Phase 0 — spike, 1–2 weekends. Go/no-go gate.** Built: `docs/spike/index.html`
(how to run it: `docs/spike/README.md`). A throwaway web page that:
signs into Apple Music via MusicKit JS; plays a track starting at a clip point;
fades out; ducks the music under an announcement MP3 and restores it.
Test it on iPhone Safari, Android Chrome, Windows Chrome, Mac Safari.
Known risk: Apple dev forums report audible hitches seeking in iOS WebViews,
and iOS restricts mixing two audio sources. **If ducking/seek doesn't hold up on
iPhone, the iOS build needs a native MusicKit plugin** (Swift, inside Capacitor),
which adds real work. Nothing else should be built until this answers.

**Phase 1 — backend (reuse).** FastAPI around the existing modules; Postgres;
login; teams/rosters/pools/clip points; TTS render jobs + object storage;
hype-point and game-deck endpoints. Import tool for Josh's current config.

**Phase 2 — client console (PWA).** Console, docked goal panel, event buttons
(Power Play / PK / Away Goal rotating decks), roster editor, settings, offline
audio cache. Josh runs a real game on it alongside the Mac app as backup.

**Phase 3 — stores and money.** Capacitor builds for App Store and Play Store
(Google Play is a one-time $25), Stripe billing for the voice tier.
Note: Apple requires in-app purchase for digital goods bought inside an iOS app;
selling the subscription on the web avoids that but has its own rules.

**Phase 4 — other teams.** Onboarding, multi-team accounts, support.

The Mac app stays as-is throughout; nothing here touches it.

## 6. Decisions for Josh

1. **Who is it for?** Just Patriots announcers (personal, cheap, low risk) or
   any team (product: licensing question, support, billing). Changes Phase 3–4.
2. **Music sources:** Apple Music + local files (recommended), or Apple only?
3. **Voice provider:** run a blind listen across 3 providers?
4. **Do Phase 0?** It's the cheapest way to find out whether "worth a shot" is
   worth more than a shot.

## Sources

- Spotify Development Mode changes: developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security
  and the February 2026 migration guide; TechCrunch 2026-02-06.
- MusicKit JS seek/volume: Apple developer forums threads 706264, 771715, 829729, 829734.
- Apple Media Services terms (personal, noncommercial use).
