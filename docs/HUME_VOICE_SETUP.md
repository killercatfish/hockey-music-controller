# Hume Custom Voice Setup Guide

## What Changed

The code now properly uses your custom Hume voice by specifying `provider='CUSTOM_VOICE'`. This tells Hume's API to look for your voice in your custom voices instead of their standard voice library.

### Key Updates:

1. **Added imports:**
   ```python
   from hume.tts import PostedUtterance, PostedUtteranceVoiceWithName
   ```

2. **Updated voice specification:**
   ```python
   utterance = PostedUtterance(
       text=announcement,
       voice=PostedUtteranceVoiceWithName(
           name=HUME_VOICE_ID,      # Your custom voice ID
           provider='CUSTOM_VOICE'   # This is the critical part!
       )
   )
   ```

## How to Use Your Custom Voice

1. **Set up your `.env` file** with your custom voice ID:
   ```
   HUME_API_KEY=your_api_key_here
   HUME_VOICE_ID=9e068547-5ba4-4c8e-8e03-69282a008f04
   ```

2. **Make sure the `.env` file is in the same directory** as your Python script

3. **Run the application** - it will automatically use your custom voice for goal announcements

## Fallback Behavior

- If `HUME_VOICE_ID` is set → Uses your custom voice with `provider='CUSTOM_VOICE'`
- If `HUME_VOICE_ID` is not set → Falls back to Hume's 'Ava Song' voice with `provider='HUME_AI'`
- If Hume fails for any reason → Falls back to macOS text-to-speech

## Testing Your Voice

To test if your custom voice is working:

1. Launch the Hockey Music Controller
2. Click the "🏒 GOAL!" button
3. Enter team and scorer info
4. The announcement should play using your custom Hume voice

If you hear the announcement in your custom voice, it's working! If not, check the terminal/console for error messages.

## Common Issues

**"Voice not found" error:**
- Double-check your voice ID in the `.env` file
- Make sure the voice ID matches exactly what's shown in the Hume dashboard
- Verify the voice was successfully created in your Hume account

**"No API key" error:**
- Ensure `HUME_API_KEY` is set in your `.env` file
- The `.env` file must be in the same directory as the script

**Falls back to macOS voice:**
- Check that the `python-dotenv` package is installed: `pip install python-dotenv`
- Check that the Hume SDK is installed: `pip install hume`
