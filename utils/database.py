import discord


class Database:

    def __init__(self, bot):
        self._bot = bot

        self._connect()

        self.users = UserDB(self)

    def _connect(self):
        from motor.motor_asyncio import AsyncIOMotorClient

        self._bot.logger.info('[DATABASE] Connecting to Database...')
        self._client = AsyncIOMotorClient(self._bot.cfg.get('Database.ConnectURI'))
        self._bot.logger.info('[DATABASE] Successfully connected to the database!')
        self._database = self._client[self._bot.cfg.get('Database.DatabaseName')]

    async def get_document(self, collection: str, key: str, value: str):
        db_filter = {
            key: value
        }
        return await self._database[collection].find_one(db_filter)

    async def set_document_value(self, collection, filter_key, filer_value, key, value):
        document = await self.get_document(collection, filter_key, filer_value)
        document[key] = value
        db_filter = {
            filter_key: filer_value
        }
        update_operation = {
            "$set": document
        }
        await self._database[collection].update_one(db_filter, update_operation, upsert=False)

    async def set_document_full(self, collection, filter_key, filer_value, document):
        db_filter = {
            filter_key: filer_value
        }
        update_operation = {
            "$set": document
        }
        await self._database[collection].update_one(db_filter, update_operation, upsert=False)

    async def add_document(self, collection, document):
        await self._database[collection].insert_one(document)

    async def get_document_amount(self, collection):
        return await self._database[collection].count_documents({})

    # REFORMAT THE DATABASE                                          hopefully
    async def reformat_database(self):
        users = dict()
        collection = self._database['UserData']
        cursor = collection.find({})
        async for document in cursor:
            g_id = int(document['user_id'])
            if g_id in users:
                continue
            users[g_id] = document

        new_docs = list()

        for key, value in users.items():
            user_doc = {
                'user_id': key,
                'notification': value['notification'],
                'shop_notification': value['shop_notification'],
                'challenges_notification': False
            }
            new_docs.append(user_doc)

        await collection.delete_many({})
        await collection.insert_many(new_docs)


class UserDB:

    def __init__(self, database: Database):
        self._database = database
        self._collection_name = 'UserData'

    async def add(self, user: discord.User):
        if await self._exists(user):
            return
        entry_doc = {
            'user_id': user.id,
            'notification': True,
            'shop_notification': False,
            'challenge_notification': False
        }
        await self._database.add_document(self._collection_name, entry_doc)

    async def _exists(self, user: discord.User):
        return await self._database.get_document(self._collection_name, 'user_id', user.id) is not None

    async def receive_notification(self, user: discord.User):
        if not await self._exists(user):
            await self.add(user)
        return (await self._database.get_document(self._collection_name, 'user_id', user.id))['notification']

    async def set_receive_notification(self, user: discord.User, value: bool):
        if not await self._exists(user):
            await self.add(user)
        await self._database.set_document_value(self._collection_name, 'user_id', user.id, 'notification', value)

    async def receive_shop_notification(self, user: discord.User):
        if not await self._exists(user):
            await self.add(user)
        return (await self._database.get_document(self._collection_name, 'user_id', user.id))['shop_notification']

    async def set_receive_shop_notification(self, user: discord.User, value: bool):
        if not await self._exists(user):
            await self.add(user)
        await self._database.set_document_value(self._collection_name, 'user_id', user.id, 'shop_notification', value)

    async def receive_challenges_notification(self, user: discord.User):
        if not await self._exists(user):
            await self.add(user)
        return (await self._database.get_document(self._collection_name, 'user_id', user.id))['challenges_notification']

    async def set_receive_challenges_notification(self, user: discord.User, value: bool):
        if not await self._exists(user):
            await self.add(user)
        await self._database.set_document_value(self._collection_name, 'user_id', user.id, 'challenges_notification',
                                                value)


class DBConfig:

    def __init__(self, database: Database):
        self._database = database
        self._collection_name = 'Config'

    async def _add(self, key, value):
        if await self._exists(key):
            return
        entry_doc = {
            'key': key,
            'value': value
        }
        await self._database.add_document(self._collection_name, entry_doc)

    async def _exists(self, key):
        return await self._database.get_document(self._collection_name, 'key', key) is not None

    async def get(self, key):
        return await self._database.get_document(self._collection_name, 'key', key)

    async def edit(self, key, new_value):
        await self._database.set_document_value(self._collection_name, 'key', key, 'value', new_value)
