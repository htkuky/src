# Developed by: UnknownBotz
# Telegram: @UnknownBotz
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from UnknownBotz.strings import COMMANDS_TXT


# ── /settings ────────────────────────────────

@Client.on_message(filters.command("settings") & filters.private)
async def settings_menu(client: Client, message: Message):
    uid = message.from_user.id
    if not await db.is_user_exist(uid):
        await db.add_user(uid, message.from_user.first_name)
    badge = "💎 Premium Member" if await db.check_premium(uid) else "👤 Free User"
    await message.reply_text(
        f"<b>⚙️ Settings Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Account:</b> {badge}\n"
        f"<b>User ID:</b> <code>{uid}</code>\n\n"
        f"<i>Select an option below to customise your experience.</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Commands List",         callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 My Usage Stats",        callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Channel",          callback_data="dump_chat_btn")],
            [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
             InlineKeyboardButton("📝 Caption",   callback_data="caption_btn")],
            [InlineKeyboardButton("❌ Close",                 callback_data="close_btn")],
        ]),
        parse_mode=enums.ParseMode.HTML
    )


# ── /setchnl  ─────────────────────────────────
# FIX 3: forward a message → bot auto-detects the channel

@Client.on_message(filters.command("setchnl") & filters.private)
async def set_dump_channel(client: Client, message: Message):
    uid = message.from_user.id
    if not await db.is_user_exist(uid):
        await db.add_user(uid, message.from_user.first_name)

    # ── If an ID / username was passed directly → use it ──
    if len(message.command) >= 2:
        arg = message.command[1].strip()
        try:
            channel_id = int(arg)
        except ValueError:
            channel_id = arg

        try:
            chat = await client.get_chat(channel_id)
        except Exception as e:
            return await message.reply_text(
                f"❌ <b>Cannot access channel:</b> <code>{e}</code>\n\n"
                "<i>Make sure the bot is a member and the ID/username is correct.</i>",
                parse_mode=enums.ParseMode.HTML
            )
        return await _save_dump_channel(client, message, uid, chat)

    # ── No argument → ask user to forward a message ──
    prompt = await message.reply_text(
        "<b><u>📢 Set Dump Channel</u></b>\n\n"
        "Forward any message from your target channel.\n\n"
        "/cancel — Cancel this process",
        parse_mode=enums.ParseMode.HTML
    )

    try:
        # FIX 3: listen for a forwarded message (pyrofork has .listen())
        response: Message = await client.listen(chat_id=uid, timeout=300)
    except asyncio.TimeoutError:
        return await prompt.edit_text(
            "⏰ <b>Timed out.</b> Process cancelled automatically.",
            parse_mode=enums.ParseMode.HTML
        )

    # Cancel command
    if response.text and response.text.strip() == "/cancel":
        try:
            await response.delete()
        except Exception:
            pass
        return await prompt.edit_text(
            "❌ <b>Process Cancelled.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    # Must be a forwarded message
    if not response.forward_date or not response.forward_from_chat:
        try:
            await response.delete()
        except Exception:
            pass
        return await prompt.edit_text(
            "❌ <b>That's not a forwarded message.</b>\n\n"
            "<i>Please forward any message from the target channel.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    try:
        await response.delete()
    except Exception:
        pass

    chat_id  = response.forward_from_chat.id
    try:
        chat = await client.get_chat(chat_id)
    except Exception as e:
        return await prompt.edit_text(
            f"❌ <b>Could not fetch channel info:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML
        )

    await _save_dump_channel(client, prompt, uid, chat, edit=True)


async def _save_dump_channel(client, message_or_prompt, uid, chat, edit=False):
    """Verify bot is admin and save the dump channel."""
    try:
        me     = await client.get_me()
        member = await client.get_chat_member(chat.id, me.id)
        is_admin = member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER
        )
    except Exception as e:
        text = (
            f"❌ <b>Could not verify bot status:</b> <code>{e}</code>\n\n"
            "<i>Make sure the bot is a member of the channel.</i>"
        )
        if edit:
            return await message_or_prompt.edit_text(text, parse_mode=enums.ParseMode.HTML)
        return await message_or_prompt.reply_text(text, parse_mode=enums.ParseMode.HTML)

    if not is_admin:
        text = (
            "❌ <b>Bot must be admin in the channel</b>\n\n"
            "<i>Please make the bot an administrator, then try again.</i>"
        )
        if edit:
            return await message_or_prompt.edit_text(text, parse_mode=enums.ParseMode.HTML)
        return await message_or_prompt.reply_text(text, parse_mode=enums.ParseMode.HTML)

    await db.set_dump_chat(uid, chat.id)
    title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(chat.id))
    text = (
        f"✅ <b>Dump Channel Set Successfully</b>\n\n"
        f"<b>Channel:</b> {title}\n"
        f"<b>ID:</b> <code>{chat.id}</code>\n\n"
        f"<i>All saved files will be sent to this channel.</i>"
    )
    if edit:
        await message_or_prompt.edit_text(text, parse_mode=enums.ParseMode.HTML)
    else:
        await message_or_prompt.reply_text(text, parse_mode=enums.ParseMode.HTML)


# ── /remchnl ─────────────────────────────────

