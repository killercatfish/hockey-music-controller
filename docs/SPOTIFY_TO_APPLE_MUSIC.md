# Converting Spotify Playlists to Apple Music

If you have existing hockey game playlists on Spotify and want to use them with the Hockey Music Controller, you'll need to transfer them to Apple Music first. This guide shows you the easiest way to do that.

## Why Transfer Playlists?

The Hockey Music Controller uses AppleScript to control the macOS Music app (formerly iTunes). It can only access songs that are in your Apple Music library. If you have playlists on Spotify that you want to use during games, you need to transfer them to Apple Music first.

## The Problem with Manual Transfer

Simply searching for songs by name and artist doesn't always work reliably because:
- Different versions (remastered, live, remixes) have similar names
- Artist names might be formatted differently
- Featured artists can cause mismatches
- Some songs might not be available on both platforms

## The Solution: ISRC Matching

**ISRC (International Standard Recording Code)** is a unique identifier assigned to each recording. Both Spotify and Apple Music use ISRC codes, which means you can get exact matches when transferring playlists.

Services like TuneMyMusic use ISRC codes under the hood to match tracks between platforms with high accuracy.

## Recommended Method: TuneMyMusic

[TuneMyMusic](https://www.tunemymusic.com/) is a free service that handles playlist transfers between streaming platforms using ISRC matching.

### Steps:

1. **Go to TuneMyMusic**
   - Visit: https://www.tunemymusic.com/

2. **Choose Source (Spotify)**
   - Click "Let's start"
   - Select "Spotify" as your source
   - Click "Connect" and authorize TuneMyMusic to access your Spotify playlists
   - OR paste a Spotify playlist URL directly

3. **Select Your Playlist**
   - Browse your Spotify playlists or use the URL you pasted
   - Select the playlist you want to transfer
   - Review the track list

4. **Choose Destination (Apple Music)**
   - Click "Choose destination"
   - Select "Apple Music"
   - Click "Connect" and authorize TuneMyMusic to access Apple Music

5. **Transfer**
   - Click "Start moving my music"
   - Wait for the transfer to complete (usually takes 1-2 minutes)
   - TuneMyMusic will show you how many tracks were successfully matched

6. **Verify in Apple Music**
   - Open the Music app on your Mac
   - Check that your new playlist appears in the sidebar
   - Verify the songs are there and play correctly

### Success Rates

TuneMyMusic typically achieves 95%+ match rates using ISRC codes. Any songs that can't be matched will be shown in the results so you can add them manually if needed.

## Alternative: Soundiiz

[Soundiiz](https://soundiiz.com/) is another service that offers similar functionality, with both free and premium tiers. It also uses ISRC matching for accurate transfers.

## After Transfer

Once your playlist is in Apple Music:

1. The Hockey Music Controller will be able to see and control these songs
2. You can create multiple playlists for different game situations:
   - Stoppage time high-energy tracks
   - Zamboni music
   - Pre-game warmup
   - Goal celebration songs
   - Power play music

3. Use the Hockey Music Controller's playlist management features to organize and shuffle your game music

## Exporting Spotify Playlists

If you want to export a Spotify playlist for other purposes:

1. Use **Exportify** (https://exportify.net/)
2. Connect your Spotify account
3. Click "Export" on the playlist you want
4. Downloads as a CSV file with full track metadata including ISRC codes

This CSV can be useful for:
- Backing up your playlists
- Sharing track lists with others
- Creating documentation of your game music library

## Technical Details: Why ISRC Works

The [ISRC (International Standard Recording Code)](https://en.wikipedia.org/wiki/International_Standard_Recording_Code) was established in 1986 to uniquely identify sound recordings. Key points:

- Each recording gets a unique ISRC code
- Remixes, edits, and live versions get different ISRCs
- Remastered versions may keep the original ISRC if changes are minor
- Both Spotify and Apple Music APIs support ISRC lookups

This makes ISRC the most reliable way to match tracks across platforms.

## Troubleshooting

**Songs didn't transfer?**
- Some songs may not be available on Apple Music
- Check if there's an alternative version (remastered, deluxe edition, etc.)
- Search manually in Apple Music and add to your playlist

**Playlist not showing in Music app?**
- Refresh your Apple Music library (File → Library → Update Cloud Library)
- Check that you're signed in to Apple Music
- Restart the Music app

**Wrong version of a song transferred?**
- Sometimes multiple recordings share metadata
- Manually replace with the correct version in your Apple Music playlist

## Reference

For more technical details on ISRC matching between Spotify and Apple Music:
- [How to Match Tracks Between Spotify and Apple Music](https://leemartin.medium.com/how-to-match-tracks-between-spotify-and-apple-music-2d6b6159957e) by Lee Martin

---

Once your playlists are in Apple Music, you're ready to use the Hockey Music Controller for your games! 🏒
