# UnknownBotz — Save Restricted Content Bot

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&style=for-the-badge">
  <img src="https://img.shields.io/badge/Library-Pyrogram-yellow?logo=telegram&style=for-the-badge">
  <img src="https://img.shields.io/badge/Database-MongoDB-green?logo=mongodb&style=for-the-badge">
</p>

A Telegram bot to save restricted/private channel content with batch support, real-time progress, and a dump channel system.

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram Bot Token from BotFather |
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `ADMINS` | Comma-separated admin user IDs |
| `DB_URI` | MongoDB connection string |
| `DB_NAME` | Database name (default: `src`) |
| `LOG_CHANNEL` | Channel ID for bot logs |
| `UPI_ID` | UPI ID for premium payments |
| `QR_CODE` | QR code image URL for payments |

---

## 🚀 Setup

**Local**
```bash
git clone <your-repo-url>
cd <repo>
pip install -r requirements.txt
python bot.py
```

**Docker**
```bash
docker build -t unknownbotz .
docker run -d --env-file .env unknownbotz
```

---

## 📝 Commands

### User
| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/help` | Show guide |
| `/login` | Login for restricted content |
| `/logout` | Logout session |
| `/cancel` | Cancel ongoing batch |
| `/settings` | Open settings panel |
| `/myplan` | Check plan & usage |
| `/premium` | View premium plans |
| `/setchnl <id>` | Set dump channel (bot must be admin) |
| `/remchnl` | Remove dump channel |
| `/set_caption <text>` | Set custom caption |
| `/see_caption` | View current caption |
| `/del_caption` | Delete caption |
| `/set_thumb` | Set custom thumbnail (reply to photo) |
| `/view_thumb` | View thumbnail |
| `/del_thumb` | Delete thumbnail |
| `/set_del_word` | Add word to delete list |
| `/rem_del_word` | Remove word from delete list |
| `/set_repl_word` | Add word replacement |
| `/rem_repl_word` | Remove word replacement |

### Admin
| Command | Description |
|---|---|
| `/broadcast` | Broadcast message to all users |
| `/users` | Get user list (JSON export) |
| `/ban <id>` | Ban a user |
| `/unban <id>` | Unban a user |
| `/add_premium <id> <days>` | Grant premium (0 = permanent) |
| `/remove_premium <id>` | Revoke premium |
| `/set_dump <user_id> <chat_id>` | Set dump channel for a user |
| `/dblink` | Get DB URI |

---

## 📌 Notes

- **Dump channel is required** before saving any file. Set it with `/setchnl` — bot must be an admin there.
- **Free users:** 10 saves/day, 2 GB file size limit.
- **Premium users:** Unlimited saves, 4 GB+ file support.
- Batch links format: `https://t.me/channel/100-200`

---

## 📞 Support

- Telegram: [@UnknownBotz](https://t.me/UnknownBotz)
