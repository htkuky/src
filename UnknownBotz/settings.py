import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from UnknownBotz.strings import COMMANDS_TXT


# ======================================================
# /settings - Enhanced Professional Settings Menu
# ======================================================

@Client.on_message(filters.command("settings") & filters.private)
async def settings_menu(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    is_premium = await db.check_premium(user_id)
    premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
        [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
        [InlineKeyboardButton("🗑 Dump Channel", callback_data="dump_chat_btn")],
        [
            InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
            InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
        ],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
    ])

    text = (
        f"<b>⚙️ Settings Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<b>Account:</b> {premium_badge}\n"
        f"<b>User ID:</b> <code>{user_id}</code>\n\n"
        f"<i>Select an option below to customize your experience.</i>"
    )
    await message.reply_text(text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML)


# ======================================================
# /commands - Direct Access to Commands List
# ======================================================

@Client.on_message(filters.command("commands") & filters.private)
async def direct_commands(client: Client, message: Message):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚙️ Open Settings", callback_data="settings_back_btn"),
            InlineKeyboardButton("❌ Close", callback_data="close_btn")
        ]
    ])
    await message.reply_text(
        COMMANDS_TXT,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )


# ======================================================
# /setchnl  — Set Dump Channel
# Bot must be admin in the channel.
# ======================================================

@Client.on_message(filters.command("setchnl") & filters.private)
async def set_dump_channel(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    if len(message.command) < 2:
        return await message.reply_text(
            "<b>📢 Set Dump Channel</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/setchnl &lt;channel_id&gt;</code> — numeric ID\n"
            "<code>/setchnl @username</code>     — public username\n\n"
            "<i>⚠️ The bot must be an admin in the channel.</i>\n"
            "<i>Example: /setchnl -1001234567890</i>",
            parse_mode=enums.ParseMode.HTML
        )

    arg = message.command[1].strip()

    # Resolve channel_id: integer or @username
    try:
        channel_identifier = int(arg)
    except ValueError:
        channel_identifier = arg  # @username or t.me link

    try:
        chat = await client.get_chat(channel_identifier)
    except Exception as e:
        return await message.reply_text(
            f"❌ <b>Cannot access channel:</b> <code>{e}</code>\n\n"
            "<i>Make sure the bot is a member and the ID/username is correct.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    # Verify bot is admin
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat.id, me.id)
        is_admin = member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER
        )
    except Exception as e:
        return await message.reply_text(
            f"❌ <b>Could not verify bot status in channel:</b> <code>{e}</code>",
            parse_mode=enums.ParseMode.HTML
        )

    if not is_admin:
        return await message.reply_text(
            "❌ <b>Bot must be admin in the channel</b>\n\n"
            "<i>Please make the bot an administrator first, then try again.</i>",
            parse_mode=enums.ParseMode.HTML
        )

    await db.set_dump_chat(user_id, chat.id)
    chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', str(chat.id))

    await message.reply_text(
        f"✅ <b>Dump Channel Set Successfully</b>\n\n"
        f"<b>Channel:</b> {chat_title}\n"
        f"<b>ID:</b> <code>{chat.id}</code>\n\n"
        f"<i>All saved files will be sent to this channel.</i>",
        parse_mode=enums.ParseMode.HTML
    )


# ======================================================
# /remchnl  — Remove Dump Channel
# ======================================================

