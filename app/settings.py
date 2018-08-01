import configparser

class Settings(object):
    def __init__(self, settings_file):
        self.settings_file = settings_file
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.read(self.settings_file)

        self.IMGUR = 'imgur'
        self.TWITTER = 'twitter'
        self.CONFIGS = 'configs'
        self.MONGODB = 'mongodb'
        self.LOGGING = 'logging'

    def read_logging(self):
        return self.config[self.LOGGING]['logging']

    def read_twitter_consumer_key(self):
        return self.config[self.TWITTER]['consumerkey']

    def read_twitter_consumer_secret(self):
        return self.config[self.TWITTER]['consumersecret']

    def read_twitter_access_token(self):
        return self.config[self.TWITTER]['accesstoken']

    def read_twitter_access_token_secret(self):
        return self.config[self.TWITTER]['accesstokensecret']

    def write_last_mention_id(self, id):
        """ Save to file the last mention id.
        :param id: last mention id
        :return:
        """
        self.config[self.CONFIGS]['lastmentionid'] = str(id)
        self._write()

    def _write(self):
        with open(self.settings_file, 'w') as configfile:
            self.config.write(configfile)

    NO_MENTIONS = 1
    def read_last_mention_id(self):
        try:
            return self.config[self.CONFIGS]['lastmentionid']
        except KeyError:
            return self.NO_MENTIONS

    def read_stopwords(self):
        stopwords = {}
        if bool(self.config[self.CONFIGS]['stopwords']) is True:
            file_str = 'assets/stopwords-{0}.txt'
            langs = ['de', 'en', 'es', 'fr', 'it']
            for l in langs:
                stopwords[l] = {}
                with open(file_str.format(l), 'r') as f:
                    for line in f.readlines():
                        stopwords[l][line[:-1]] = 1
            return stopwords
        else:
            return stopwords

    def read_imgur_client_id(self):
        return self.config[self.IMGUR]['clientid']

    def read_imgur_client_secret(self):
        return self.config[self.IMGUR]['clientsecret']

    def read_imgur_access_token(self):
        return self.config[self.IMGUR]['accesstoken']

    def read_imgur_refresh_token(self):
        return self.config[self.IMGUR]['refreshtoken']

    def read_bot_name(self):
        return self.config[self.CONFIGS]['botname']

    def read_wordcloud_hashtags(self):
        return self.config[self.CONFIGS]['wordcloudhashtag'].split(',')

    def read_description_image_str(self):
        return self.config[self.CONFIGS]['descriptionimagestr']    

    def read_output_dir(self):
        return self.config[self.CONFIGS]['outputdir']

    def read_working_dir(self):
        return self.config[self.CONFIGS]['workingdir']

    def read_max_words(self):
            return int(self.config[self.CONFIGS]['maxwords'])

    def read_width(self):
        return int(self.config[self.CONFIGS]['width'])

    def read_height(self):
        return int(self.config[self.CONFIGS]['height'])

    def read_mask(self):
        return self.config[self.CONFIGS]['mask']

    def read_margin(self):
        return int(self.config[self.CONFIGS]['margin'])

    def read_random_state(self):
        try:
            return self.config[self.CONFIGS]['random_state']
        except KeyError:
            return int(self.config[self.CONFIGS]['random_state'])

    def read_min_font_size(self):
        try:
            return int(self.config[self.CONFIGS]['min_font_size'])
        except KeyError:
            return None

    def read_max_font_size(self):
        try:
            return int(self.config[self.CONFIGS]['max_font_size'])
        except ValueError:
            return None

    def read_ranks_only(self):
        return bool(self.config[self.CONFIGS]['ranks_only'])

    def read_prefer_horizontal(self):
        return float(self.config[self.CONFIGS]['prefer_horizontal'])

    def read_relative_scaling(self):
        return float(self.config[self.CONFIGS]['relative_scaling'])

    def read_font_step(self):
        return int(self.config[self.CONFIGS]['font_step'])

    def read_mode(self):
        return self.config[self.CONFIGS]['mode']

    def read_background_color(self):
        return self.config[self.CONFIGS]['background_color']

    # def read_stopwords(self):
    #     return int(self.config[self.CONFIGS]['stopwords'])

    def read_normalize_plurals(self):
        return bool(self.config[self.CONFIGS]['normalize_plurals'])

    def read_font_path(self):
        if self.config[self.CONFIGS]['font_path'] is not None:
            return self.config[self.CONFIGS]['font_path']
        else:
            return None

    def read_recolor(self):
        return self.config[self.CONFIGS]['recolor']

    def read_offset(self):
        return int(self.config[self.CONFIGS]['offset'])

    def read_end_time(self):
        return self.config[self.CONFIGS]['end_time']

    def read_start_time(self):
        return self.config[self.CONFIGS]['start_time']

    def read_tz_offset(self):
        return int(self.config[self.CONFIGS]['tz_offset'])

    def read_max_results(self):
        return int(self.config[self.CONFIGS]['max_results'])

    def read_server_ip(self):
        return self.config[self.MONGODB]['server_ip']

    def read_server_port(self):
        return int(self.config[self.MONGODB]['server_port'])

