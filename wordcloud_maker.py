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
import numpy as np
from PIL import Image
from pymongo import MongoClient, monitoring
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS, random_color_func, \
get_single_color_func
import matplotlib.pyplot as plt
from pyfiglet import Figlet
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientError, ImgurClientRateLimitError
from twitter import *
# from twitterapi import TwitterApi
from settings import Settings
from functools import update_wrapper

coloredlogs.install(level='DEBUG')
logger = logging.getLogger(__name__)

class Context(object):
    def __init__(self):
        self.debug = False
        self.s = Settings("./settings.ini")
        
pass_context = click.make_pass_decorator(Context, ensure=True)

# CLI Interface (Main)

@click.group(chain=True)
# @click.option('--debug', is_flag=True,
#               help='Debug Mode')
# @click.option('--working_directory', '-w', type=click.Path())
# @click.option('--output_directory', '-o', type=click.Path())
@pass_context

def main(ctx):
    '''
    Generates wordclouds based on query responces from MongoDB Twitter Database. -
    https://github.com/azcoigreach/twitter_logger

    Wordcloud API reference - http://amueller.github.io/word_cloud/references.html

    Edit ./settings.ini to modify defaults.
    '''
    init(convert=True)
    ctx.debug = ctx.s.read_debug()
    ctx.workingdir = ctx.s.read_working_dir()
    ctx.outputdir = ctx.s.read_output_dir()
    

    if ctx.debug is True:
        logger.setLevel(logging.DEBUG)
        logger.debug('<<<DEBUG MODE>>>')
    else:
        logger.setLevel(logging.INFO)

    # if working_directory is None:
    #     logger.debug('working_directory is %s', ctx.workingdir)
    # else:
    #     ctx.workingdir = working_directory

    # if output_directory is None:
    #     logger.debug('output_directory is %s', ctx.outputdir)
    # else:
    #     ctx.outputdir = output_directory

    if os.path.exists(ctx.workingdir) is False:
        os.mkdir(ctx.workingdir)
        logger.debug('working_directory created as %s', ctx.workingdir)
    
    if os.path.exists(ctx.outputdir) is False:
        os.mkdir(ctx.outputdir)
        logger.debug('output_directory created as %s', ctx.outputdir)

    ctx.fig = Figlet(font='CLR6X10')

    # with open(ctx.workingdir + '/bot.pickle', 'wb') as f:
    #     bot = False
    #     pickle.dump(bot, f)

@main.resultcallback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """
    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)
        return processor
    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """
    @processor
    def new_func(stream, *args, **kwargs):
        for item in stream:
            yield item
        for item in f(*args, **kwargs):
            yield item
    return update_wrapper(new_func, f)

# Get Data

@main.command('get_data')
@click.option('--server_ip', '-ip',
              help='Server IPv4 address to MongoDB database')
@click.option('--server_port', '-port',
              help='Server IPv4 address to MongoDB database')
@click.option('--offset', '-o', type=int,
              help='Time frame of query - X hours offset before end_time')
@click.option('--end_time', '-e',
              help='Query start datetime "2018-02-04 16:20"')
@click.option('--start_time', '-s',
              help='Query start datetime "2018-02-03 16:20"')
@click.option('--tz_offset', '-tz', type=int,
              help='Time Zone offset (db times are GMT)')
@click.option('--max_results', '-max',
              help='Limit query results')
