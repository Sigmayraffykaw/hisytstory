# Miamidian Giveaway Bot

Advanced Discord giveaway bot with invite requirements and anti-fake invite checks.

## Features

- `/giveaway_create` — create a giveaway with prize, duration, invite requirement, winner count, optional role requirement, and bonus-entry settings.
- `/giveaway_end` — end a giveaway early.
- `/giveaway_reroll` — reroll winners.
- `/invites` — check a member's tracked valid invites.
- `/giveaway_blacklist` — block a member from giveaway entry.
- `/giveaway_unblacklist` — remove a member from the blacklist.
- `/giveaway_blacklist_check` — check blacklist status.
- Rich giveaway embeds.
- Discord countdown timestamps using both absolute and relative time.
- Persistent giveaway entry buttons.
- Winner DMs when possible.
- Required-role support.
- Weighted bonus entries based on valid invite counts.
- SQLite storage for invites, giveaways, entries, blacklist records, and invite relationships.
- Default invite requirement is 5.

## Anti-fake invite checks

Invite credit is not given instantly. By default:

- bot accounts do not count;
- self-invites do not count;
- accounts younger than 7 days do not count;
- invited members must remain in the server for at least 10 minutes before the inviter receives credit;
- if a credited invited member leaves later, the invite is deducted again.

You can change the defaults using environment variables:

```env
MIN_ACCOUNT_AGE_DAYS=7
INVITE_CREDIT_DELAY_MINUTES=10
```

## Discord bot permissions

Give the bot:

- View Channels
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands

The bot must also be able to view server invites for invite tracking. The person creating, ending, rerolling, or managing giveaway blacklists needs **Manage Server**.

## Developer Portal

Enable **Server Members Intent** under **Bot > Privileged Gateway Intents**.

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

## Giveaway example

```text
/giveaway_create prize:Nitro minutes:60 min_invites:5 winners:1 required_role:@Member bonus_every_invites:5 bonus_entries:1
```

That example requires 5 valid invites and the Member role. Every 5 valid invites gives the entrant +1 extra weighted entry.

## Invite tracking note

Discord invite attribution works by comparing invite-use counts before and after a member joins. It works best while the bot stays online and can see all server invites. Vanity invites or missing invite permissions can reduce attribution accuracy.
