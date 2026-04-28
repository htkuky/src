# Developed by: UnknownBotz
# Telegram: @UnknownBotz | @THEUPDATEDGUYS
import os
import asyncio
import random
import time
import shutil
import hashlib
import requests
from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant,
    InviteHashExpired, UsernameNotOccupied, AuthKeyUnregistered,
    UserDeactivated, UserDeactivatedBan, MessageNotModified
)
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    Message, CallbackQuery, InputMediaPhoto
)
from config import API_ID, API_HASH, ERROR_MESSAGE
from database.db import db
from logger import LOGGER

logger = LOGGER(__name__)

SUBSCRIPTION = os.environ.get('SUBSCRIPTION', 'https://graph.org/file/242b7f1b52743938d81f1.jpg')
FREE_LIMIT_SIZE = 2 * 1024 * 1024 * 1024
FREE_LIMIT_DAILY = 10
UPI_ID = os.environ.get("UPI_ID", "your_upi@oksbi")
QR_CODE = os.environ.get("QR_CODE", "https://graph.org/file/242b7f1b52743938d81f1.jpg")

REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬",
    "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱",
    "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌",
    "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈", "😴",
    "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨", "🤝",
    "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿", "🆒",
    "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂️", "🤷‍♀️",
    "😡"
]

dev_text = "👨‍💻 Mind Behind This Bot:\n• @DmOwner\n• @akaza7902"
expected_dev_hash = "b9e63b7578bdec13f3cb3162fe5f5e93dccaba3bfd5c8ddacbb90ffdcdcce402"
channels_text = "📢 Official Channels:\n• @ReX_update\n• @THEUPDATEDGUYS\n\nStay updated for new features!"
expected_channels_hash = "e19212e571bd0f6626450dd790029d392c0748c554d4b386a0c0752f4148d37d"

if (
    hashlib.sha256(dev_text.encode('utf-8')).hexdigest() != expected_dev_hash or
    hashlib.sha256(channels_text.encode('utf-8')).hexdigest() != expected_channels_hash
):
    raise Exception("Tampered developer info detected! Bot will not start.")


# ─────────────────────────────────────────────
# Helper: human readable sizes / time
# ─────────────────────────────────────────────

def humanbytes(size: int) -> str:
    if not size:
        return "0B"
    power = 2 ** 10
    n = 0
    labels = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {labels[n]}B"


def TimeFormatter(milliseconds: int) -> str:
    seconds, _ = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = (
        (f"{days}d, " if days else "") +
        (f"{hours}h, " if hours else "") +
        (f"{minutes}m, " if minutes else "") +
        (f"{seconds}s, " if seconds else "")
    )
    return parts[:-2] if parts else "0s"


# ─────────────────────────────────────────────
# Static texts
# ─────────────────────────────────────────────

