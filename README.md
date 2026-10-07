# Creative Studio — Core Generators (standalone module)

Three independent tools, nothing else:
- **Text-to-image** — prompt in, image out.
- **Image + text-to-image** — a reference image + prompt in, transformed image out.
- **Caption generator** — a short description in, an ad caption out.

No trend engine connection, no CTR scoring, no niche/tone system — just the
core generation building blocks. Runs on Hugging Face Inference Providers
(FLUX.1-schnell / FLUX.1-Kontext-dev / Qwen2.5-7B-Instruct), so no GPU or
model download needed on your laptop.

## 1. Get your free Hugging Face token
- Sign up at https://huggingface.co (free)
- https://huggingface.co/settings/tokens → **Create new token** → type **Read** → Generate
- Copy the token (starts with `hf_...`)

## 2. Set up the project

```
cd creative_studio
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Add your token

Copy `.env.example` to a new file named `.env`, paste your token in:
```
HF_TOKEN=hf_your_actual_token_here
```

## 4. Run it

```
uvicorn main:app --host 0.0.0.0 --port 8000
```
Check it's alive:
```
curl http://127.0.0.1:8000/health
```

## 5. Try each tool

**Text-to-image:**
```
curl -X POST http://localhost:8000/generate/text2img -F "prompt=professional ad photo of a matcha latte in a cozy cafe, warm lighting, high quality" -o result_text2img.png
```

**Image + text-to-image** (put a reference photo in the folder first):
```
curl -X POST http://localhost:8000/generate/img2img -F "prompt=same product but with a festive Diwali themed background" -F "reference_image=@your_photo.jpg" -o result_img2img.png
```

**Caption generator:**
```
curl -X POST http://localhost:8000/generate/caption -F "description=matcha latte at a cozy cafe" -F "tone=Playful" -o result_caption.json
```
Open `result_caption.json` in Notepad to see `{"caption": "..."}`.

## Notes
- Text-to-image and image-to-image responses are returned as raw PNG image
  bytes (`-o filename.png` saves them directly — no decoding step needed,
  unlike the earlier combined-JSON version).
- Caption is returned as plain JSON since there's no image to carry alongside it.
- These three endpoints are fully independent — call any one on its own, in
  any order, for whatever you're testing.
