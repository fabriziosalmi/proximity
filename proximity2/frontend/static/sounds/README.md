# Proximity 2.0 - Sound Effects

This directory contains the UI sound effects for Proximity 2.0. The sounds should be:
- **Subtle and minimal** (< 1 second duration)
- **Futuristic/sci-fi aesthetic** (think command deck, spacecraft console)
- **Low volume by default** (user can adjust)
- **Small file size** (preferably < 50KB each)

## Required Sound Files

### 1. `click.wav`
- **Trigger**: Generic button clicks, tab switches
- **Style**: Soft mechanical click, like pressing a physical switch
- **Duration**: ~100ms
- **Volume**: Subtle

### 2. `deploy-start.wav`
- **Trigger**: Starting an app deployment
- **Style**: Ascending tone, "powering up" sound
- **Duration**: ~500ms
- **Volume**: Medium

### 3. `success.wav`
- **Trigger**: Successful operations (deploy complete, backup complete)
- **Style**: Pleasant confirmation beep, 2-3 ascending tones
- **Duration**: ~300ms
- **Volume**: Medium

### 4. `error.wav`
- **Trigger**: Failed operations, errors
- **Style**: Low warning tone, not alarming but clear
- **Duration**: ~200ms
- **Volume**: Medium-loud

### 5. `flip.wav`
- **Trigger**: Card flip animation (3D flip)
- **Style**: Soft "whoosh" or mechanical flip sound
- **Duration**: ~300ms
- **Volume**: Subtle

### 6. `backup-create.wav`
- **Trigger**: Creating a backup
- **Style**: Data processing sound, soft electronic chirp
- **Duration**: ~400ms
- **Volume**: Medium

### 7. `restore.wav`
- **Trigger**: Restoring from backup
- **Style**: Data loading sound, ascending beeps
- **Duration**: ~500ms
- **Volume**: Medium

## Sound Generation Tools

You can use these free tools to generate sci-fi sounds:

1. **SFXR / BFXR** (http://www.bfxr.net/)
   - Web-based retro sound effect generator
   - Great for sci-fi UI sounds

2. **Audacity** (https://www.audacityteam.org/)
   - Free audio editor
   - Can generate tones and add effects

3. **Free Sound Libraries**:
   - https://freesound.org/ (search for "ui click", "beep", "interface")
   - https://mixkit.co/free-sound-effects/
   - Filter by CC0/Public Domain licenses

## Placeholder Silence

Until proper sounds are added, the SoundService will gracefully handle missing files with console warnings. The app will function normally without sounds.

## Implementation Notes

- Sounds are preloaded on app initialization
- Users can disable/enable sounds via localStorage
- Volume is adjustable (0.0 - 1.0, default 0.3)
- All sound playback errors are caught to prevent app crashes
