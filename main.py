"""
AdVantage OS — Creative Studio: Core Generators (standalone module)

Three independent tools, nothing else:
    POST /generate/text2img   -> prompt only -> image
    POST /generate/img2img    -> prompt + reference image -> image
    POST /generate/caption    -> description/prompt -> ad caption

No trend engine, no CTR scoring, no niche/tone logic — pure generation
building blocks you can wire up however you like later.

Setup:
    1. Get a free HF token: https://huggingface.co/settings/tokens (Read access)
    2. Copy .env.example to .env and paste your token in
    3. pip install -r requirements.txt
    4. uvicorn main:app --host 0.0.0.0 --port 8000
"""

import io
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from huggingface_hub import InferenceClient
from PIL import Image

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN not set. Copy .env.example to .env and paste your Hugging Face "
        "token in (get one free at https://huggingface.co/settings/tokens)."
    )

client = InferenceClient(api_key=HF_TOKEN)

TEXT2IMG_MODEL = "black-forest-labs/FLUX.1-schnell"
IMG2IMG_MODEL = "black-forest-labs/FLUX.1-Kontext-dev"
CAPTION_MODEL = "meta-llama/Llama-3.1-8B-Instruct:novita"

app = FastAPI(title="AdVantage OS — Creative Studio: Core Generators")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before deploying beyond your own laptop
    allow_methods=["*"],
    allow_headers=["*"],
)


def _image_to_response(image: Image.Image) -> StreamingResponse:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# ----------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "text2img_model": TEXT2IMG_MODEL, "img2img_model": IMG2IMG_MODEL}


@app.post("/generate/text2img")
def generate_text2img(
    prompt: str = Form(...),
    negative_prompt: str = Form(""),
):
    """Pure text-to-image. `negative_prompt` is accepted but only applied
    if the underlying provider/model supports it — FLUX.1-schnell largely
    ignores it, kept here for when you swap in a model that honors it."""
    try:
        image = client.text_to_image(prompt, model=TEXT2IMG_MODEL)
    except Exception as e:
        raise HTTPException(502, f"Image generation failed: {e}")
    return _image_to_response(image)


@app.post("/generate/img2img")
async def generate_img2img(
    prompt: str = Form(...),
    reference_image: UploadFile = File(...),
):
    """Image + prompt -> image. Uses the reference image as a visual anchor
    and transforms/extends it according to the prompt."""
    raw = await reference_image.read()
    try:
        image = client.image_to_image(raw, prompt=prompt, model=IMG2IMG_MODEL)
    except Exception as e:
        raise HTTPException(502, f"Image-to-image generation failed: {e}")
    return _image_to_response(image)


@app.post("/generate/caption")
def generate_caption_endpoint(
    description: str = Form(...),
    tone: str = Form("Playful"),
):
    """Freeform description -> a short ad caption."""
    try:
        completion = client.chat.completions.create(
            model=CAPTION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert social media advertising copywriter. "
                        "Generate concise, engaging Instagram ad captions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write ONE short {tone.lower()}-tone Instagram ad caption "
                        f"for: {description}. "
                        "Maximum 20 words. "
                        "Include exactly one relevant emoji. "
                        "Return ONLY the caption text."
                    ),
                },
            ],
            max_tokens=60,
            temperature=0.8,
        )

        caption = completion.choices[0].message.content

        if not caption:
            raise RuntimeError("The caption model returned no text.")

        caption = caption.strip().strip('"')

        return {"caption": caption}

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Caption generation failed: {e}"
        )