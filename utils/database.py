import discord


class Database:

    def __init__(self, bot):
        self._bot = bot

        self._connect()

        self.user = UserDB(self)

    def _connect(self):
        self._bot.logger.info('[DATABASE] Connecting to Database...')
        from pymongo import MongoClient
        self._client = MongoClient(self._bot.cfg.get('Database.ConnectURI'))
        self._bot.logger.info('[DATABASE] Successfully connected to the database!')
        self._database = self._client[self._bot.cfg.get('Database.DatabaseName')]

    def get_document(self, collection: str, key: str, value: str):
        db_filter = {
            key: value
        }
        return self._database[collection].find_one(db_filter)

    def set_document(self, collection, filter_key, filer_value, key, value):
        document = self.get_document(collection, filter_key, filer_value)
        document[key] = value
        db_filter = {
            filter_key: filer_value
        }
        update_operation = {
            "$set": document
        }
        self._database[collection].update_one(db_filter, update_operation, upsert=False)

    def add_document(self, collection, document):
        self._database[collection].insert_one(document)

    def get_document_amount(self, collection):
        return self._database[collection].count_documents({})

    # CLEANUP THE DATABASE                                          hopefully
    def cleanup_database(self):
        guilds = dict()
        collection = self._database['GuildData']
        cursor = collection.find({})
        for document in cursor:
            g_id = str(document['guild_id'])
            if g_id in guilds:
                continue
            lang = document['lang']
            permissions_warn = document['write_warn']
            guilds[g_id] = [lang, permissions_warn]
        collection.delete_many({})
        for key, value in guilds.items():
            lang = value[0].replace('EN', 'en-EN').replace('DE', 'de-DE')
            guild_doc = {
                'guild_id': str(key),
                'lang': lang,
                'has_donator': False,
                'permissions_warn': value[1],
                'br_news_channel': 'none',
                'stw_news_channel': 'none',
                'shop_channel': 'none'
            }
            self.add_document('GuildData', guild_doc)


class UserDB:

    def __init__(self, database: Database):
        self._database = database
        self._collection_name = 'UserData'

    def add(self, user: discord.User):
        if self._exists(user):
            return
        entry_doc = {
            'user_id': str(user.id),
            'notification': True
        }
        self._database.add_document(self._collection_name, entry_doc)

    def _exists(self, user: discord.User):
        return self._database.get_document(self._collection_name, 'user_id', str(user.id)) is not None

    def receive_notification(self, user: discord.User):
        if not self._exists(user):
            self.add(user)
        return self._database.get_document(self._collection_name, 'user_id', str(user.id))['notification']

    def set_receive_notification(self, user: discord.User, value: bool):
        if not self._exists(user):
            self.add(user)
        self._database.set_document(self._collection_name, 'user_id', str(user.id), 'notification', value)


class DBConfig:

    def __init__(self, database: Database):
        self._database = database
        self._collection_name = 'Config'

    def _add(self, key, value):
        if self._exists(key):
            return
        entry_doc = {
            'key': key,
            'value': value
        }
        self._database.add_document(self._collection_name, entry_doc)

    def _exists(self, key):
        return self._database.get_document(self._collection_name, 'key', key) is not None

    def get(self, key):
        return self._database.get_document(self._collection_name, 'key', key)

    def edit(self, key, new_value):
        self._database.set_document(self._collection_name, 'key', key, 'value', new_value)
