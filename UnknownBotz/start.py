# Developed by: UnknownBotz
# Telegram: @UnknownBotz |
import os
import asyncio
import random
import time
import shutil
import hashlib
import requests
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated,
    MessageNotModified, ChannelInvalid, ChannelPrivate,
    ChatAdminRequired, ChatWriteForbidden
)
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery, InputMediaPhoto
)
from config import API_ID, API_HASH, ERROR_MESSAGE
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION   = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
FREE_LIMIT_SIZE = 2 * 1024 * 1024 * 1024
UPI_ID  = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")

REACTIONS = [
    "👍","❤️","🔥","🥰","👏","😁","🤔","🤯","😱","🤬","😢","🎉","🤩",
    "🤮","💩","🙏","👌","🕊","🤡","🥱","🥴","😍","🐳","❤️‍🔥","🌚","🌭",
    "💯","🤣","⚡","🍌","🏆","💔","🤨","😐","🍓","🍾","💋","🖕","😈",
    "😴","😭","🤓","👻","👨‍💻","👀","🎃","🙈","😇","😨","🤝","✍","🤗",
    "🫡","🎅","🎄","☃","💅","🤪","🗿","🆒","💘","🙉","🦄","😘","💊",
    "🙊","😎","👾","🤷‍♂️","🤷‍♀️","😡"
]

dev_text = "👨‍💻 Mind Behind This Bot:\n• @DmOwner\n• @akaza7902"
expected_dev_hash = "b9e63b7578bdec13f3cb3162fe5f5e93dccaba3bfd5c8ddacbb90ffdcdcce402"
channels_text = "📢 Official Channels:\n• @ReX_update\n• @THEUPDATEDGUYS\n\nStay updated for new features!"
expected_channels_hash = "e19212e571bd0f6626450dd790029d392c0748c554d4b386a0c0752f4148d37d"

if (
    hashlib.sha256(dev_text.encode()).hexdigest() != expected_dev_hash or
    hashlib.sha256(channels_text.encode()).hexdigest() != expected_channels_hash
):
    raise Exception("Tampered developer info detected! Bot will not start.")


# ── Helpers ──────────────────────────────────

def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    power, n = 2**10, 0
    labels = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {labels[n]}B"


def TimeFormatter(ms: int) -> str:
    s, _   = divmod(int(ms), 1000)
    m, s   = divmod(s, 60)
    h, m   = divmod(m, 60)
    d, h   = divmod(h, 24)
    parts  = (
        (f"{d}d, " if d else "") +
        (f"{h}h, " if h else "") +
        (f"{m}m, " if m else "") +
        (f"{s}s, " if s else "")
    )
    return parts[:-2] if parts else "0s"


def get_message_type(msg):
    for attr, label in [('document','Document'),('video','Video'),
                        ('photo','Photo'),('audio','Audio'),('text','Text')]:
        if getattr(msg, attr, None):
            return label
    return None


# ── Static texts ─────────────────────────────

