#!/usr/bin/env python2
import sys
import os
from os import path
import time
from datetime import datetime, timedelta
import pickle
import json
import string
import logging
import coloredlogs
import click
from colorama import init, Fore
from pymongo import MongoClient, monitoring
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS, random_color_func, \
get_single_color_func
import matplotlib.pyplot as plt
from pyfiglet import Figlet

coloredlogs.install(level='DEBUG')
logger = logging.getLogger(__name__)

class Config(object):
    def __init__(self):
        self.debug = False

pass_config = click.make_pass_decorator(Config, ensure=True)

# CLI Interface

@click.group()
@click.option('--debug', is_flag=True,
              help='Debug Mode')
@click.option('--working_directory', '-w', type=click.Path())
@pass_config
def main(config, debug, working_directory):
    '''
    Generates wordclouds based on query responces from MongoDB Twitter Database. -
    https://github.com/azcoigreach/twitter_logger

    Wordcloud API reference - http://amueller.github.io/word_cloud/references.html
    '''
    init(convert=True)
    config.debug = debug
    config.working_directory = working_directory
    if debug is True:
        logger.setLevel(logging.DEBUG)
        logger.debug('<<<DEBUG MODE>>>')
    else:
        logger.setLevel(logging.INFO)

    if working_directory is None:
        config.working_directory = '.'
        logger.debug('working_directory is %s', config.working_directory)
    elif os.path.exists(working_directory) is False:
        os.mkdir(working_directory)
        logger.debug('working_directory created as %s', config.working_directory)
    config.fig = Figlet(font='CLR6X10')

# Get Data

@main.command()
@click.option('--server_ip', '-ip', default='localhost',
              help='Server IPv4 address to MongoDB database')
@click.option('--server_port', '-port', default=27017,
              help='Server IPv4 address to MongoDB database')
@click.option('--offset', '-o', default=None, type=int,
              help='Time frame of query - X hours offset before end_time')
@click.option('--end_time', '-e', default=None,
              help='Query start datetime "2018-02-04 16:20"')
@click.option('--start_time', '-s', default=None,
              help='Query start datetime "2018-02-03 16:20"')
@click.option('--limit', '-l', default=50,
              help='Limit query results')
@pass_config