@pass_context
@generator
def get_data(ctx, server_ip, server_port, start_time, end_time, offset, max_results, tz_offset):
    '''
    Populates query_words.pickle with a list of hashtags and frequencies from a MongoDB
    database containing raw Twitter data.
    '''
    # with open(ctx.workingdir + '/bot.pickle', 'rb') as f:
    #     bot = pickle.load(f)

    # logger.warning('<<<--gd in bot mode %s -->>>', bot)

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

    if server_ip is None:
        server_ip = ctx.s.read_server_ip()
    if server_port is None:
        server_port = ctx.s.read_server_port()
    if start_time is None:
        if ctx.s.read_start_time() is not None:
            start_time = datetime.strptime(ctx.s.read_start_time(), '%Y-%m-%d %H:%M')
        else:
            start_time = None
    if end_time is None:
        if ctx.s.read_end_time() is not None:
            end_time = datetime.strptime(ctx.s.read_end_time(), '%Y-%m-%d %H:%M')
        else:
            end_time = None
    if offset is None:
        offset = ctx.s.read_offset()
    if max_results is None:
        max_results = ctx.s.read_max_results()
    if tz_offset is None:
        tz_offset = ctx.s.read_tz_offset()


    try:
        client = MongoClient(server_ip, server_port)
        db = client.twitter_stream
        logger.warning('MongoDB connected...')
    except Exception as err:
        logging.error(err)
    
    if end_time == None:
        end_time = datetime.now() + timedelta(hours=tz_offset)
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
            {'$limit' : max_results}])
    except Exception as err:
        logger.error('query error: %s', err)

    words = []

    with open(ctx.workingdir + '/query_words.pickle', 'wb') as f:

        for i in iter(query):
            printable = set(string.printable)
            text_filter = filter(lambda x: x in printable, i['_id'])

            logger.info(Fore.LIGHTRED_EX + text_filter + ' : ' + str(i['count']))
            logger.debug(i)

            words.append(i)

        logger.debug(words)
        pickle.dump(words, f)

    logger.info(Fore.YELLOW + ctx.fig.renderText('OPERATION COMPLETE'))
    yield



# Generate Wordcloud

@main.command('gen_wordcloud')

@click.option('--width', type=int,
              help='Image width')
@click.option('--height', type=int,
              help='Image height')
@click.option('--max_words', type=int,
              help='maximum words in wordcloud')
@click.option('--mask', type=click.Path(),
              help='Mask filename')
@click.option('--margin', type=int,
              help='Margin between words')
@click.option('--random_state', type=int,
              help='Add random state')
@click.option('--min_font_size', type=float,
              help='Minimum Font size')
@click.option('--max_font_size', type=float,
              help='Maximum Font size')
@click.option('--ranks_only', type=bool,
              help='')
@click.option('--prefer_horizontal', type=float,
              help='Prefer horizontal word alignment')
@click.option('--relative_scaling', type=float,
              help='Relative scaling between other words')
@click.option('--font_step', type=int,
              help='Steps between font sizes')
@click.option('--mode',
              help='Color mode ex."RGB" or "RGBA"')
@click.option('--background_color',
              help='Background color in HEX')
@click.option('--stopwords', type=click.Path(),
              help='Set stopwords file')
@click.option('--normalize_plurals', type=bool,
              help='Normalize plurals')
@click.option('--font_path', type=click.Path(),
              help='Font path')