class script:
    START_TXT = (
        "<b>👋 Hello {},</b>\n"
        "<b>🤖 I am <a href=https://t.me/{}>{}</a></b>\n"
        "<i>Your Professional Restricted Content Saver Bot.</i>\n"
        "<blockquote><b>🚀 System Status: 🟢 Online</b>\n"
        "<b>⚡ Performance: 10x High-Speed Processing</b>\n"
        "<b>🔐 Security: End-to-End Encrypted</b>\n"
        "<b>📊 Uptime: 99.9% Guaranteed</b></blockquote>\n"
        "<b>👇 Select an Option Below to Get Started:</b>\n"
    )

    HELP_TXT = (
        "<b>📚 Help & User Guide</b>\n"
        "<blockquote><b>1️⃣ Public Channels</b>\n"
        "Send or forward a public post link.\n"
        "Example: <code>https://t.me/channel/123</code></blockquote>\n"
        "<blockquote><b>2️⃣ Private/Restricted Channels</b>\n"
        "Use /login first, then send the private link.</blockquote>\n"
        "<blockquote><b>3️⃣ Batch Mode</b>\n"
        "Send: <code>https://t.me/channel/100-200</code>\n"
        "Real-time progress bar with ❌ Cancel support.</blockquote>\n"
        "<blockquote><b>📢 Dump Channel (Required)</b>\n"
        "Set with /setchnl before saving.\n"
        "Bot must be admin in that channel.</blockquote>\n"
        "<blockquote><b>🛑 Free Limits</b>\n"
        "10 Files/day • 2 GB max per file</blockquote>\n"
        "<blockquote><b>💎 Premium</b>\n"
        "Unlimited downloads & no restrictions</blockquote>\n"
    )

    ABOUT_TXT = (
        "<b>ℹ️ About This Bot</b>\n"
        "<blockquote><b>╭────[ 🧩 Technical Stack ]────⍟</b>\n"
        "<b>├⍟ 🤖 Bot Name : <a href=http://t.me/THEUPDATEDGUYS_Bot>Save Content</a></b>\n"
        "<b>├⍟ 👨‍💻 Developer : <a href=https://t.me/DmOwner>Ⓜ️ark X UnknownBotz</a></b>\n"
        "<b>├⍟ 📚 Library : <a href='https://docs.pyrogram.org/'>Pyrogram Async</a></b>\n"
        "<b>├⍟ 🐍 Language : <a href='https://www.python.org/'>Python 3.11+</a></b>\n"
        "<b>├⍟ 🗄 Database : <a href='https://www.mongodb.com/'>MongoDB Atlas Cluster</a></b>\n"
        "<b>├⍟ 📡 Hosting : Dedicated High-Speed VPS</b>\n"
        "<b>╰───────────────⍟</b></blockquote>\n"
    )

    PREMIUM_TEXT = (
        "<b>💎 Premium Membership Plans</b>\n"
        "<b>Unlock Unlimited Access & Advanced Features!</b>\n"
        "<blockquote><b>✨ Key Benefits:</b>\n"
        "<b>♾️ Unlimited Daily Downloads</b>\n"
        "<b>📂 Support for 4GB+ File Sizes</b>\n"
        "<b>⚡ Instant Processing (Zero Delay)</b>\n"
        "<b>🖼 Customizable Thumbnails</b>\n"
        "<b>📝 Personalized Captions</b>\n"
        "<b>🛂 24/7 Priority Support</b></blockquote>\n"
        "<blockquote><b>💳 Pricing Options:</b>\n"
        "• <b>1 Month Plan:</b> ₹50 / $1\n"
        "• <b>3 Month Plan:</b> ₹120 / $2.5 (Save 20%)\n"
        "• <b>Lifetime Access:</b> ₹200 / $4</blockquote>\n"
        "<b>💸 UPI ID:</b> <code>{}</code>\n"
        "<b>📸 QR Code:</b> <a href='{}'>Scan to Pay</a>\n"
        "<i>Send payment screenshot to admin for instant activation.</i>\n"
    )

    CAPTION = (
        "<b><a href=\"https://t.me/THEUPDATEDGUYS\"></a></b>\n\n"
        "<b>⚜️ Powered By : <a href=\"https://t.me/THEUPDATEDGUYS\">THE UPDATED GUYS 😎</a></b>"
    )

    LIMIT_REACHED = (
        "<b>🚫 Daily Limit Exceeded</b>\n"
        "<b>Your 10 free saves for today have been used.</b>\n"
        "<i>Quota resets automatically after 24 hours.</i>\n"
        "<blockquote><b>🔓 Upgrade to Premium for Unlimited Access!</b></blockquote>\n"
    )

    SIZE_LIMIT = (
        "<b>⚠️ File Size Exceeded</b>\n"
        "<b>Free tier limited to 2GB per file.</b>\n"
        "<blockquote><b>🔓 Upgrade to Premium</b>\n"
        "Download files up to 4GB and beyond!</blockquote>\n"
    )

    # ── FIX 2: blockquote progress bar with Download/Upload status ──
    @staticmethod
    def progress_text(status_emoji, status_label, completed, total,
                      filename, pct, speed, cur, tot, elapsed_ms, eta_ms):
        return (
            f"{status_emoji} <b>{status_label}</b>  "
            f"<code>{completed} / {total}</code>\n"
            f"<blockquote>"
            f"📄 <b>{filename}</b>\n"
            f"Progress: <b>{pct:.1f}%</b>\n"
            f"🚀 Speed: <code>{humanbytes(speed)}/s</code>\n"
            f"💾 Size: <code>{humanbytes(cur)} of {humanbytes(tot)}</code>\n"
            f"⏱ Elapsed: <code>{TimeFormatter(elapsed_ms)}</code>\n"
            f"⏳ ETA: <code>{TimeFormatter(eta_ms)}</code>"
            f"</blockquote>"
        )


# ── Batch State ───────────────────────────────

class UserBatchState:
    def __init__(self, total_files, progress_msg, user_id):
        self.total_files     = total_files
        self.completed_files = 0
        self.cancelled       = False
        self.progress_msg    = progress_msg
        self.user_id         = user_id
        self.batch_start     = time.time()
        self.file_start      = time.time()
        self.last_edit       = 0.0


class batch_temp:
    IS_BATCH: dict = {}
    STATES:   dict = {}


def cancel_markup(user_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_batch_{user_id}")
    ]])


async def _safe_edit(msg, text, markup=None):
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    except (MessageNotModified, Exception):
        pass


# ── FIX 4a: raise asyncio.CancelledError (not Exception) ──
# so pyrogram treats it as a clean abort instead of logging ERROR

