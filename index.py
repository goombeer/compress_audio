import pathlib
import subprocess
import math
from fastapi import FastAPI

from pydub import AudioSegment


app = FastAPI()

@app.get("/")
def index():
    return {"Hello": "World"}

@app.post("/")
def index():
    original_file = pathlib.Path("sample.mp4")

    audio_file = pathlib.Path("./audio").with_suffix(original_file.suffix)

    subprocess.run(["ffmpeg", "-i", str(original_file)
        , "-codec:a", "copy", "-vn", str(audio_file)])

    TARGET_FILE_SIZE = 25000000

    print(f"{audio_file.stat().st_size=}")
    if audio_file.stat().st_size > TARGET_FILE_SIZE:
        print("This file needs to be converted.")
        
    audio_segment = AudioSegment.from_file(str(audio_file))

    audio_length_sec = len(audio_segment)/1000

    target_kbps = int(math.floor(TARGET_FILE_SIZE * 8 / audio_length_sec / 1000 * 0.95))

    if target_kbps < 8:
        assert f"{target_kbps=} is not supported."

    converted_file = pathlib.Path("./converted").with_suffix(".mp4")

    subprocess.run(["ffmpeg", "-i", str(audio_file)
        , "-codec:a", "aac", "-ar", "16000", "-ac", "1", "-b:a", f"{target_kbps}k"
        , str(converted_file)])
    return converted_file