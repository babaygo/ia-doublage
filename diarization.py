from pyannote.audio import Pipeline
from dotenv import load_dotenv
import os
import torch
import torchaudio

load_dotenv()

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

print("GPU dispo:", torch.cuda.is_available())
print(
    "Nom GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"
)

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1", token=os.getenv("huggingface-token")
)

if torch.cuda.is_available():
    pipeline.to(torch.device("cuda"))


def diarize(folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(folder):
        if not file.endswith(".wav"):
            continue

        path = os.path.join(folder, file)
        waveform, sample_rate = torchaudio.load(path)

        diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})

        ann = diarization.speaker_diarization

        rttm_path = os.path.join(output_folder, file.replace(".wav", ".rttm"))
        with open(rttm_path, "w", encoding="utf-8") as rttm:
            ann.write_rttm(rttm)

        for segment, _, speaker in ann.itertracks(yield_label=True):
            print(f"{file}: {segment.start:.1f}s → {segment.end:.1f}s | {speaker}")


diarize("audio_vf", "speakers_fr")
