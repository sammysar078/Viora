# Viora

Modular Telegram economy + premium + gems + powers + five games bot.

## Run
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Important configuration
- `PREMIUM_STARS` and `PREMIUM_DAYS` control Premium pricing/duration.
- `GEM_PRICE_INR` is the configured 1-gem INR price (default ₹8).
- `PAYMENT_PROVIDER_TOKEN` is required for INR gem invoices.
- Telegram Stars are used for Premium.
- `LIBRETRANSLATE_URL` is optional for `/tr`.
- `ffmpeg` is recommended for future animated sticker processing.

## Implemented command families
Economy, wallet, daily, kill, rob, revive, protection, gifting, leaderboards, Premium, gems, powers, Hack, Bluff, Roulette, Card, Bomb, coupons, whisper, intros, interactions, utilities, translation, TTS, reports and group help.

## Telegram button styles
Navigation is sent through the Telegram Bot API so inline buttons use `primary`, `success`, and `danger` styles where applicable.
