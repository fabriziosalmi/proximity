#!/usr/bin/env python3
"""
Professional Sound Generator for Proximity Platform
Generates futuristic, control-room aesthetic sound effects
"""

import numpy as np
import wave
import struct

SAMPLE_RATE = 44100

def generate_sine_wave(frequency, duration, amplitude=0.3):
    """Generate a sine wave"""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    return amplitude * np.sin(2 * np.pi * frequency * t)

def apply_envelope(audio, attack=0.01, decay=0.05, sustain_level=0.7, release=0.1):
    """Apply ADSR envelope to audio"""
    length = len(audio)
    envelope = np.ones(length)
    
    # Attack
    attack_samples = int(SAMPLE_RATE * attack)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    
    # Decay
    decay_samples = int(SAMPLE_RATE * decay)
    if decay_samples > 0:
        decay_end = attack_samples + decay_samples
        envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_samples)
    
    # Release
    release_samples = int(SAMPLE_RATE * release)
    if release_samples > 0 and release_samples < length:
        envelope[-release_samples:] = np.linspace(sustain_level, 0, release_samples)
    
    return audio * envelope

def save_wav(filename, audio):
    """Save audio to WAV file"""
    # Normalize
    audio = audio / np.max(np.abs(audio))
    # Convert to 16-bit PCM
    audio = (audio * 32767).astype(np.int16)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio.tobytes())

def generate_success():
    """Generate success sound - crystalline, positive chime"""
    duration = 0.35
    # Two harmonious tones
    tone1 = generate_sine_wave(800, duration, 0.3)
    tone2 = generate_sine_wave(1200, duration, 0.2)
    tone3 = generate_sine_wave(1600, duration, 0.15)
    
    audio = tone1 + tone2 + tone3
    audio = apply_envelope(audio, attack=0.005, decay=0.03, sustain_level=0.6, release=0.15)
    
    save_wav('success.wav', audio)
    print("✓ Generated success.wav")

def generate_error():
    """Generate error sound - low frequency, non-harsh denial"""
    duration = 0.3
    # Lower frequency buzz
    tone1 = generate_sine_wave(180, duration, 0.4)
    tone2 = generate_sine_wave(140, duration, 0.3)
    
    audio = tone1 + tone2
    audio = apply_envelope(audio, attack=0.01, decay=0.05, sustain_level=0.7, release=0.12)
    
    save_wav('error.wav', audio)
    print("✓ Generated error.wav")

def generate_click():
    """Generate click sound - subtle mechanical/digital blip"""
    duration = 0.08
    # High frequency short blip
    tone = generate_sine_wave(1400, duration, 0.25)
    
    audio = apply_envelope(tone, attack=0.002, decay=0.01, sustain_level=0.5, release=0.03)
    
    save_wav('click.wav', audio)
    print("✓ Generated click.wav")

def generate_notification():
    """Generate notification sound - gentle attention grabber"""
    duration = 0.4
    # Soft rising tone
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    freq_sweep = 600 + 300 * np.sin(2 * np.pi * 3 * t)
    audio = 0.25 * np.sin(2 * np.pi * freq_sweep * t / SAMPLE_RATE)
    
    audio = apply_envelope(audio, attack=0.02, decay=0.05, sustain_level=0.6, release=0.15)
    
    save_wav('notification.wav', audio)
    print("✓ Generated notification.wav")

def generate_deploy_start():
    """Generate deploy start sound - power-up/activation"""
    duration = 0.5
    # Rising frequency sweep (power-up feel)
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    freq_start = 300
    freq_end = 900
    frequency = freq_start + (freq_end - freq_start) * (t / duration)
    
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Add harmonic
    audio += 0.15 * np.sin(2 * np.pi * frequency * 2 * t)
    
    audio = apply_envelope(audio, attack=0.01, decay=0.08, sustain_level=0.7, release=0.2)
    
    save_wav('deploy_start.wav', audio)
    print("✓ Generated deploy_start.wav")

