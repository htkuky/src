import motor.motor_asyncio
import datetime
from config import DB_NAME, DB_URI
from logger import LOGGER

logger = LOGGER(__name__)


class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            session=None,
            daily_usage=0,
            limit_reset_time=None
        )

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
        logger.info(f"New user added to DB: {id} - {name}")

    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})
        logger.info(f"User deleted from DB: {user_id}")

    async def set_session(self, id, session):
        await self.col.update_one({'id': int(id)}, {'$set': {'session': session}})

    async def get_session(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('session')

    # Caption Support
    async def set_caption(self, id, caption):
        await self.col.update_one({'id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('caption', None)

    async def del_caption(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'caption': ""}})

    # Thumbnail Support
    async def set_thumbnail(self, id, thumbnail):
        await self.col.update_one({'id': int(id)}, {'$set': {'thumbnail': thumbnail}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('thumbnail', None)

    async def del_thumbnail(self, id):
        await self.col.update_one({'id': int(id)}, {'$unset': {'thumbnail': ""}})

    # UnknownBotz
    # Don't Remove Credit
    # Telegram Channel @UnknownBotz

    # Premium Support
    async def add_premium(self, id, expiry_date):
        await self.col.update_one({'id': int(id)}, {
            '$set': {
                'is_premium': True,
                'premium_expiry': expiry_date,
                'daily_usage': 0,
                'limit_reset_time': None
            }
        })
        logger.info(f"User {id} granted premium until {expiry_date}")

    async def remove_premium(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_premium': False, 'premium_expiry': None}})
        logger.info(f"User {id} removed from premium")

    async def check_premium(self, id):
        user = await self.col.find_one({'id': int(id)})
        if user and user.get('is_premium'):
            return user.get('premium_expiry')
        return None

    async def get_premium_users(self):
        return self.col.find({'is_premium': True})

    # Ban Support
    async def ban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_banned': True}})
        logger.warning(f"User banned: {id}")

    async def unban_user(self, id):
        await self.col.update_one({'id': int(id)}, {'$set': {'is_banned': False}})
        logger.info(f"User unbanned: {id}")

    async def is_banned(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('is_banned', False)

    # Dump Channel Support
    async def set_dump_chat(self, id, chat_id):
        """Set dump channel. Pass None or 0 to clear."""
        if chat_id is None or chat_id == 0:
            await self.col.update_one({'id': int(id)}, {'$unset': {'dump_chat': ""}})
        else:
            await self.col.update_one({'id': int(id)}, {'$set': {'dump_chat': int(chat_id)}})

    async def get_dump_chat(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('dump_chat', None)

    async def del_dump_chat(self, id):
        """Explicitly remove the dump channel for a user."""
        await self.col.update_one({'id': int(id)}, {'$unset': {'dump_chat': ""}})
        logger.info(f"Dump channel removed for user: {id}")

    # Delete/Replace Words Support
    async def set_delete_words(self, id, words):
        await self.col.update_one({'id': int(id)}, {'$addToSet': {'delete_words': {'$each': words}}})

    async def get_delete_words(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('delete_words', [])

    async def remove_delete_words(self, id, words):
        await self.col.update_one({'id': int(id)}, {'$pull': {'delete_words': {'$in': words}}})

    async def set_replace_words(self, id, repl_dict):
        user = await self.col.find_one({'id': int(id)})
        current_repl = user.get('replace_words', {})
        current_repl.update(repl_dict)
        await self.col.update_one({'id': int(id)}, {'$set': {'replace_words': current_repl}})

    async def get_replace_words(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user.get('replace_words', {})

    async def remove_replace_words(self, id, words):
        user = await self.col.find_one({'id': int(id)})
        current_repl = user.get('replace_words', {})
        for w in words:
            current_repl.pop(w, None)
        await self.col.update_one({'id': int(id)}, {'$set': {'replace_words': current_repl}})

    # --------------------------------------------------------
    # Daily Limits (Free User Restriction)
    # --------------------------------------------------------
    async def check_limit(self, id):
        """
        Checks if a user has hit their daily limit.
        Returns: True if BLOCKED (limit reached), False if ALLOWED.
        """
        user = await self.col.find_one({'id': int(id)})
        if not user:
            return False

        # 1. Premium Check: Always allowed
        if user.get('is_premium'):
            return False

        # 2. Check Time Reset
        now = datetime.datetime.now()
        reset_time = user.get('limit_reset_time')

        if reset_time is None or now >= reset_time:
            await self.col.update_one(
                {'id': int(id)},
                {'$set': {'daily_usage': 0, 'limit_reset_time': None}}
            )
            return False

        # 3. Check Count
        usage = user.get('daily_usage', 0)
        if usage >= 10:
            return True

        return False

    async def add_traffic(self, id):
        """
        Increments usage count.
        If it's the first save of the cycle, sets the 24h timer.
        """
        user = await self.col.find_one({'id': int(id)})

        if user.get('is_premium'):
            return

        now = datetime.datetime.now()
        reset_time = user.get('limit_reset_time')

        if reset_time is None:
            new_reset_time = now + datetime.timedelta(hours=24)
            await self.col.update_one(
                {'id': int(id)},
                {'$set': {'daily_usage': 1, 'limit_reset_time': new_reset_time}}
            )
        else:
            await self.col.update_one(
                {'id': int(id)},
                {'$inc': {'daily_usage': 1}}
            )


db = Database(DB_URI, DB_NAME)

# UnknownBotz
# Don't Remove Credit
# Telegram Channel @UnknownBotz
