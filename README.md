# QuickSummary

A small Flask web app that summarizes pasted text using the
[`facebook/bart-large-cnn`](https://huggingface.co/facebook/bart-large-cnn) model through
the Hugging Face Inference API.

## How it works

1. You paste text and choose a maximum summary length.
2. The app sets the minimum length to a quarter of the maximum and sends the text to the
   Hugging Face Inference API.
3. The returned summary is rendered on the page. The requested `max_length` is measured in model tokens, not words.

## Setup

Requires Python 3.10+ and a free [Hugging Face access token](https://huggingface.co/settings/tokens).

```bash
git clone https://github.com/sachin2967/QuickSummary-App.git
cd QuickSummary-App
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env        # then put your token in API_TOKEN
flask --app app run
```

Open http://127.0.0.1:5000. For local debugging only, set `FLASK_DEBUG=1`; debug mode is off by default.

The output range is 50–1,000 model tokens (not words). Very long inputs may exceed the hosted model's input limit.

## Configuration

| Variable | Purpose |
| --- | --- |
| `API_TOKEN` | Hugging Face access token, read from `.env`. Never commit this file. |

## Limitations

- Depends on the third-party hosted Hugging Face model; availability, rate limits and latency are outside
  this app's control. Timeouts and common API errors are displayed in the page.
- Intended as a learning project, not a production service.

## License

MIT