def get_data(config, server_ip, server_port, start_time, end_time, offset, limit):
    '''
    Populates query_words.pickle with a list of hashtags and frequencies from a MongoDB
    database containing raw Twitter data.
    '''

    class CommandLogger(monitoring.CommandListener):

        def started(self, event):
            logging.info("Command {0.command_name} with request id "
                         "{0.request_id} started on server "
                         "{0.connection_id}".format(event))

        def succeeded(self, event):
            logging.info("Command {0.command_name} with request id "
                         "{0.request_id} on server {0.connection_id} "
                         "succeeded in {0.duration_micros} "
                         "microseconds".format(event))

        def failed(self, event):
            logging.info("Command {0.command_name} with request id "
                         "{0.request_id} on server {0.connection_id} "
                         "failed in {0.duration_micros} "
                         "microseconds".format(event))

    monitoring.register(CommandLogger())

    try:
        client = MongoClient(server_ip, server_port)
        db = client.twitter_stream
        logger.warning('MongoDB connected...')
    except Exception as err:
        logging.error(err)
    
    if end_time == None:
        end_time = datetime.now()
    else:
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M')
    
    if (offset == None) and (start_time == None):
        offset = 24
        start_time = (end_time - timedelta(hours=offset))
    elif (offset != None) and (start_time != None):
        logger.error(Fore.LIGHTRED_EX + 'Can not use OFFSET and START_TIME together. Pick one.')
        sys.exit(-1)
    elif (offset != None):
        start_time = (end_time - timedelta(hours=offset))
    elif (start_time != None):
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M')


    
        

    # start_time = (datetime.now() - timedelta(hours=hours))
    logger.info(Fore.CYAN+'created_at start time - %s', start_time)
    # end_time = datetime.now()
    logger.info(Fore.CYAN+'created_at end time - %s', end_time)

    query = []

    try:
        query = db.twitter_query.aggregate([
            {'$match': {'created_at': {'$gte': start_time,
                                       '$lte': end_time}}},
            {'$unwind': '$entities.hashtags'},
            {'$group': {'_id': '$entities.hashtags.text',
                        'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit' : limit}])
    except Exception as err:
        logger.error('query error: %s', err)

    words = []

    with open(config.working_directory + '/query_words.pickle', 'wb') as f:

        for i in iter(query):
            printable = set(string.printable)
            text_filter = filter(lambda x: x in printable, i['_id'])

            logger.info(Fore.LIGHTRED_EX + text_filter + ' : ' + str(i['count']))
            logger.debug(i)

            words.append(i)

        logger.debug(words)
        pickle.dump(words, f)

    logger.info(Fore.YELLOW + 'Operation complete')
    
    print Fore.YELLOW + config.fig.renderText('OPERATION COMPLETE')




# Generate Wordcloud

@main.command()
@click.option('--width', default=1920, type=int,
              help='Image width')
@click.option('--height', default=1080, type=int,
              help='Image height')
@click.option('--max_words', default=50, type=int,
              help='maximum words in wordcloud')
@click.option('--mask', default=None, type=file,
              help='Mask filename')
@click.option('--margin', default=2, type=int,
              help='Margin between words')
@click.option('--random_state', default=None, type=int,
              help='Add random state')
@click.option('--min_font_size', default=8, type=int,
              help='Minimum Font size')
@click.option('--max_font_size', default=None, type=int,
              help='Maximum Font size')
@click.option('--ranks_only', default=None, type=bool,
              help='')
@click.option('--prefer_horizontal', default=0.6, type=float,
              help='Prefer horizontal word alignment')
@click.option('--relative_scaling', default=0.6, type=float,
              help='Relative scaling between other words')
@click.option('--font_step', default=2, type=int,
              help='Steps between font sizes')
@click.option('--mode', default='RGB',
              help='Color mode ex."RGB" or "RGBA"')
@click.option('--background_color', default='#000000',
              help='Background color in HEX')
@click.option('--stopwords', default=None, type=file,
              help='Set stopwords file')
@click.option('--normalize_plurals', default=False, type=bool,
              help='Normalize plurals')
@click.option('--font_path', default=None, type=file,
              help='Font path')
@click.option('--recolor', default=None,
              help='Colormap: Accent, Accent_r, Blues, Blues_r, \
              BrBG, BrBG_r, BuGn, BuGn_r, BuPu, BuPu_r, \
              CMRmap, CMRmap_r, Dark2, Dark2_r, GnBu, GnBu_r, \
              Greens, Greens_r, Greys, Greys_r, OrRd, OrRd_r, \
              Oranges, Oranges_r, PRGn, PRGn_r, Paired, \
              Paired_r, Pastel1, Pastel1_r, Pastel2, \
              Pastel2_r, PiYG, PiYG_r, PuBu, PuBuGn, \
              PuBuGn_r, PuBu_r, PuOr, PuOr_r, PuRd, PuRd_r, \
              Purples, Purples_r, RdBu, RdBu_r, RdGy, RdGy_r, \
              RdPu, RdPu_r, RdYlBu, RdYlBu_r, RdYlGn, \
              RdYlGn_r, Reds, Reds_r, Set1, Set1_r, Set2, \
              Set2_r, Set3, Set3_r,  Spectral, Spectral_r, \
              Vega10, Vega10_r, Vega20, Vega20_r, Vega20b, \
              Vega20b_r, Vega20c, Vega20c_r, Wistia, \
              Wistia_r, YlGn, YlGnBu, YlGnBu_r, YlGn_r, \
              YlOrBr, YlOrBr_r, YlOrRd, YlOrRd_r, afmhot, \
              afmhot_r, autumn, autumn_r, binary, binary_r, \
              bone, bone_r, brg, brg_r, bwr, bwr_r, cool, \
              cool_r, coolwarm, coolwarm_r, copper, copper_r, \
              cubehelix, cubehelix_r, flag, flag_r, \
              gist_earth, gist_earth_r, gist_gray, \
              gist_gray_r, gist_heat, gist_heat_r, \
              gist_ncar, gist_ncar_r, gist_rainbow, \
              gist_rainbow_r, gist_stern, gist_stern_r, \
              gist_yarg, gist_yarg_r, gnuplot, gnuplot2, \
              gnuplot2_r, gnuplot_r, gray, gray_r, hot, \
              hot_r, hsv, hsv_r, inferno, inferno_r, \
              jet, jet_r, magma, magma_r, nipy_spectral, \
              nipy_spectral_r, ocean, ocean_r, pink, \
              pink_r, plasma, plasma_r, prism, prism_r, \
              rainbow, rainbow_r, seismic, seismic_r, \
              spectral, spectral_r, spring, spring_r, \
              summer, summer_r, tab10, tab10_r, tab20, \
              tab20_r, tab20b, tab20b_r, tab20c, tab20c_r, \
              terrain, terrain_r, viridis, \
              viridis_r, winter, winter_r')

@pass_config
def gen_wordcloud(config, width, height, max_words, mask, margin,
                  random_state, min_font_size, max_font_size, ranks_only,
                  prefer_horizontal, relative_scaling, font_step, mode,
                  background_color, stopwords, normalize_plurals,
                  font_path, recolor):
    '''
    Generates wordcloud from list of words and frequencies stored in query_words.pickle.
    '''
    logger.debug(config.working_directory)

    start_time = time.strftime("%Y%m%d_%H%M%S")
    output_file = str(config.working_directory + "/wordcloud_" + start_time + ".png")

    words = {}
    with open(config.working_directory + '/query_words.pickle', 'rb') as f:
        text = pickle.load(f)
        logger.debug(Fore.LIGHTRED_EX + 'pickle contents: ' + Fore.LIGHTCYAN_EX + '[%s] %s',\
                     type(text), text)

        for i in iter(text):
                # logger.debug('i : [%s] %s',type(text), text)

            for key, value in i.items():
                if key == '_id':
                    id_value = value
                    logger.debug(id_value)
                if key == 'count':
                    count_value = value
                    logger.debug(count_value)

            freq = json.dumps({id_value : count_value})
            freq = json.loads(freq)
            words.update(freq)

    logger.debug('words list: [%s] %s', type(words), words)

    # if stopwords is not None:
    #     stopwords = None

    wc = WordCloud(width=width, height=height, max_words=max_words, mask=mask, margin=margin,
                   random_state=random_state, min_font_size=min_font_size,
                   max_font_size=max_font_size, ranks_only=ranks_only,
                   prefer_horizontal=prefer_horizontal, relative_scaling=relative_scaling,
                   font_step=font_step, mode=mode, background_color=background_color,
                   stopwords=stopwords, normalize_plurals=normalize_plurals,
                   font_path=font_path).generate_from_frequencies(words).recolor(colormap=recolor)

    logger.info(Fore.LIGHTCYAN_EX + 'width = ' + Fore.LIGHTMAGENTA_EX + '%s', width)
    logger.info(Fore.LIGHTCYAN_EX + 'height = ' + Fore.LIGHTMAGENTA_EX + '%s', height)
    logger.info(Fore.LIGHTCYAN_EX + 'max_words = ' + Fore.LIGHTMAGENTA_EX + '%s', max_words)
    logger.info(Fore.LIGHTCYAN_EX + 'mask = ' + Fore.LIGHTMAGENTA_EX + '%s', mask)
    logger.info(Fore.LIGHTCYAN_EX + 'margin = ' + Fore.LIGHTMAGENTA_EX + '%s', margin)
    logger.info(Fore.LIGHTCYAN_EX + 'random_state = ' + Fore.LIGHTMAGENTA_EX + '%s', random_state)
    logger.info(Fore.LIGHTCYAN_EX + 'min_font_size = ' + Fore.LIGHTMAGENTA_EX + '%s', min_font_size)
    logger.info(Fore.LIGHTCYAN_EX + 'max_font_size = ' + Fore.LIGHTMAGENTA_EX + '%s', max_font_size)
    logger.info(Fore.LIGHTCYAN_EX + 'ranks_only = ' + Fore.LIGHTMAGENTA_EX + '%s', ranks_only)
    logger.info(Fore.LIGHTCYAN_EX + 'prefer_horizontal = ' + Fore.LIGHTMAGENTA_EX + '%s', prefer_horizontal)
    logger.info(Fore.LIGHTCYAN_EX + 'relative_scaling = ' + Fore.LIGHTMAGENTA_EX + '%s', relative_scaling)
    logger.info(Fore.LIGHTCYAN_EX + 'font_step = ' + Fore.LIGHTMAGENTA_EX + '%s', font_step)
    logger.info(Fore.LIGHTCYAN_EX + 'mode = ' + Fore.LIGHTMAGENTA_EX + '%s', mode)
    logger.info(Fore.LIGHTCYAN_EX + 'background_color = ' + Fore.LIGHTMAGENTA_EX + '%s', background_color)
    logger.info(Fore.LIGHTCYAN_EX + 'stopwords = ' + Fore.LIGHTMAGENTA_EX + '%s', stopwords)
    logger.info(Fore.LIGHTCYAN_EX + 'normalize_plurals = ' + Fore.LIGHTMAGENTA_EX + '%s', normalize_plurals)
    logger.info(Fore.LIGHTCYAN_EX + 'font_path = ' + Fore.LIGHTMAGENTA_EX + '%s', font_path)

    print Fore.YELLOW + config.fig.renderText('WORDCLOUD GENERATED')
    plt.figure()
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")

    logging.warning('Saving file to %s', output_file)

    wc.to_file(output_file)

    plt.show()

    
