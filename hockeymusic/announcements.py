"""Announcement copy.

Every announcement string in the app is built here. The preview panes call the
exact same functions the announcer does, so what you read is what the crowd
hears -- the old build had two separate string builders that had drifted apart.
"""


def _who(number, roster):
    """'number 7, Alexander Mellen' -- or just 'number 7' if not on the roster."""
    number = str(number).strip().lstrip("#")
    name = roster.display_name(number) if roster else None
    return f"number {number}, {name}" if name else f"number {number}"


def _assist_phrase(assists, roster, excited):
    """Join up to two assists into a phrase, using names when we have them."""
    named = [_who(a, roster) for a in assists if a and str(a).strip()]
    bang = "!" if excited else "."
    if len(named) >= 2:
        return f" Assisted by {named[0]} and {named[1]}{bang}"
    if len(named) == 1:
        return f" Assisted by {named[0]}{bang}"
    return f" Unassisted{bang}"


def goal(team, scorer, assists=(), roster=None, team_name="Patriots"):
    """The goal call. Home goals get energy; away goals stay flat and neutral."""
    if team.lower() == "home":
        text = f"{team_name} GOAL!! Scored by {_who(scorer, roster)}!"
        return text + _assist_phrase(assists, roster, excited=True)

    # Visiting goals: announce the number only -- we don't carry their roster.
    number = str(scorer).strip().lstrip("#")
    text = f"Goal scored by number {number}"
    named = [str(a).strip().lstrip("#") for a in assists if a and str(a).strip()]
    if len(named) >= 2:
        return f"{text}, assisted by number {named[0]} and number {named[1]}."
    if len(named) == 1:
        return f"{text}, assisted by number {named[0]}."
    return f"{text}, unassisted."


# Jersey numbers a visiting player can wear. "00" is real in youth hockey.
AWAY_NUMBERS = ["0", "00"] + [str(n) for n in range(1, 100)]


def away_goal_pieces(scorer, assists=()):
    """The away goal call as short lines, each rendered once and joined at the rink.

    Every combination of scorer and assists would be about a million lines, so
    each number is rendered twice instead: "number 12," with the voice rising
    (mid-sentence) and "number 12." falling (the end). Read together the pieces
    say exactly what goal("away", ...) says, minus a comma or two; the test
    holds them to it. Returns None if any number isn't a renderable jersey.
    """
    numbers = [str(scorer).strip().lstrip("#")]
    numbers += [str(a).strip().lstrip("#") for a in assists if a and str(a).strip()]
    if any(n not in AWAY_NUMBERS for n in numbers):
        return None
    scorer, assists = numbers[0], numbers[1:3]
    pieces = ["Goal scored by", f"number {scorer},"]
    if len(assists) == 2:
        return pieces + ["assisted by", f"number {assists[0]},", "and",
                         f"number {assists[1]}."]
    if len(assists) == 1:
        return pieces + ["assisted by", f"number {assists[0]}."]
    return pieces + ["unassisted."]


def away_piece_manifest():
    """(cache_key, text) for every away-goal piece: 4 phrases + 2 per number."""
    items = [(f"away_{t.rstrip('.').replace(' ', '_')}", t)
             for t in ("Goal scored by", "assisted by", "and", "unassisted.")]
    items += [(f"away_mid_{n}", f"number {n},") for n in AWAY_NUMBERS]
    items += [(f"away_end_{n}", f"number {n}.") for n in AWAY_NUMBERS]
    return items


def player_called(number, name, last=True):
    """A player as a recorded piece: 'Number 7, Alexander Mellen!' to land a
    sentence, 'number 7, Alexander Mellen' (voice rising) when more follows.
    No name (not on the roster): just 'Number 23!' / 'number 23'."""
    who = f"{number}, {name}" if name else f"{number}"
    return f"Number {who}!" if last else f"number {who}"


