import os

import pandas as pd
from datasets import load_dataset
from huggingface_hub import CommitOperationAdd, HfApi, create_repo, login

from speechbox import Restorer

REPO_ID = "patrickvonplaten/librispeech_asr_dummy_orthograph"
LOCAL_FOLDER = f"/home/patrick/{REPO_ID.split('/')[-1]}"
LOCAL_FILE = os.path.join(LOCAL_FOLDER, "transcripts.csv")
NUM_BEAMS = 2

MODEL_ID = "openai/whisper-tiny.en"

hf_api = HfApi()

dataset = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean")["validation"]
# dataset = dataset.select(range(48, 49))

restorer = Restorer.from_pretrained(MODEL_ID)
restorer.to("cuda")


def restore(example):
    audio = example["audio"]["array"]
    sampling_rate = example["audio"]["sampling_rate"]
    text = example["text"].lower()
    restored_text, probs = restorer(audio, text, sampling_rate=sampling_rate, num_beams=NUM_BEAMS)
    return {"orig_transcript": text, "new_transcript": restored_text, "probs": probs}


out = dataset.map(restore, remove_columns=dataset.column_names)

df = pd.DataFrame(
    {"orig_transcript": out["orig_transcript"], "new_transcript": out["new_transcript"], "props": out["probs"]}
)

with open(LOCAL_FILE, "w") as f:
    f.write(df.to_csv(index=False))

operations = [CommitOperationAdd(path_in_repo="transcripts.csv", path_or_fileobj=LOCAL_FILE)]

create_repo(REPO_ID, exist_ok=True, repo_type="dataset")
hf_api.create_commit(
    repo_id=REPO_ID,
    operations=operations,
    commit_message="Upload new transcriptions",
    repo_type="dataset",
)
