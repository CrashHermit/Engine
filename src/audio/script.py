from __future__ import annotations

import miniaudio

# Get file info
info = miniaudio.get_file_info("src/audio/samples/music.mp3")
print(
    f"Playing: {info.nchannels} channels, {info.sample_rate} Hz, {info.duration:.1f}s"
)

# Stream and play
stream = miniaudio.stream_file("src/audio/samples/music.mp3")
with miniaudio.PlaybackDevice() as device:
    device.start(stream)
    input("Playing... press Enter to stop")

# Get the audio data
audio_data = miniaudio.read_file("src/audio/samples/music.mp3")
print(audio_data)
