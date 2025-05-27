# download_ckip_model.py

from transformers import AutoModelForTokenClassification, AutoTokenizer
import os

def download_ckip_model(save_path="models/ckip-models/bert-base"):
    # 建立儲存資料夾（若不存在）
    os.makedirs(save_path, exist_ok=True)

    model_name = "ckiplab/bert-base-chinese-ws"

    print(f"Downloading model from Hugging Face: {model_name}")
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print(f"Saving model to: {save_path}")
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print("✅ Model and tokenizer saved successfully.")

if __name__ == "__main__":
    download_ckip_model()
