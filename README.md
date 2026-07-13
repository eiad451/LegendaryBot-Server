# LegendaryBot Server 🚀

**Developer:** 𝓙𝓸𝓴𝓮𝓻丨𝓜4
**Username:** @VT_YC

Telegram Bot + Web API Server for Digital Products Store.

## Features
- Telegram bot for selling digital codes via Telegram Stars
- API Server for app integration
- Admin panel (telegram & web)
- SQLite database
- Discount system
- Order management

## Setup
```bash
pip install python-telegram-bot flask
export BOT_TOKEN="your_bot_token"
export ADMIN_ID="your_telegram_id"
python bot.py
```

## API Endpoints
- `GET /api/` - API info
- `GET /api/products` - List products
- `POST /api/verify` - Admin login
- `GET /api/stats` - Statistics
- `GET /api/orders` - Orders list

## Admin Password
Default: `VT_YC`

## License
© 2026 𝓙𝓸𝓴𝓮𝓻丨𝓜4 - All Rights Reserved
