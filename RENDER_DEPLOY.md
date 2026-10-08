# Viora — Render deployment

Use a **Background Worker** from this repository. The included `render.yaml` uses the Docker runtime so FFmpeg is available for `/q` media conversion.

Required secrets:
- API_ID
- API_HASH
- BOT_TOKEN
- MONGO_URI
- BOT_USERNAME
- OWNER_IDS
- PAYMENT_PROVIDER_TOKEN (only if INR Gem purchases are enabled)

Optional:
- LIBRETRANSLATE_URL / LIBRETRANSLATE_API_KEY for `/tr`

The bot starts with:
`python -m Viora.app`

Never commit `.env` or real Telegram/Mongo/payment credentials.
