import os
import csv
import json
from helper import ocr_space_file

IMAGES_DIR = "schedule_images"
OUT_DIR = "out"
OUT_CSV = os.path.join(OUT_DIR, "schedule_texts.csv")

def load_env(file_path=".env"):
    """Manually load environment variables from a .env file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

def extract_text_from_image(path, api_key, language="eng"):
    """Calls [`ocr_space_file`](helper.py) and returns combined ParsedText."""
    raw = ocr_space_file(filename=path, api_key=api_key, language=language)
    try:
        j = json.loads(raw)
    except Exception:
        return ""  # return empty on parse error
    texts = []
    for pr in j.get("ParsedResults", []) or []:
        texts.append(pr.get("ParsedText", ""))
    return "\n".join(t.strip() for t in texts).strip()

def main():
    load_env()
    os.makedirs(OUT_DIR, exist_ok=True)
    api_key = os.environ.get("OCR_API_KEY")
    if not api_key:
        print("Error: OCR_API_KEY environment variable not set in .env or system.")
        return
    files = sorted(f for f in os.listdir(IMAGES_DIR)
                   if f.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvf:
        writer = csv.writer(csvf, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["filename", "text"])
        for fn in files:
            path = os.path.join(IMAGES_DIR, fn)
            print("Processing", path)
            text = extract_text_from_image(path, api_key=api_key)
            writer.writerow([fn, text])
    print("Wrote", OUT_CSV)

if __name__ == "__main__":
    main()
