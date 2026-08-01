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
}


def prerender_manifest(roster, team_name="Patriots", scope="basic"):
    """(cache_key, text) pairs worth rendering before you leave for the rink.

    Rink wifi is unreliable, so anything cached to disk plays instantly and
    offline. Scope trades render time and API spend for coverage:

      lineup -- N+1 lines
      basic  -- N+1 lineup, plus N unassisted goal calls
      full   -- adds N*(N-1) single-assist calls (the common case in a game)

    Anything not cached still synthesises live, so a smaller scope only costs
    you latency on the rarer calls.
    """
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
