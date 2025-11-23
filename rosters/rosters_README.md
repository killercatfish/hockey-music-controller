# Team Rosters

This directory contains CSV files with player roster information for automatic name lookup in PA announcements.

## File Format

CSV files with format: `number,FirstName LastName`

**Example (`patriots_roster_2025.csv`):**
```csv
5,Hugo Brown
7,Alexander Mellen
9,Brant Friedholm
10,Cale Kulig
11,Kyler Harris
```

## Rules

- **No header row** - Start directly with player data
- **Comma-separated** - Number first, then full name
- **Numbers as strings** - Use `7` not `07` (unless your jerseys say 07)
- **Full names** - Use complete names for best announcements

## Usage

1. Edit `patriots_roster_2025.csv` to match your current team
2. Launch the Hockey Music Controller
3. Player names automatically appear in PA announcements

**Example announcement:**
```
"Patriots GOAL!! Scored by number 7, Alexander Mellen, assisted by 10 and 5!"
```

## Multiple Teams

You can create separate roster files for different teams:

```
rosters/
├── patriots_roster_2025.csv      ← Home team
├── opponents_blue_devils.csv     ← Opponent 1
└── opponents_warriors.csv         ← Opponent 2
```

To use a different roster, modify the code or create a UI selector.

## Updates

**Good news:** Roster changes take effect immediately!

- Edit the CSV file anytime
- Save it
- Next announcement uses updated roster
- **No restart needed!**

## Troubleshooting

### Names Not Appearing

Check the console output when launching:
```
✅ Loaded 18 players from roster  ← Working!
⚠️  Roster file not found          ← Need to create/fix file
```

### Wrong Name

- Verify jersey number in CSV matches exactly
- Remember: `7` and `07` are different!
- Check for typos in player names

### File Not Found

Make sure file is at: `rosters/patriots_roster_2025.csv`

```bash
# Check if file exists
ls -la rosters/

# Show contents
cat rosters/patriots_roster_2025.csv
```

## Season Updates

### Start of New Season

1. Copy last season's file:
   ```bash
   cp rosters/patriots_roster_2025.csv rosters/patriots_roster_2026.csv
   ```

2. Edit the new file with current players

3. Update the default path in code (or keep 2025 filename)

### Mid-Season Changes

Just edit the CSV file directly:
- Add new players at the end
- Update player names if needed
- Remove players who left (or keep for records)

---

**See full documentation:** `docs/ROSTER_INTEGRATION_COMPLETE.md`