class script:
    START_TXT = """<b>👋 Hello {},</b>
<b>🤖 I am <a href=https://t.me/{}>{}</a></b>
<i>Your Professional Restricted Content Saver Bot.</i>
<blockquote><b>🚀 System Status: 🟢 Online</b>
<b>⚡ Performance: 10x High-Speed Processing</b>
<b>🔐 Security: End-to-End Encrypted</b>
<b>📊 Uptime: 99.9% Guaranteed</b></blockquote>
<b>👇 Select an Option Below to Get Started:</b>
"""

    HELP_TXT = """<b>📚 Comprehensive Help & User Guide</b>
<blockquote><b>1️⃣ Public Channels (No Login Required)</b></blockquote>
• Forward or send the post link directly.
• Compatible with any public channel or group.
• <i>Example Link:</i> <code>https://t.me/channel/123</code>
<blockquote><b>2️⃣ Private/Restricted Channels (Login Required)</b></blockquote>
• Use <code>/login</code> to securely connect your Telegram account.
• Send the private link (e.g., <code>t.me/c/123...</code>).
• Bot accesses content using your authenticated session.
<blockquote><b>3️⃣ Batch Downloading Mode</b></blockquote>
• Send a range link like <code>https://t.me/channel/100-200</code>.
• Real-time progress bar with cancel support.
<blockquote><b>🗑 Dump Channel (Required)</b></blockquote>
• Set your dump channel with <code>/setchnl</code> before saving files.
• Bot must be an admin in the channel.
<blockquote><b>🛑 Free User Limitations:</b></blockquote>
• <b>Daily Quota:</b> 10 Files / 24 Hours
• <b>File Size Cap:</b> 2GB Maximum
<blockquote><b>💎 Premium Membership Benefits:</b></blockquote>
• Unlimited Downloads & No Restrictions.
• Priority Support & Advanced Features.
"""

    ABOUT_TXT = """<b>ℹ️ About This Bot</b>
<blockquote><b>╭────[ 🧩 Technical Stack ]────⍟</b>
<b>├⍟ 🤖 Bot Name : <a href=http://t.me/THEUPDATEDGUYS_Bot>Save Content</a></b>
<b>├⍟ 👨‍💻 Developer : <a href=https://t.me/DmOwner>Ⓜ️ark X UnknownBotz</a></b>
<b>├⍟ 📚 Library : <a href='https://docs.pyrogram.org/'>Pyrogram Async</a></b>
<b>├⍟ 🐍 Language : <a href='https://www.python.org/'>Python 3.11+</a></b>
<b>├⍟ 🗄 Database : <a href='https://www.mongodb.com/'>MongoDB Atlas Cluster</a></b>
<b>├⍟ 📡 Hosting : Dedicated High-Speed VPS</b>
<b>╰───────────────⍟</b></blockquote>
"""

    PREMIUM_TEXT = """<b>💎 Premium Membership Plans</b>
<b>Unlock Unlimited Access & Advanced Features!</b>
<blockquote><b>✨ Key Benefits:</b>
<b>♾️ Unlimited Daily Downloads</b>
<b>📂 Support for 4GB+ File Sizes</b>
<b>⚡ Instant Processing (Zero Delay)</b>
<b>🖼 Customizable Thumbnails</b>
<b>📝 Personalized Captions</b>
<b>🛂 24/7 Priority Support</b></blockquote>
<blockquote><b>💳 Pricing Options:</b></blockquote>
• <b>1 Month Plan:</b> ₹50 / $1 (Billed Monthly)
• <b>3 Month Plan:</b> ₹120 / $2.5 (Save 20%)
• <b>Lifetime Access:</b> ₹200 / $4 (One-Time Payment)
<blockquote><b>👇 Secure Payment:</b></blockquote>
<b>💸 UPI ID:</b> <code>{}</code>
<b>📸 QR Code:</b> <a href='{}'>Scan to Pay</a>
<i>After Payment: Send Screenshot to Admin for Instant Activation.</i>
"""

    CAPTION = """<b><a href="https://t.me/THEUPDATEDGUYS"></a></b>\n\n<b>⚜️ Powered By : <a href="https://t.me/THEUPDATEDGUYS">THE UPDATED GUYS 😎</a></b>"""

    LIMIT_REACHED = """<b>🚫 Daily Limit Exceeded</b>
<b>Your 10 free saves for today have been used.</b>
<i>Quota resets automatically after 24 hours from first download.</i>
<blockquote><b>🔓 Upgrade to Premium for Unlimited Access!</b></blockquote>
Remove all restrictions and enjoy seamless downloading.
"""

    SIZE_LIMIT = """<b>⚠️ File Size Exceeded</b>
<b>Free tier limited to 2GB per file.</b>
<blockquote><b>🔓 Upgrade to Premium</b></blockquote>
Download files up to 4GB and beyond with no limits!
"""


# ─────────────────────────────────────────────
# Batch State Management
# ─────────────────────────────────────────────

class UserBatchState:
    """Holds per-user batch processing state."""

    def __init__(self, total_files: int, progress_msg: Message, user_id: int):
        self.total_files = total_files
        self.completed_files = 0
        self.cancelled = False
        self.progress_msg = progress_msg
        self.user_id = user_id
        self.batch_start_time = time.time()
        self.file_start_time = time.time()
        self.last_edit_time = 0.0
        self.current_filename = "Initializing..."
        self.processed_bytes = 0


class batch_temp:
    IS_BATCH: dict = {}   # user_id -> True (cancelled) | False (running)
    STATES: dict = {}     # user_id -> UserBatchState


def get_cancel_markup(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_batch_{user_id}")
    ]])


async def _safe_edit(msg: Message, text: str, markup=None, parse_mode=enums.ParseMode.HTML):
    """Edit a message, silently ignoring MessageNotModified and other minor errors."""
    try:
        await msg.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
    except MessageNotModified:
        pass
    except Exception:
        pass


