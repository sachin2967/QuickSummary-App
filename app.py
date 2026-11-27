import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
MIN_OUTPUT_TOKENS = 50
MAX_OUTPUT_TOKENS = 1000
DEFAULT_OUTPUT_TOKENS = 150


def render_error(message: str, status_code: int, *, text: str = "", max_length: int = DEFAULT_OUTPUT_TOKENS):
    return (
        render_template(
            "index.html",
            data="",
            error=message,
            text=text,
            maxL=max_length,
        ),
        status_code,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html", maxL=DEFAULT_OUTPUT_TOKENS)

    text = (request.form.get("text") or "").strip()
    if not text:
        return render_error("Enter some text before requesting a summary.", 400)

    try:
        max_length = int(request.form.get("maxL", DEFAULT_OUTPUT_TOKENS))
    except (TypeError, ValueError):
        return render_error("Choose a valid summary length.", 400, text=text)

    if not MIN_OUTPUT_TOKENS <= max_length <= MAX_OUTPUT_TOKENS:
        return render_error(
            f"Summary length must be between {MIN_OUTPUT_TOKENS} and {MAX_OUTPUT_TOKENS} model tokens.",
            400,
            text=text,
            max_length=max_length,
        )

    token = os.getenv("API_TOKEN")
    if not token:
        return render_error(
            "Hugging Face is not configured. Set API_TOKEN in your local .env file.",
            503,
            text=text,
            max_length=max_length,
        )

    payload = {
        "inputs": text,
        "parameters": {
            "min_length": max(1, max_length // 4),
            "max_length": max_length,
        },
    }

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=(10, 60),
        )
        response.raise_for_status()
        result = response.json()

        if isinstance(result, dict):
            api_message = result.get("error")
            raise ValueError(api_message or "The summarization service returned an unexpected response.")

        summary = result[0].get("summary_text") if isinstance(result, list) and result else None
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("The summarization service returned no summary.")

    except requests.Timeout:
        return render_error(
            "The summarization request timed out. Try a shorter input and submit again.",
            504,
            text=text,
            max_length=max_length,
        )
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        if status == 503:
            message = "The hosted model is loading or temporarily unavailable. Try again shortly."
        elif status in (401, 403):
            message = "Hugging Face rejected the configured token. Check API_TOKEN in your local .env file."
        else:
            message = f"The summarization service returned HTTP {status}. Try again later."
        return render_error(message, 502, text=text, max_length=max_length)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return render_error(
            "The summarization service could not complete this request. Try again later.",
            502,
            text=text,
            max_length=max_length,
        )

    return render_template("index.html", data=summary, text=text, maxL=max_length)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