def generate_deployment_loop():
    """Generate seamless dub-techno ambient loop for deployment progress"""
    duration = 8.0  # 8-second loop
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    
    # Deep bass pulse (55Hz - A1 note, dub-techno characteristic)
    bass_freq = 55
    bass = 0.4 * np.sin(2 * np.pi * bass_freq * t)
    
    # Add subtle bass movement (slow LFO)
    lfo_bass = 0.15 * np.sin(2 * np.pi * 0.25 * t)
    bass = bass * (1 + lfo_bass)
    
    # Ambient pad layers
    pad1 = 0.15 * np.sin(2 * np.pi * 220 * t)  # A3
    pad2 = 0.12 * np.sin(2 * np.pi * 330 * t)  # E4
    pad3 = 0.10 * np.sin(2 * np.pi * 440 * t)  # A4
    
    # Breathing effect on pads
    pad_lfo = np.sin(2 * np.pi * 0.125 * t)
    pads = (pad1 + pad2 + pad3) * (0.5 + 0.5 * pad_lfo)
    
    # Subtle hi-hat texture
    hihat = np.random.normal(0, 0.02, len(t))
    hihat = np.convolve(hihat, np.array([0.1, 0.2, 0.4, 0.2, 0.1]), mode='same')
    
    # Combine layers
    audio = bass + pads + hihat
    
    # Seamless loop crossfade
    fade_samples = int(SAMPLE_RATE * 0.5)
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out
    
    # Moderate volume for ambient background
    audio = audio / np.max(np.abs(audio)) * 0.6
    
    save_wav('deployment_loop.wav', audio)
    print("✓ Generated deployment_loop.wav")

def generate_explosion():
    """Generate explosion/completion sound for deployment success"""
    duration = 1.2
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    
    # Impact transient (white noise burst)
    impact_duration = 0.05
    impact_samples = int(SAMPLE_RATE * impact_duration)
    impact = np.random.normal(0, 1, impact_samples)
    impact = impact * np.exp(-10 * np.linspace(0, 1, impact_samples))
    
    # Bass drop (descending sweep)
    bass_t = t[impact_samples:]
    bass_freq = np.linspace(200, 40, len(bass_t))
    bass_phase = np.cumsum(2 * np.pi * bass_freq / SAMPLE_RATE)
    bass = 0.8 * np.sin(bass_phase)
    sub_bass = 0.4 * np.sin(bass_phase * 0.5)
    
    bass_full = bass + sub_bass
    bass_with_impact = np.concatenate([impact * 0.5, bass_full])
    
    # Harmonic sweep (celebration)
    harm_freq = np.linspace(800, 400, len(t))
    harm_phase = np.cumsum(2 * np.pi * harm_freq / SAMPLE_RATE)
    harmonic = 0.3 * np.sin(harm_phase)
    
    # Bright shimmer
    shimmer_freq = np.linspace(2000, 1000, len(t))
    shimmer_phase = np.cumsum(2 * np.pi * shimmer_freq / SAMPLE_RATE)
    shimmer = 0.15 * np.sin(shimmer_phase)
    
    # Combine
    audio = bass_with_impact[:len(t)] + harmonic + shimmer
    
    # Exponential decay envelope
    envelope = np.exp(-3 * t)
    audio = audio * envelope
    
    # Simple reverb tail
    reverb_delay = int(SAMPLE_RATE * 0.08)
    reverb = np.zeros(len(audio) + reverb_delay)
    reverb[:len(audio)] = audio
    reverb[reverb_delay:] += audio * 0.3
    
    audio = reverb / np.max(np.abs(reverb))
    
    save_wav('explosion.wav', audio)
    print("✓ Generated explosion.wav")

if __name__ == '__main__':
    print("🎵 Generating Professional Sound Effects for Proximity...")
    print("=" * 60)
    
    generate_success()
    generate_error()
    generate_click()
    generate_notification()
    generate_deploy_start()
    generate_deployment_loop()
    generate_explosion()
    
    print("=" * 60)
    print("✅ All sound effects generated successfully!")
    print("\nSound files created:")
    print("  • success.wav         - Positive completion chime")
    print("  • error.wav           - Low frequency denial tone")
    print("  • click.wav           - Subtle digital blip")
    print("  • notification.wav    - Gentle attention sound")
    print("  • deploy_start.wav    - Power-up activation")
    print("  • deployment_loop.wav - Dub-techno ambient (8s seamless)")
    print("  • explosion.wav       - Deployment completion impact")