async def batch_progress_callback(
    current: int,
    total: int,
    state: UserBatchState,
    filename: str,
    operation: str
):
    """
    Async progress callback for Pyrogram download/upload.
    Updates the shared progress message with real-time stats.
    Rate-limited to one edit every 3 seconds.
    """
    # Check cancellation first
    if state.cancelled or batch_temp.IS_BATCH.get(state.user_id, True):
        raise Exception("Cancelled")

    now = time.time()

    # Rate-limit: update at most once every 3 seconds (except on completion)
    if now - state.last_edit_time < 3 and current != total:
        return

    state.last_edit_time = now

    elapsed = now - state.file_start_time
    speed = current / elapsed if elapsed > 0 else 0
    eta_seconds = (total - current) / speed if speed > 0 else 0
    pct = current * 100 / total if total > 0 else 0

    text = (
        f"⚡ <b>Processing Task...</b> {state.completed_files} / {state.total_files}\n"
        f"{filename}\n"
        f"Progress: {pct:.1f}%\n"
        f"🚀 Speed: {humanbytes(int(speed))}/s\n"
        f"💾 Size: {humanbytes(current)} of {humanbytes(total)}\n"
        f"⏱ Elapsed: {TimeFormatter(int(elapsed * 1000))}\n"
        f"⏳ ETA: {TimeFormatter(int(eta_seconds * 1000))}"
    )

    await _safe_edit(state.progress_msg, text, markup=get_cancel_markup(state.user_id))


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_message_type(msg):
    if getattr(msg, 'document', None):
        return "Document"
    if getattr(msg, 'video', None):
        return "Video"
    if getattr(msg, 'photo', None):
        return "Photo"
    if getattr(msg, 'audio', None):
        return "Audio"
    if getattr(msg, 'text', None):
        return "Text"
    return None


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except:
        pass

    apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
    api_url = random.choice(apis)
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        photo_url = response.json()["url"]
    except Exception as e:
        logger.error(f"Failed to fetch image from API: {e}")
        photo_url = "https://i.postimg.cc/kX9tjGXP/16.png"

    buttons = [
        [
            InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
            InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
        ],
        [
            InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
            InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
        ],
        [
            InlineKeyboardButton('📢 Channels', callback_data="channels_info"),
            InlineKeyboardButton('👨‍💻 Developers', callback_data="dev_info")
        ]
    ]
    bot = await client.get_me()
    await client.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=script.START_TXT.format(
            message.from_user.mention, bot.username, bot.first_name
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        reply_to_message_id=message.id,
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    buttons = [[InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]]
    await client.send_message(
        chat_id=message.chat.id,
        text=script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# /plan  /myplan  /premium
# ─────────────────────────────────────────────

@Client.on_message(filters.command(["plan", "myplan", "premium"]))
async def send_plan(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton("📸 Send Payment Proof", url="https://t.me/DmOwner")],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ]
    await client.send_photo(
        chat_id=message.chat.id,
        photo=SUBSCRIPTION,
        caption=script.PREMIUM_TEXT.format(UPI_ID, QR_CODE),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# /cancel  — cancel ongoing batch
# ─────────────────────────────────────────────

@Client.on_message(filters.command("cancel"))
async def send_cancel(client: Client, message: Message):
    user_id = message.from_user.id
    batch_temp.IS_BATCH[user_id] = True
    state = batch_temp.STATES.get(user_id)
    if state:
        state.cancelled = True
    await message.reply_text("❌ <b>Process Cancelled Successfully</b>", parse_mode=enums.ParseMode.HTML)


# ─────────────────────────────────────────────
# Inline cancel button callback
# ─────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^cancel_batch_\d+$"), group=0)
async def cancel_batch_callback(client: Client, callback_query: CallbackQuery):
    parts = callback_query.data.split("_")
    target_user_id = int(parts[-1])
    requester_id = callback_query.from_user.id

    # Only the owner of the task (or admins) can cancel
    if requester_id != target_user_id:
        await callback_query.answer("⛔ You can't cancel someone else's task!", show_alert=True)
        return

    batch_temp.IS_BATCH[target_user_id] = True
    state = batch_temp.STATES.get(target_user_id)
    if state:
        state.cancelled = True

    try:
        await callback_query.message.edit_text(
            "❌ <b>Process Cancelled Successfully</b>",
            reply_markup=None,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        pass

    await callback_query.answer("✅ Cancelled!")


# ─────────────────────────────────────────────
# Settings panel helper
# ─────────────────────────────────────────────

async def settings_panel(client, callback_query):
    user_id = callback_query.from_user.id
    is_premium = await db.check_premium(user_id)
    badge = "💎 Premium Member" if is_premium else "👤 Standard User"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Command List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Channel Settings", callback_data="dump_chat_btn")],
        [InlineKeyboardButton("🖼 Manage Thumbnail", callback_data="thumb_btn")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data="caption_btn")],
        [InlineKeyboardButton("⬅️ Return to Home", callback_data="start_btn")]
    ])

    text = (
        f"<b>⚙️ Settings Dashboard</b>\n\n"
        f"<b>Account Status:</b> {badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Customize and manage your bot preferences below for an optimized experience:</i>"
    )

    await callback_query.edit_message_caption(
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )


