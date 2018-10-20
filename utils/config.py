from configparser import ConfigParser


class Config:

    def __init__(self, bot):
        self._bot = bot
        self._config = ConfigParser()
        self._loaded_config = dict()

        self.load()

    def load(self):
        self._config.read('configs/config.ini', encoding='utf-8')

        sections = self._config.sections()
        for section in sections:
            options = self._config.options(section)
            for option in options:
                value = self._config.get(section, option)
                self._loaded_config[f'{section.lower()}.{option.lower()}'] = value

    def get(self, path: str):
        path = path.lower()
        if not self._loaded_config.__contains__(path):
            return None
        return self._loaded_config[path]