async def batch_progress_callback(current, total, state: UserBatchState,
                                   filename, operation):
    if state.cancelled or batch_temp.IS_BATCH.get(state.user_id, True):
        raise asyncio.CancelledError()

    now = time.time()
    if now - state.last_edit < 3 and current != total:
        return
    state.last_edit = now

    elapsed  = now - state.file_start
    speed    = int(current / elapsed) if elapsed > 0 else 0
    eta_secs = (total - current) / speed if speed > 0 else 0
    pct      = current * 100 / total if total > 0 else 0

    if operation == "down":
        emoji, label = "⬇️", "Downloading..."
    else:
        emoji, label = "⬆️", "Uploading..."

    text = script.progress_text(
        emoji, label,
        state.completed_files, state.total_files,
        filename, pct, speed, current, total,
        int(elapsed * 1000), int(eta_secs * 1000)
    )
    await _safe_edit(state.progress_msg, text, markup=cancel_markup(state.user_id))


# ── /start ────────────────────────────────────

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        pass

    try:
        r = requests.get(random.choice([
            "https://api.waifu.pics/sfw/waifu",
            "https://nekos.life/api/v2/img/waifu"
        ]), timeout=5)
        photo_url = r.json()["url"]
    except Exception:
        photo_url = "https://i.postimg.cc/kX9tjGXP/16.png"

    bot = await client.get_me()
    await client.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=script.START_TXT.format(message.from_user.mention, bot.username, bot.first_name),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Buy Premium",    callback_data="buy_premium"),
             InlineKeyboardButton("🆘 Help & Guide",   callback_data="help_btn")],
            [InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
             InlineKeyboardButton("ℹ️ About Bot",      callback_data="about_btn")],
            [InlineKeyboardButton("📢 Channels",       callback_data="channels_info"),
             InlineKeyboardButton("👨‍💻 Developers",    callback_data="dev_info")],
        ]),
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )


# ── /help ─────────────────────────────────────

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        message.chat.id, script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_btn")]]),
        parse_mode=enums.ParseMode.HTML
    )


# ── /plan /myplan /premium ────────────────────

@Client.on_message(filters.command(["plan", "myplan", "premium"]))
async def send_plan(client: Client, message: Message):
    await client.send_photo(
        message.chat.id, SUBSCRIPTION,
        caption=script.PREMIUM_TEXT.format(UPI_ID, QR_CODE),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Send Payment Proof", url="https://t.me/DmOwner")],
            [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
        ]),
        parse_mode=enums.ParseMode.HTML
    )


# ── /cancel ───────────────────────────────────

@Client.on_message(filters.command("cancel"))
async def send_cancel(client: Client, message: Message):
    uid = message.from_user.id
    batch_temp.IS_BATCH[uid] = True
    s = batch_temp.STATES.get(uid)
    if s:
        s.cancelled = True
    await message.reply_text("❌ <b>Process Cancelled Successfully</b>",
                              parse_mode=enums.ParseMode.HTML)


# ── Inline Cancel button ──────────────────────

@Client.on_callback_query(filters.regex(r"^cancel_batch_\d+$"), group=0)
async def cancel_batch_callback(client: Client, cq: CallbackQuery):
    target = int(cq.data.split("_")[-1])
    if cq.from_user.id != target:
        await cq.answer("⛔ You can't cancel someone else's task!", show_alert=True)
        return
    batch_temp.IS_BATCH[target] = True
    s = batch_temp.STATES.get(target)
    if s:
        s.cancelled = True
    try:
        await cq.message.edit_text("❌ <b>Process Cancelled Successfully</b>",
                                   reply_markup=None, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    await cq.answer("✅ Cancelled!")


# ── Settings panel helper ─────────────────────

async def settings_panel(client, cq):
    uid = cq.from_user.id
    badge = "💎 Premium Member" if await db.check_premium(uid) else "👤 Standard User"
    await cq.edit_message_caption(
        caption=(
            f"<b>⚙️ Settings Dashboard</b>\n\n"
            f"<b>Account Status:</b> {badge}\n"
            f"<b>User ID:</b> <code>{uid}</code>\n\n"
            f"<i>Customize your bot preferences below:</i>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Command List",          callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 Usage Stats",           callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Channel Settings", callback_data="dump_chat_btn")],
            [InlineKeyboardButton("🖼 Manage Thumbnail",      callback_data="thumb_btn")],
            [InlineKeyboardButton("📝 Edit Caption",          callback_data="caption_btn")],
            [InlineKeyboardButton("⬅️ Return to Home",        callback_data="start_btn")],
        ]),
        parse_mode=enums.ParseMode.HTML
    )