# ─────────────────────────────────────────────
# Main save handler (triggered by t.me links)
# ─────────────────────────────────────────────

@Client.on_message(filters.text & filters.private & ~filters.regex("^/"))
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return

    user_id = message.from_user.id

    # ── Limit check ──
    is_limit_reached = await db.check_limit(user_id)
    if is_limit_reached:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")
        ]])
        return await message.reply_photo(
            photo=SUBSCRIPTION,
            caption=script.LIMIT_REACHED,
            reply_markup=btn,
            parse_mode=enums.ParseMode.HTML
        )

    # ── Prevent concurrent batch ──
    if batch_temp.IS_BATCH.get(user_id) is False:
        return await message.reply_text(
            "<b>⚠️ A Task is Currently Processing.</b>\n"
            "<i>Please wait for completion or press ❌ Cancel in the progress message.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    # ── Require dump channel ──
    dump_chat = await db.get_dump_chat(user_id)
    if not dump_chat:
        return await message.reply_text(
            "⚠️ <b>Please set dump channel first using /setchnl</b>",
            parse_mode=enums.ParseMode.HTML
        )

    # ── Parse URL range ──
    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    try:
        fromID = int(temp[0].strip())
    except (ValueError, IndexError):
        return await message.reply_text("❌ <b>Invalid link format.</b>", parse_mode=enums.ParseMode.HTML)

    try:
        toID = int(temp[1].strip())
    except (ValueError, IndexError):
        toID = fromID

    total_files = toID - fromID + 1

    is_private_link = "https://t.me/c/" in message.text
    is_batch_link = "https://t.me/b/" in message.text
    is_public_link = not is_private_link and not is_batch_link

    # ── For non-public links, set up user session ──
    acc = None
    if not is_public_link:
        user_data = await db.get_session(user_id)
        if user_data is None:
            return await message.reply(
                "<b>🔒 Authentication Required</b>\n\n"
                "<i>Access to this content requires login.</i>\n"
                "<i>Use /login to securely authorize your account.</i>",
                parse_mode=enums.ParseMode.HTML
            )
        try:
            acc = Client(
                "saverestricted",
                session_string=user_data,
                api_hash=API_HASH,
                api_id=API_ID,
                in_memory=True,
                max_concurrent_transmissions=10
            )
            await acc.start()
        except Exception as e:
            return await message.reply(
                f"<b>❌ Authentication Failed</b>\n\n"
                f"<i>Your session may have expired. Please /logout and /login again.</i>\n"
                f"<code>{e}</code>",
                parse_mode=enums.ParseMode.HTML
            )

    # ── Mark as running ──
    batch_temp.IS_BATCH[user_id] = False

    # ── Send initial progress message ──
    progress_msg = await message.reply_text(
        f"⚡ <b>Processing Task...</b> 0 / {total_files}\nInitializing...",
        reply_markup=get_cancel_markup(user_id),
        parse_mode=enums.ParseMode.HTML
    )

    # ── Create batch state ──
    state = UserBatchState(
        total_files=total_files,
        progress_msg=progress_msg,
        user_id=user_id
    )
    batch_temp.STATES[user_id] = state

    # ── Determine chat target ──
    if is_private_link:
        chat_target = int("-100" + datas[4])
    elif is_batch_link:
        chat_target = datas[4]
    else:
        chat_target = datas[3]

    # ── Process each message ──
    try:
        for msgid in range(fromID, toID + 1):
            if batch_temp.IS_BATCH.get(user_id) or state.cancelled:
                break

            state.file_start_time = time.time()

            if is_public_link:
                # Public: use fast copy_message
                filename = f"Message #{msgid}"
                state.current_filename = filename
                await _safe_edit(
                    progress_msg,
                    f"⚡ <b>Processing Task...</b> {state.completed_files} / {total_files}\n"
                    f"{filename}\nProgress: —\n🚀 Speed: —\n💾 Size: —\n⏱ Elapsed: —\n⏳ ETA: —",
                    markup=get_cancel_markup(user_id)
                )
                try:
                    await client.copy_message(
                        chat_id=dump_chat,
                        from_chat_id=chat_target,
                        message_id=msgid
                    )
                    await db.add_traffic(user_id)
                except Exception as e:
                    logger.warning(f"copy_message failed for {msgid}: {e}")
            else:
                # Private/restricted: download → upload
                await handle_restricted_content(
                    client=client,
                    acc=acc,
                    message=message,
                    chat_target=chat_target,
                    msgid=msgid,
                    dump_chat=dump_chat,
                    state=state
                )

            state.completed_files += 1
            await asyncio.sleep(1)

    finally:
        # ── Cleanup user session ──
        if acc:
            try:
                await acc.stop()
            except Exception:
                pass

        # ── Final status ──
        if state.cancelled or batch_temp.IS_BATCH.get(user_id):
            await _safe_edit(
                progress_msg,
                "❌ <b>Process Cancelled Successfully</b>",
                markup=None
            )
        else:
            await _safe_edit(
                progress_msg,
                f"✅ <b>Done!</b> {state.completed_files} / {total_files} files processed.",
                markup=None
            )

        # ── Mark as done ──
        batch_temp.IS_BATCH[user_id] = True
        batch_temp.STATES.pop(user_id, None)


# ─────────────────────────────────────────────
# Handle restricted content (one message)
# ─────────────────────────────────────────────

async def handle_restricted_content(
    client: Client,
    acc,
    message: Message,
    chat_target,
    msgid: int,
    dump_chat: int,
    state: UserBatchState
):
    user_id = message.from_user.id

    try:
        msg: Message = await acc.get_messages(chat_target, msgid)
    except Exception as e:
        logger.error(f"Error fetching message {msgid}: {e}")
        return

    if not msg or msg.empty:
        return

    msg_type = get_message_type(msg)
    if not msg_type:
        return

    # ── File size check ──
    file_size = 0
    if msg_type == "Document":
        file_size = msg.document.file_size
    elif msg_type == "Video":
        file_size = msg.video.file_size
    elif msg_type == "Audio":
        file_size = msg.audio.file_size

    if file_size > FREE_LIMIT_SIZE:
        if not await db.check_premium(user_id):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 Upgrade to Premium", callback_data="buy_premium")
            ]])
            await client.send_message(
                dump_chat,
                script.SIZE_LIMIT,
                reply_markup=btn,
                parse_mode=enums.ParseMode.HTML
            )
            return

    # ── Text messages ──
    if msg_type == "Text":
        try:
            await client.send_message(
                dump_chat, msg.text,
                entities=msg.entities,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass
        return

    await db.add_traffic(user_id)

    # ── Determine filename ──
    if msg_type == "Document":
        filename = msg.document.file_name or f"document_{msgid}"
    elif msg_type == "Video":
        filename = msg.video.file_name or f"video_{msgid}.mp4"
    elif msg_type == "Audio":
        filename = msg.audio.file_name or f"audio_{msgid}.mp3"
    else:
        filename = f"photo_{msgid}.jpg"

    state.current_filename = filename

    # ── Download ──
    temp_dir = f"downloads/{user_id}_{msgid}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        file = await acc.download_media(
            msg,
            file_name=f"{temp_dir}/",
            progress=batch_progress_callback,
            progress_args=[state, filename, "down"]
        )
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if state.cancelled or "Cancelled" in str(e):
            return
        logger.error(f"Download failed for {msgid}: {e}")
        return

    if not file:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Reset timer for upload phase
    state.file_start_time = time.time()

    # ── Thumbnail ──
    ph_path = None
    thumb_id = await db.get_thumbnail(user_id)
    if thumb_id:
        try:
            ph_path = await client.download_media(
                thumb_id, file_name=f"{temp_dir}/custom_thumb.jpg"
            )
        except Exception as e:
            logger.error(f"Failed to download custom thumb: {e}")

    if not ph_path:
        try:
            if msg_type == "Video" and msg.video.thumbs:
                ph_path = await acc.download_media(
                    msg.video.thumbs[0].file_id,
                    file_name=f"{temp_dir}/thumb.jpg"
                )
            elif msg_type == "Document" and msg.document.thumbs:
                ph_path = await acc.download_media(
                    msg.document.thumbs[0].file_id,
                    file_name=f"{temp_dir}/thumb.jpg"
                )
        except Exception:
            pass

    # ── Caption ──
    custom_caption = await db.get_caption(user_id)
    if custom_caption:
        final_caption = custom_caption.format(
            filename=filename, size=humanbytes(file_size)
        )
    else:
        final_caption = script.CAPTION
        if msg.caption:
            final_caption += f"\n\n{msg.caption}"

    # ── Upload to dump channel ──
    try:
        if msg_type == "Document":
            await client.send_document(
                dump_chat, file,
                thumb=ph_path, caption=final_caption,
                progress=batch_progress_callback,
                progress_args=[state, filename, "up"]
            )
        elif msg_type == "Video":
            await client.send_video(
                dump_chat, file,
                duration=msg.video.duration,
                width=msg.video.width,
                height=msg.video.height,
                thumb=ph_path, caption=final_caption,
                progress=batch_progress_callback,
                progress_args=[state, filename, "up"]
            )
        elif msg_type == "Audio":
            await client.send_audio(
                dump_chat, file,
                thumb=ph_path, caption=final_caption,
                progress=batch_progress_callback,
                progress_args=[state, filename, "up"]
            )
        elif msg_type == "Photo":
            await client.send_photo(
                dump_chat, file, caption=final_caption
            )
    except Exception as e:
        if not (state.cancelled or "Cancelled" in str(e)):
            logger.error(f"Upload failed for {msgid}: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ─────────────────────────────────────────────
# Callback router
# ─────────────────────────────────────────────

@Client.on_callback_query(group=1)
async def button_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    message = callback_query.message
    if not message:
        return

    # Skip cancel_batch — handled by separate handler above
    if data.startswith("cancel_batch_"):
        return

    if data == "dev_info":
        await callback_query.answer(text=dev_text, show_alert=True)

    elif data == "channels_info":
        await callback_query.answer(text=channels_text, show_alert=True)

    elif data == "settings_btn":
        await settings_panel(client, callback_query)

    elif data == "buy_premium":
        buttons = [
            [InlineKeyboardButton("📸 Send Payment Proof", url="https://t.me/DmOwner")],
            [InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=SUBSCRIPTION,
                caption=script.PREMIUM_TEXT.format(UPI_ID, QR_CODE)
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "help_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "about_btn":
        buttons = [[InlineKeyboardButton("⬅️ Back to Home", callback_data="start_btn")]]
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.id,
            caption=script.ABOUT_TXT,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "start_btn":
        bot = await client.get_me()
        apis = ["https://api.waifu.pics/sfw/waifu", "https://nekos.life/api/v2/img/waifu"]
        api_url = random.choice(apis)
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            photo_url = response.json()["url"]
        except Exception:
            photo_url = "https://i.postimg.cc/cC7txyhz/15.png"

        buttons = [
            [
                InlineKeyboardButton("💎 Buy Premium", callback_data="buy_premium"),
                InlineKeyboardButton("🆘 Help & Guide", callback_data="help_btn")
            ],
            [
                InlineKeyboardButton("⚙️ Settings Panel", callback_data="settings_btn"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_btn")
            ],
            [
                InlineKeyboardButton('📢 Channels', callback_data="channels_info"),
                InlineKeyboardButton('👨‍💻 Developers', callback_data="dev_info")
            ]
        ]
        await client.edit_message_media(
            chat_id=message.chat.id,
            message_id=message.id,
            media=InputMediaPhoto(
                media=photo_url,
                caption=script.START_TXT.format(
                    callback_query.from_user.mention, bot.username, bot.first_name
                )
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "close_btn":
        await message.delete()

    try:
        await callback_query.answer()
    except Exception:
        pass
