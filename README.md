<div align="center">
<img src="icon.jpeg" alt="Casino Bot Icon" width="200"/>

# Discord Casino Bot

A Discord bot that brings the excitement of casino games to your server with fair gaming mechanics!
</div>

## Features

- Fair and transparent gaming mechanics
- Real-time credit balance tracking
- European Roulette with multiple betting options
- Admin credit management system
- User-friendly embed messages

## Add Bot to Your Server

Click [here](https://discord.com/oauth2/authorize?client_id=1344000509933256725&permissions=277025392704&integration_type=0&scope=bot) to add the Casino Bot to your Discord server!

## Commands

### `/balance`
Check your current casino credit balance.
- Creates a new account if you don't have one
- Displays your current credit balance with a stylish embed

### `/roulette`
Place bets on European Roulette with various betting options.

**Parameters:**
- `amount`: Number of credits to bet (minimum 10 credits)
- `choice`: Betting options
  - `red/black`: 1:1 payout
  - `1-18/19-36`: 1:1 payout
  - `1-12/13-24/25-36`: 2:1 payout

### `/give` (Admin Only)
Allow administrators to give credits to users.

**Parameters:**
- `user`: The Discord user to give credits to
- `amount`: Number of credits to give

### `/withdraw` (Admin Only)
Allow administrators to withdraw credits from users.

**Parameters:**
- `user`: The Discord user to withdraw credits from
- `amount`: Number of credits to withdraw

## European Roulette Numbers

- **Red Numbers:** 1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36
- **Black Numbers:** 2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35
- **Green Number:** 0

## Setup Requirements

1. Python 3.12 or higher
2. Required packages:
   - discord.py
   - python-dotenv
   - supabase-py

## Environment Variables

Create a `.env` file with the following variables:
```
DISCORD_TOKEN=your_bot_token
CLIENT_ID=your_client_id
SUPABASE_URL=your_supabase_url
SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your environment variables
4. Run the bot: `python app.py`

## Fair Gaming Policy

This bot implements fair gaming mechanics with standard European Roulette odds:
- Red/Black: 48.6% chance (18/37)
- High/Low: 48.6% chance (18/37)
- Dozens: 32.4% chance (12/37)

## Support

For support, feature requests, or bug reports, please open an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.