# ── Main save handler ─────────────────────────
# FIX 1: Dump channel checked FIRST for both single & batch

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    uid = message.from_user.id

    # ── FIX 1: dump channel guard — block before anything else ──
    dump_chat = await db.get_dump_chat(uid)
    if not dump_chat:
        return await message.reply_text(
            "⚠️ <b>Dump channel not set!</b>\n\n"
            "<blockquote>You must set a dump channel before saving any files.\n"
            "Use /setchnl to set your channel.\n"
            "The bot must be an admin there.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )

    # Prevent concurrent task
    if batch_temp.IS_BATCH.get(uid) is False:
        return await message.reply_text(
            "<b>⚠️ A Task is Already Running.</b>\n"
            "<i>Wait for it to finish or press ❌ Cancel.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    # Daily limit
    if await db.check_limit(uid):
        return await message.reply_photo(
            SUBSCRIPTION, caption=script.LIMIT_REACHED,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")
            ]]),
            parse_mode=enums.ParseMode.HTML
        )

    # Parse range
    datas = message.text.split("/")
    temp  = datas[-1].replace("?single", "").split("-")
    try:
        fromID = int(temp[0].strip())
    except (ValueError, IndexError):
        return await message.reply_text("❌ <b>Invalid link format.</b>",
                                        parse_mode=enums.ParseMode.HTML)
    try:
        toID = int(temp[1].strip())
    except (ValueError, IndexError):
        toID = fromID

    total_files = toID - fromID + 1
    is_private  = "https://t.me/c/" in message.text
    is_batch    = "https://t.me/b/" in message.text
    is_public   = not is_private and not is_batch

    # Session for private/restricted
    acc = None
    if not is_public:
        session_str = await db.get_session(uid)
        if not session_str:
            return await message.reply(
                "<b>🔒 Login Required</b>\n\n"
                "<i>Use /login to authorize your account first.</i>",
                parse_mode=enums.ParseMode.HTML
            )
        try:
            acc = Client("saverestricted", session_string=session_str,
                         api_hash=API_HASH, api_id=API_ID,
                         in_memory=True, max_concurrent_transmissions=10)
            await acc.start()
        except Exception as e:
            return await message.reply(
                f"<b>❌ Authentication Failed</b>\n\n"
                f"<i>Session expired. Please /logout and /login again.</i>\n"
                f"<code>{e}</code>",
                parse_mode=enums.ParseMode.HTML
            )

    batch_temp.IS_BATCH[uid] = False
    progress_msg = await message.reply_text(
        f"⏳ <b>Initializing...</b>  <code>0 / {total_files}</code>\n"
        f"<blockquote>Starting up, please wait...</blockquote>",
        reply_markup=cancel_markup(uid),
        parse_mode=enums.ParseMode.HTML
    )

    state = UserBatchState(total_files, progress_msg, uid)
    batch_temp.STATES[uid] = state

    if is_private:
        chat_target = int("-100" + datas[4])
    elif is_batch:
        chat_target = datas[4]
    else:
        chat_target = datas[3]

    try:
        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(uid) or state.cancelled:
                break
            state.file_start = time.time()

            if is_public:
                fn = f"Message #{msgid}"
                await _safe_edit(
                    progress_msg,
                    f"⬇️ <b>Copying...</b>  <code>{state.completed_files} / {total_files}</code>\n"
                    f"<blockquote>📄 <b>{fn}</b></blockquote>",
                    markup=cancel_markup(uid)
                )
                try:
                    await client.copy_message(dump_chat, chat_target, msgid)
                    await db.add_traffic(uid)
                except (ChannelInvalid, ChannelPrivate, ChatWriteForbidden):
                    await _safe_edit(progress_msg,
                        "❌ <b>Dump channel error!</b>\n"
                        "<blockquote>Bot was removed or lost admin rights.\n"
                        "Use /setchnl to set a new dump channel.</blockquote>",
                        markup=None)
                    await db.del_dump_chat(uid)
                    state.cancelled = True
                    break
                except Exception as e:
                    logger.warning(f"copy_message failed #{msgid}: {e}")
            else:
                ok = await handle_restricted_content(
                    client, acc, message, chat_target, msgid, dump_chat, state)
                if not ok and state.cancelled:
                    break

            state.completed_files += 1
            await asyncio.sleep(1)

    finally:
        if acc:
            try:
                await acc.stop()
            except Exception:
                pass

        if not state.cancelled:
            await _safe_edit(progress_msg,
                f"✅ <b>Done!</b>  <code>{state.completed_files} / {total_files}</code> files processed.",
                markup=None)
        else:
            await _safe_edit(progress_msg,
                "❌ <b>Process Cancelled Successfully</b>", markup=None)

        batch_temp.IS_BATCH[uid] = True
        batch_temp.STATES.pop(uid, None)


# ── Handle one restricted message ────────────

async def handle_restricted_content(client, acc, message, chat_targ