@Client.on_message(filters.command("remchnl") & filters.private)
async def remove_dump_channel(client: Client, message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

    await db.del_dump_chat(user_id)
    await message.reply_text(
        "✅ <b>Dump channel removed successfully</b>",
        parse_mode=enums.ParseMode.HTML
    )


# ======================================================
# Settings Callbacks — Full Navigation
# ======================================================

@Client.on_callback_query(
    filters.regex(
        r"^(cmd_list_btn|dump_chat_btn|thumb_btn|caption_btn|user_stats_btn|settings_back_btn|close_btn)$"
    )
)
async def settings_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    back_close = [[
        InlineKeyboardButton("⬅️ Back", callback_data="settings_back_btn"),
        InlineKeyboardButton("❌ Close", callback_data="close_btn")
    ]]

    if data == "cmd_list_btn":
        await callback_query.edit_message_text(
            COMMANDS_TXT,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )

    elif data == "dump_chat_btn":
        current = await db.get_dump_chat(user_id)
        if current:
            try:
                chat = await client.get_chat(current)
                title = getattr(chat, 'title', None) or str(current)
            except Exception:
                title = "Unknown (Inaccessible)"
            text = (
                f"<b>🗑 Current Dump Channel</b>\n\n"
                f"<b>Channel ID:</b> <code>{current}</code>\n"
                f"<b>Title:</b> {title}\n\n"
                "<i>All saved files are sent here.</i>\n"
                "<i>Use /setchnl to change or /remchnl to remove.</i>"
            )
        else:
            text = (
                "<b>🗑 No Dump Channel Set</b>\n\n"
                "<i>You must set a dump channel before saving files.</i>\n"
                "<i>Use /setchnl &lt;channel_id&gt; to set one.</i>"
            )
        await callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "thumb_btn":
        thumb = await db.get_thumbnail(user_id)
        if thumb:
            await callback_query.message.reply_photo(
                thumb,
                caption=(
                    "<b>🖼 Your Current Custom Thumbnail</b>\n\n"
                    "<i>Send a new photo to update • /del_thumb to remove</i>"
                ),
                parse_mode=enums.ParseMode.HTML
            )
            await callback_query.answer("Thumbnail preview sent below 👇")
        else:
            await callback_query.edit_message_text(
                "<b>🖼 No Custom Thumbnail Set</b>\n\n"
                "<i>Send a photo to set as default thumbnail for uploads.</i>",
                reply_markup=InlineKeyboardMarkup(back_close),
                parse_mode=enums.ParseMode.HTML
            )

    elif data == "caption_btn":
        caption = await db.get_caption(user_id)
        if caption:
            preview = caption.format(filename="Video_File_2024.mp4", size="1.2 GB")
            text = (
                f"<b>📝 Current Custom Caption</b>\n\n"
                f"<code>{caption}</code>\n\n"
                f"<b>Preview:</b>\n{preview}\n\n"
                "<i>Placeholders: {filename}, {size}</i>\n"
                "<i>/set_caption &lt;text&gt; to change • /del_caption to remove</i>"
            )
        else:
            text = (
                "<b>📝 No Custom Caption Set</b>\n\n"
                "<i>Use /set_caption &lt;text&gt; to set one.</i>\n"
                "<i>Supports {filename} and {size} placeholders.</i>"
            )
        await callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "user_stats_btn":
        is_premium = await db.check_premium(user_id)
        user_data = await db.col.find_one({'id': int(user_id)})

        if is_premium:
            limit_text = "♾️ Unlimited"
            usage_text = "Ignored (Premium)"
        else:
            daily_limit = 10
            used = user_data.get('daily_usage', 0) if user_data else 0
            limit_text = f"{daily_limit} Files / 24h"
            usage_text = f"{used} / {daily_limit}"

        text = (
            f"<b>📊 My Usage Statistics</b>\n\n"
            f"<b>Plan:</b> {'💎 Premium' if is_premium else '👤 Free'}\n"
            f"<b>Daily Limit:</b> <code>{limit_text}</code>\n"
            f"<b>Today's Usage:</b> <code>{usage_text}</code>\n\n"
            f"<i>Upgrade to Premium for unlimited downloads!</i>"
        )
        await callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(back_close),
            parse_mode=enums.ParseMode.HTML
        )

    elif data == "settings_back_btn":
        is_premium = await db.check_premium(user_id)
        premium_badge = "💎 Premium Member" if is_premium else "👤 Free User"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📜 Commands List", callback_data="cmd_list_btn")],
            [InlineKeyboardButton("📊 My Usage Stats", callback_data="user_stats_btn")],
            [InlineKeyboardButton("🗑 Dump Channel", callback_data="dump_chat_btn")],
            [
                InlineKeyboardButton("🖼 Thumbnail", callback_data="thumb_btn"),
                InlineKeyboardButton("📝 Caption", callback_data="caption_btn")
            ],
            [InlineKeyboardButton("❌ Close Menu", callback_data="close_btn")]
        ])

        text = (
            f"<b>⚙️ Settings Panel</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>Account:</b> {premium_badge}\n"
            f"<b>User ID:</b> <code>{user_id}</code>\n\n"
            f"<i>Select an option below to customize your experience.</i>"
        )
        await callback_query.edit_message_text(
            text, reply_markup=buttons, parse_mode=enums.ParseMode.HTML
        )

    elif data == "close_btn":
        await callback_query.message.delete()

    try:
        await callback_query.answer()
    except Exception:
        pass