@click.option('--recolor',
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
@click.option('--show', is_flag=True, expose_value=True, \
              is_eager=False, help='Show Python output')
@pass_context
@generator
def gen_wordcloud(ctx, width, height, max_words, mask, margin,
                  random_state, min_font_size, max_font_size, ranks_only,
                  prefer_horizontal, relative_scaling, font_step, mode,
                  background_color, stopwords, normalize_plurals,
                  font_path, recolor, show):
    '''
    Generates wordcloud from list of words and frequencies stored in query_words.pickle.
    '''

    # with open(ctx.workingdir + '/bot.pickle', 'rb') as f:
    #     bot = pickle.load(f)
    
    logger.debug(ctx.workingdir)
    # logger.warning('<<<--bot mode %s -->>>', bot)

    start_time = time.strftime("%Y%m%d_%H%M%S")
    output_file = str(ctx.outputdir + "/wordcloud_" + start_time + ".png")

    if width is None:
        width = ctx.s.read_width()
    if height is None:
        height = ctx.s.read_height()
    if max_words is None:
        max_words = ctx.s.read_max_words()
    if mask is None:
        mask = ctx.s.read_mask()
    if margin is None:
        margin = ctx.s.read_margin()
    if random_state is None:
        random_state = ctx.s.read_random_state()
    if min_font_size is None:
        min_font_size = ctx.s.read_min_font_size()
    if max_font_size is None:
        max_font_size = ctx.s.read_max_font_size()
    if ranks_only is None:
        ranks_only = ctx.s.read_ranks_only()
    if prefer_horizontal is None:
        prefer_horizontal = ctx.s.read_prefer_horizontal()
    if relative_scaling is None:
        relative_scaling = ctx.s.read_relative_scaling()
    if font_step is None:
        font_step = ctx.s.read_font_step()
    if mode is None:
        mode = ctx.s.read_mode()
    if background_color is None:
        background_color = ctx.s.read_background_color()
    if stopwords is None:
        stopwords = ctx.s.read_stopwords()
    if normalize_plurals is None:
        normalize_plurals = ctx.s.read_normalize_plurals()
    if font_path is None:
        font_path = ctx.s.read_font_path()
    if recolor is None:
        recolor = ctx.s.read_recolor()
    

    words = {}
    with open(ctx.workingdir + '/query_words.pickle', 'rb') as f:
        text = pickle.load(f)
        logger.debug(Fore.LIGHTRED_EX + 'pickle contents: ' + Fore.LIGHTCYAN_EX + '[%s] %s',\
                     type(text), text)

        for i in iter(text):
                # logger.debug('i : [%s] %s',type(text), text)

            for key, value in i.items():
                if key == '_id':
                    id_value = value
                    # logger.debug(id_value)
                if key == 'count':
                    count_value = value
                    # logger.debug(count_value)

            freq = json.dumps({id_value : count_value})
            freq = json.loads(freq)
            words.update(freq)

    logger.debug('words list: [%s] %s', type(words), words)

    if mask != None:
        mask_array = np.array(Image.open(mask))
        logger.debug('Mask converted to numpy array %s', mask_array)
    else:
        mask_array = None
    
    logger.info(Fore.LIGHTCYAN_EX + 'width = ' + Fore.LIGHTMAGENTA_EX + '%s' + Fore.CYAN + ' %s' , width, type(width))
    logger.info(Fore.LIGHTCYAN_EX + 'height = ' + Fore.LIGHTMAGENTA_EX + '%s', height)
    logger.info(Fore.LIGHTCYAN_EX + 'max_words = ' + Fore.LIGHTMAGENTA_EX + '%s', max_words)
    logger.info(Fore.LIGHTCYAN_EX + 'mask = ' + Fore.LIGHTMAGENTA_EX + '%s', mask)
    logger.info(Fore.LIGHTCYAN_EX + 'margin = ' + Fore.LIGHTMAGENTA_EX + '%s', margin)
    logger.info(Fore.LIGHTCYAN_EX + 'random_state = ' + Fore.LIGHTMAGENTA_EX + '%s', random_state)
    logger.info(Fore.LIGHTCYAN_EX + 'min_font_size = ' + Fore.LIGHTMAGENTA_EX + '%s', min_font_size)
    logger.info(Fore.LIGHTCYAN_EX + 'max_font_size = ' + Fore.LIGHTMAGENTA_EX + '%s' + Fore.CYAN + ' %s' , max_font_size, type(max_font_size))
    logger.info(Fore.LIGHTCYAN_EX + 'ranks_only = ' + Fore.LIGHTMAGENTA_EX + '%s', ranks_only)
    logger.info(Fore.LIGHTCYAN_EX + 'prefer_horizontal = ' + Fore.LIGHTMAGENTA_EX + '%s', prefer_horizontal)
    logger.info(Fore.LIGHTCYAN_EX + 'relative_scaling = ' + Fore.LIGHTMAGENTA_EX + '%s', relative_scaling)
    logger.info(Fore.LIGHTCYAN_EX + 'font_step = ' + Fore.LIGHTMAGENTA_EX + '%s', font_step)
    logger.info(Fore.LIGHTCYAN_EX + 'mode = ' + Fore.LIGHTMAGENTA_EX + '%s', mode)
    logger.info(Fore.LIGHTCYAN_EX + 'background_color = ' + Fore.LIGHTMAGENTA_EX + '%s', background_color)
    logger.info(Fore.LIGHTCYAN_EX + 'stopwords = ' + Fore.LIGHTMAGENTA_EX + '%s', stopwords)
    logger.info(Fore.LIGHTCYAN_EX + 'normalize_plurals = ' + Fore.LIGHTMAGENTA_EX + '%s', normalize_plurals)
    logger.info(Fore.LIGHTCYAN_EX + 'font_path = ' + Fore.LIGHTMAGENTA_EX + '%s', font_path)

    wc = WordCloud(width=width, height=height, max_words=max_words, mask=mask_array, margin=margin,
                   random_state=random_state, min_font_size=min_font_size,
                   max_font_size=max_font_size, ranks_only=ranks_only,
                   prefer_horizontal=prefer_horizontal, relative_scaling=relative_scaling,
                   font_step=font_step, mode=mode, background_color=background_color,
                   stopwords=stopwords, normalize_plurals=normalize_plurals,
                   font_path=font_path).generate_from_frequencies(words).recolor(colormap=recolor)

    logger.info(Fore.YELLOW + ctx.fig.renderText('WORDCLOUD GENERATED'))
    plt.figure()
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    
    if show is not True:
        logger.debug('<<<--save to file-->>>')
        logger.warning('Saving file to %s', output_file)
        wc.to_file(output_file)
        with open(ctx.workingdir + '/output_file.pickle', 'wb') as f:
            pickle.dump(output_file, f)
            logger.debug('Saving output_file.pickle')
    else:
        logger.debug('<<<--show output-->>>')
        plt.show()
    yield

# Automation
@main.command()
@pass_context
@generator
def post(ctx):
    logger.warning('posting output')
    twitter_api = Twitter(auth = OAuth(ctx.s.read_twitter_access_token(), ctx.s.read_twitter_access_token_secret(),
                          ctx.s.read_twitter_consumer_key(), ctx.s.read_twitter_consumer_secret()))

    imgur_client = ImgurClient(ctx.s.read_imgur_client_id(), ctx.s.read_imgur_client_secret(),
                               ctx.s.read_imgur_access_token(), ctx.s.read_imgur_refresh_token())
    
    
    #TODO: Automate Status and Title
    title = "Top 50 hashtags tweeted to @realDonaldTrump."
    status = "Top 50 hashtags tweeted to @realDonaldTrump. "

    with open(ctx.workingdir + '/output_file.pickle', 'rb') as f:
            output_file = pickle.load(f)
            logger.debug('Loading output_file.pickle')
            

    def upload_image(image_path, title, max_errors=3, sleep_seconds=60):
        """ Try to upload the image to imgur.com.
        :param image_path: path to the image file
        :param title: title of the image
        :param max_errors: max number of retries
        :param sleep_seconds: number of seconds to wait when an error happens
        :return: an imgur object (use `id` key to get the id to use in https://imgur.com/<id>),
                 None if an error occurs
        """
        config = {'title': title,
                  'name': title,
                  'description': title + '\n' + ctx.s.read_description_image_str()}
        errors = 0
        while True:
            try:
                logger.info("I'm going to upload this image: {0}".format(image_path))
                return imgur_client.upload_from_path(image_path, config=config, anon=False)
            except Exception as e:
                errors += 1
                logger.error(e)

                logger.error('Encountered {0} error(s). Retrying in {1} seconds'.format(errors, sleep_seconds))

                if (errors > max_errors):
                    return None

                time.sleep(sleep_seconds)

    
    def update_status(status, max_errors=3, sleep_seconds=60):
        """
        :param status: text of the tweet
        :param max_errors: max number of retries
        :param sleep_seconds: number of seconds to wait when an error happens
        :return: see https://dev.twitter.com/rest/reference/post/statuses/update example result,
                 None if an error occurs
        """
        errors = 0
        while True:
            try:
                logger.info('Tweeting status: %s', status)
                return twitter_api.statuses.update(status=status)
            except Exception as e:
                errors += 1

                logger.error("Error while trying to post: " + str(e))
                logger.error('Encountered {0} error(s). Retrying in {1} seconds'.format(errors, sleep_seconds))

                if (errors > max_errors):
                    return None

                time.sleep(sleep_seconds)
    
    imgur_id = upload_image(output_file, title)

    if imgur_id is None:
        logger.error("Error: failed uploading the word cloud image\n")
        exit

    imgur_id = imgur_id['id']

    status += 'http://imgur.com/' + imgur_id
    tweet = update_status(status)

    yield