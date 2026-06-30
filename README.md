# Discord Honeypot Ban Bot

A simple Discord bot to monitor honeypot channels and automatically ban compromised accounts that post in them.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure the bot:
   - Edit `config.json` and add:
     - `bot_token`: Your Discord bot token
     - `authorized_role_id`: Role ID that can use /watchchannel and /unwatchchannel commands
     - `whitelisted_role_id`: Role ID that won't be banned when posting in honeypot channels

3. Bot Permissions Required:
   - Ban Members
   - Read Messages/View Channels
   - Read Message History
   - Manage Messages

4. Run the bot:
   ```
   python bot.py
   ```

## Commands

- `/watchchannel <channel_id>` - Add a channel to the watch list (requires authorized role)
- `/unwatchchannel <channel_id>` - Remove a channel from the watch list (requires authorized role)

## How It Works

1. Admins use `/watchchannel` to mark channels as honeypots
2. The bot monitors all messages in watched channels
3. If a user without the whitelisted role posts a message, they are immediately banned
4. The bot deletes the last hour of the banned user's messages across the server
