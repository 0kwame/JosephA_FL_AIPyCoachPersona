from pathlib import Path
import sounddevice as sd
from scipy.io.wavfile import write
import pygame

class AudioService:
    """
    Service for recording and playing audio.
    """

    def __init__(self, fs: int = 16000, channels: int = 1):
        self.fs = fs
        self.channels = channels

    def record(self, filename: Path, duration: int = 10):
        """
        Record audio from microphone and save as WAV.
        """
        try:
            print(f"🎙️ Recording for {duration} seconds...")
            audio = sd.rec(int(duration * self.fs), samplerate=self.fs,
                           channels=self.channels, dtype="int16")
            sd.wait()
            write(str(filename), self.fs, audio)
            print(f"✅ Audio saved to {filename}")
            return filename
        except Exception as e:
            print(f"⚠️ Recording failed: {e}")
            return None

    def play(self, filepath: Path):
        """
        Play audio file using pygame.
        """
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(str(filepath))
            pygame.mixer.music.play()

            # Wait until playback finishes
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            print(f"▶️ Finished playing {filepath}")
        except Exception as e:
            print(f"⚠️ Could not play {filepath}: {e}")
