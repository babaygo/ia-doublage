import json
import os


def json_to_rttm(json_path: str, output_folder="speakers_fr"):
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


json_files = []
for file in os.listdir("speakers_fr"):
    if file.endswith(".json"):
        json_files.append("speakers_fr/" + file)

print(json_files)
for jf in json_files:
    json_to_rttm(jf, "speakers_fr")