@Client.on_message(filters.command("remchnl") & filters.private)
async def remove_dump_channel(client: Client, message: Message):
    uid = message.from_user.id
    if not await db.is_user_exist(uid):
        await db.add_user(uid, message.from_user.first_name)
    await db.del_dump_chat(uid)
    await message.reply_text(
        "✅ <b>Dump channel removed successfully</b>",
        parse_mode=enums.ParseMode.HTML
    )


# ── Settings callbacks ────────────────────────

BACK_CLOSE = lambda: [[
    InlineKeyboardButton("⬅️ Back", callback_data="settings_back_btn"),
    InlineKeyboardButton("❌ Close", callback_data="close_btn")
]]

@Client.on_callback_query(
    filters.regex(
        r"^(cmd_list_btn|dump_chat_btn|thumb_btn|caption_btn|user_stats_btn|settings_back_btn|close_btn)$"
    )
)
async def settings_callbacks(client: Client, cq: CallbackQuery):
    data = cq.data
    uid  = cq.from_user.id

    if data == "cmd_list_btn":
        await cq.edit_message_text(
            COMMANDS_TXT,
            reply_markup=InlineKeyboardMarkup(BACK_CLOSE()),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )

    elif data == "dump_chat_btn":
        current = await db.get_dump_chat(uid)
        if current:
            try:
                chat  = await client.get_chat(current)
                title = getattr(chat, 'title', None) or str(current)
            except Exception:
                title = "Unknown (Inaccessible)"
            text = (
                f"<b>🗑 Current Dump Channel</b>\n\n"
                f"<b>ID:</b> <code>{current}</code>\n"
                f"<b>Title:</b> {title}\n\n"
                "<i>Use /setchnl to change or /remchnl to remove.</i>"
            )
        else:
            text = (
                "<b>🗑 No Dump Channel Set</b>\n\n"
                "<i>Use /setchnl to set a dump channel.\n"
                "Forward any message from the target channel.</i>"
            )
        await cq.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(BACK_CLOSE()),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "thumb_btn":
        thumb = await db.get_thumbnail(uid)
        if thumb:
            await cq.message.reply_photo(
                thumb,
                caption="<b>🖼 Your Current Thumbnail</b>\n\n"
                        "<i>Send a new photo to update • /del_thumb to remove</i>",
                parse_mode=enums.ParseMode.HTML
            )
            await cq.answer("Thumbnail sent below 👇")
        else:
            await cq.edit_message_text(
                "<b>🖼 No Thumbnail Set</b>\n\n"
                "<i>Reply to a photo with /set_thumb to set one.</i>",
                reply_markup=InlineKeyboardMarkup(BACK_CLOSE()),
                parse_mode=enums.ParseMode.HTML
            )

    elif data == "caption_btn":
        cap = await db.get_caption(uid)
        if cap:
            preview = cap.format(filename="Video_2024.mp4", size="1.2 GB")
            text = (
                f"<b>📝 Current Caption</b>\n\n"
                f"<code>{cap}</code>\n\n"
                f"<b>Preview:</b>\n{preview}\n\n"
                "<i>Placeholders: {{filename}}, {{size}}\n"
                "/set_caption to change • /del_caption to remove</i>"
            )
        else:
            text = (
                "<b>📝 No Custom Caption Set</b>\n\n"
                "<i>Use /set_caption &lt;text&gt; to set one.\n"
                "Supports {{filename}} and {{size}} placeholders.</i>"
            )
        await cq.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(BACK_CLOSE()),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "user_stats_btn":
        is_premium = await db.check_premium(uid)
        user_data  = await db.col.find_one({'id': int(uid)})
        if is_premium:
            limit_text = "♾️ Unlimited"
            usage_text = "N/A (Premium)"
        else:
            used = (user_data or {}).get('daily_usage', 0)
            limit_text = "10 Files / 24h"
            usage_text = f"{used} / 10"
        await cq.edit_message_text(
            f"<b>📊 My Usage Statistics</b>\n\n"
            f"<b>Plan:</b> {'💎 Premium' if is_premium else '👤 Free'}\n"
            f"<b>Daily Limit:</b> <code>{limit_text}</code>\n"
            f"<b>Today's Usage:</b> <code>{usage_text}</code>\n\n"
            f"<i>Upgrade to Premium for unlimited downloads!</i>",
            reply_markup=InlineKeyboardMarkup(BACK_CLOSE()),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "settings_back_btn":
        badge = "💎 Premium Member" if await db.check_premium(uid) else "👤 Free User"
        await cq.edit_message_text(
            f"<b>⚙️ Settings Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Account:</b> {badge}\n"
            f"<b>User ID:</b> <code>{uid}</code>\n\n"
            f"<i>Select an option below to customise your experience.</i>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📜 Commands List",         callback_data="cmd_list_btn")],
                [InlineKeyboardButton("📊 My Usage Stats",        callback_data="user_stats_btn")],
                [InlineKeyboardButton("🗑 Dump Channel",          callback_data="dump_chat_btn")],
                [InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
                 InlineKeyboardButton("📝 Caption",   callback_data="caption_btn")],
                [InlineKeyboardButton("❌ Close",                 callback_data="close_btn")],
            ]),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "close_btn":
        await cq.message.delete()

    try:
        await cq.answer()
    except Exception:
        pass
        
