# Miamidian Giveaway Bot

Discord giveaway bot with invite requirements.

## Features

- `/giveaway_create` — create a giveaway with prize, duration, invite requirement, and winner count.
- `/giveaway_end` — end a giveaway early.
- `/giveaway_reroll` — reroll winners.
- `/invites` — check a member's tracked valid invites.
- Persistent giveaway buttons.
- SQLite storage for invites, giveaways, and entries.
- Default invite requirement is 5.

## Discord bot permissions

Give the bot these server permissions:

- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands
- Manage Server is **not** required for the bot itself.

The bot account also needs permission to view server invites so invite tracking can work. The person creating/ending giveaways needs **Manage Server**.

## Developer Portal

Enable the **Server Members Intent** under Bot > Privileged Gateway Intents.

Invite the bot with these OAuth2 scopes:

- `bot`
- `applications.commands`

## Setup

1. Install Python 3.11+.
2. Open this folder in a terminal.
3. Run:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env`.
5. Put your Discord bot token in `.env`:

```env
DISCORD_TOKEN=YOUR_TOKEN_HERE
```

Never upload your real token to GitHub.

6. Start the bot:

```bash
python bot.py
```

## Example

```text
/giveaway_create prize:Nitro minutes:60 min_invites:5 winners:1
```

Members press **Enter Giveaway**. If they have fewer than 5 tracked valid invites, the bot rejects the entry privately.

## Important invite-tracking note

Discord invite tracking is based on changes to invite-use counts. It works best when the bot has access to all server invites and remains online while members join. Vanity invites or missing permissions can make attribution less reliable.
