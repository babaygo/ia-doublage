import requests
import os
import time
import json
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

API_KEY = os.getenv("PYANNOTE_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

UPLOAD_URL = "https://api.pyannote.ai/v1/media/input"
DIARIZE_URL = "https://api.pyannote.ai/v1/diarize"

SPEAKERS_FOLDER = "speakers"
AUDIOS_FOLDER = "audios_vostr"


def upload_audio_file(input_path: str, object_key=None):
    """Upload un fichier local et retourne son URL interne (media://...)."""
    if object_key is None:
        object_key = os.path.basename(input_path).split(".")[0]

    # 1. Demander une URL pré-signée
    resp = requests.post(
        url=UPLOAD_URL,
        json={"url": f"media://{object_key}"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    presigned_url = resp.json()["url"]

    # 2. Uploader le fichier via PUT
    with open(input_path, "rb") as f:
        put_resp = requests.put(presigned_url, data=f)
        put_resp.raise_for_status()

    print(f"{input_path} uploadé avec succès !")
    return f"media://{object_key}"


def diarize(audio_urls: list[str], output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for audio_url in audio_urls:
        resp = requests.post(DIARIZE_URL, headers=HEADERS, json={"url": audio_url})
        resp.raise_for_status()
        job_id = resp.json()["jobId"]

        while True:
            job_resp = requests.get(
                f"https://api.pyannote.ai/v1/jobs/{job_id}", headers=HEADERS
            )
            job_resp.raise_for_status()
            job = job_resp.json()
            status = job["status"]

            if status in ["succeeded", "failed", "canceled"]:
                if status == "succeeded":
                    print(f"Diarisation terminée pour {audio_url}")
                    output = job["output"]

                    filename = audio_url.split("media://")[-1]
                    json_path = os.path.join(output_folder, filename + ".json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(output, indent=2))
                else:
                    print(f"Job {status} pour {audio_url}")
                break

            print(f"Job {job_id} status: {status}, attente...")
            time.sleep(15)


def json_to_rttm(json_path: str, output_folder):
    file_id = os.path.splitext(os.path.basename(json_path))[0]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(output_folder, exist_ok=True)

    rttm_path = os.path.join(output_folder, file_id + ".rttm")

    with open(rttm_path, "w", encoding="utf-8") as out:
        for seg in data["diarization"]:
            speaker = seg["speaker"]
            start = seg["start"]
            end = seg["end"]
            duration = end - start

            line = f"SPEAKER {file_id} 1 {start:.3f} {duration:.3f} <NA> <NA> {speaker} <NA> <NA>\n"
            out.write(line)

    print(f"Converti {json_path} → {rttm_path}")


def extract_segments(audio_folder, output_folder, min_duration_ms=5000):
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(audio_folder):
        if not file.endswith(".wav"):
            continue

        audio_path = os.path.join(audio_folder, file)
        audio = AudioSegment.from_file(audio_path)

        rttm_file = os.path.join(SPEAKERS_FOLDER, file.replace(".wav", ".rttm"))
        if not os.path.exists(rttm_file):
            print(f"RTTM manquant pour {file}, ignoré.")
            continue

        with open(rttm_file, "r", encoding="utf-8") as r:
            for line in r:
                if not line.startswith("SPEAKER"):
                    continue
                parts = line.split()
                if len(parts) < 8:
                    continue

                speaker = parts[7]
                start = float(parts[3]) * 1000
                dur = float(parts[4]) * 1000

                if dur < min_duration_ms:
                    continue

                segment = audio[start : start + dur]

                speaker_folder = os.path.join(output_folder, speaker)
                os.makedirs(speaker_folder, exist_ok=True)

                seg_filename = f"{file.replace('.wav', '')}_{int(start)}ms.wav"
                seg_path = os.path.join(speaker_folder, seg_filename)

                segment.export(seg_path, format="wav")

        print(f"Segments extraits pour {file}")


# 1. upload files
audio_urls = []

for file in os.listdir(AUDIOS_FOLDER):
    if file.endswith(".wav"):
        path = os.path.join(AUDIOS_FOLDER, file)
        audio_urls.append(upload_audio_file(path))

# 2. Diarization
diarize(audio_urls, SPEAKERS_FOLDER)

#  3. Convert JSON to RTTM
json_files = []
for file in os.listdir(SPEAKERS_FOLDER):
    if file.endswith(".json"):
        json_files.append(SPEAKERS_FOLDER + "/" + file)

print(json_files)
for jf in json_files:
    json_to_rttm(jf, SPEAKERS_FOLDER)

# 4. Get segments
extract_segments(AUDIOS_FOLDER, "segments")
