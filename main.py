from fastapi import FastAPI, File, UploadFile, Response
import subprocess
import math
from pydub import AudioSegment
import os

app = FastAPI()

@app.post("/convert_video_to_audio/")
async def convert_video_to_audio(video_file: UploadFile = File(...)):
    # アップロードされた動画ファイルを一時ファイルに保存
    with open("input.mp4", "wb") as buffer:
        buffer.write(await video_file.read())
    
    # 音声ファイルを抽出して、MP3形式で保存する
    audio_file = "output.mp3"
    subprocess.run(["ffmpeg", "-i", "input.mp4", "-f", "mp3", "-ab", "128k", "-maxrate", "128k", "-vn", audio_file], check=True)
    
    # 音声ファイルを読み込む
    audio_segment = AudioSegment.from_file(audio_file)
    
    # 音声ファイルの長さを取得
    audio_length_sec = len(audio_segment)/1000
    
    # 目標ビットレートを計算
    TARGET_FILE_SIZE = 25 * 1024 * 1024 # 25MB
    target_kbps = int(math.floor(TARGET_FILE_SIZE * 8 / audio_length_sec / 1000 * 0.95))
    
    # 目標ビットレートが8kbps以下の場合、エラーを返す
    if target_kbps < 8:
        return {"error": f"{target_kbps=} is not supported."}
    
    # 音声ファイルを圧縮する
    try:
        compressed_audio = subprocess.run(["ffmpeg", "-i", audio_file, "-codec:a", "aac", "-ar", "16000", "-ac", "1", "-b:a", f"{target_kbps}k", "-f", "adts", "pipe:"], check=True, capture_output=True).stdout
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.decode("utf-8")}
    
    # 一時ファイルを削除
    os.remove("input.mp4")
    os.remove(audio_file)
    
    # ファイルサイズが25MB以下かチェック
    print(f"{len(compressed_audio)=}")
    if len(compressed_audio) > TARGET_FILE_SIZE:
        return {"error": "The compressed audio file is too large. Please upload a shorter video or reduce the audio bitrate."}
    
    # レスポンスを返す
    headers = {
        "Content-Disposition": f"attachment; filename={video_file.filename.split('.')[0]}.mp3"
    }
    return Response(content=compressed_audio, media_type="audio/mp3", headers=headers)