def home_goal_pieces(scorer, assists=(), roster=None, team_name="Patriots"):
    """The home goal call as recorded pieces, joined at the rink.

    Each rostered player is recorded twice (landing and rising), plus a few
    phrases. Read together they say what goal("home", ...) says; the test holds
    them to it. A number not on the roster is called by number alone, the same
    as goal() does; only the Hume pieces cover those (hume_home_piece_manifest).
    Returns None if a number isn't a jersey number at all.
    """
    numbers = [str(scorer).strip().lstrip("#")]
    numbers += [str(a).strip().lstrip("#") for a in assists if a and str(a).strip()]
    names = [roster.display_name(n) if roster else None for n in numbers]
    if any(not name and n not in AWAY_NUMBERS for n, name in zip(numbers, names)):
        return None
    called = list(zip(numbers, names))[:3]
    pieces = [f"{team_name} GOAL!!", "Scored by", player_called(*called[0])]
    if len(called) == 3:
        return pieces + ["Assisted by", player_called(*called[1], last=False), "and",
                         player_called(*called[2])]
    if len(called) == 2:
        return pieces + ["Assisted by", player_called(*called[1])]
    return pieces + ["Unassisted!"]


def home_piece_manifest(roster, team_name="Patriots"):
    """Every line the recorded home voice needs: phrases + two per player."""
    items = [f"{team_name} GOAL!!", "Scored by", "Assisted by", "and", "Unassisted!",
             lineup_intro(team_name)]
    for p in roster.sorted_players():
        items += [player_called(p.number, p.display_name),
                  player_called(p.number, p.display_name, last=False)]
    return items


def hume_home_piece_manifest(roster, team_name="Patriots"):
    """(cache_key, text) for the home goal call in Hume pieces: the recorded
    voice's lines plus every jersey number on its own. Joined at the rink, they
    cover the two-assist calls (too many to render whole) and a player who
    isn't on the roster yet."""
    items = [(f"home_piece_{i}", t)
             for i, t in enumerate(home_piece_manifest(roster, team_name))]
    for n in AWAY_NUMBERS:
        items += [(f"home_end_{n}", player_called(n, None)),
                  (f"home_mid_{n}", player_called(n, None, last=False))]
    return items


def visiting_goal(visiting_team, scorer, assists=(), roster=None):
    """A visiting goal when we DO have their roster (photo of the game sheet).
    Same flat tone as the nameless version, but with the name."""
    text = f"{visiting_team} goal, scored by {_who(scorer, roster)}."
    return text + _assist_phrase(assists, roster, excited=False)


def final_score(home_score, visiting_team, visiting_score, team_name="Patriots"):
    return (f"Final score: {team_name} {home_score}, "
            f"{visiting_team} {visiting_score}")


def lineup_intro(team_name="Patriots"):
    return f"Now, please welcome your {team_name}!"


def lineup_player(player):
    """One player in the starting-lineup rundown."""
    position = f"{player.position}, " if player.position else ""
    return f"Number {player.number}, {position}{player.display_name}!"


def lineup_sequence(roster, team_name="Patriots"):
    """(cache_key, text) pairs for the full lineup announcement."""
    items = [("lineup_intro", lineup_intro(team_name))]
    for p in roster.sorted_players():
        items.append((f"lineup_{p.number}", lineup_player(p)))
    return items


PRERENDER_SCOPES = {
    "lineup": "Starting lineup only",
    "basic": "Lineup + every unassisted goal call",
    "full": "Lineup + goal calls with each single assist",
    "away": "Away goal pieces (any number, any assists)",
    "home_pieces": "Home goal pieces (two-assist calls, numbers not on the roster)",
}


def prerender_manifest(roster, team_name="Patriots", scope="basic"):
    """(cache_key, text) pairs worth rendering before you leave for the rink.

    Rink wifi is unreliable, so anything cached to disk plays instantly and
    offline. Scope trades render time and API spend for coverage:

      lineup -- N+1 lines
      basic  -- N+1 lineup, plus N unassisted goal calls
      full   -- adds N*(N-1) single-assist calls (the common case in a game)
      away   -- the ~206 away-goal pieces; no roster needed
      home_pieces -- ~240 home pieces, joined for any call not cached whole

    Anything not cached still synthesises live, so a smaller scope only costs
    you latency on the rarer calls.
    """
    if scope == "away":
        return away_piece_manifest()
    if scope == "home_pieces":
        return hume_home_piece_manifest(roster, team_name)
    items = list(lineup_sequence(roster, team_name))
    if scope == "lineup":
        return items

    players = roster.sorted_players()
    for scorer in players:
        items.append((f"goal_{scorer.number}",
                      goal("home", scorer.number, (), roster, team_name)))

    if scope == "full":
        for scorer in players:
            for assist in players:
                if assist.number == scorer.number:
                    continue
                items.append((
                    f"goal_{scorer.number}_a{assist.number}",
                    goal("home", scorer.number, (assist.number,), roster, team_name),
                ))

    return items
