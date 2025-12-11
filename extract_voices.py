import os
import subprocess


def extract_audio(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".mp4"):
            input_path = os.path.join(input_folder, file)
            output_path = os.path.join(output_folder, file.replace(".mp4", ".wav"))
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                output_path,
            ]
            subprocess.run(cmd, shell=True)


extract_audio("videos_vf", "audio_vf")
extract_audio("videos_vo", "audio_vo")
