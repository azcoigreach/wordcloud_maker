#!/usr/bin/env python
import os
from os import path
from datetime import datetime, timedelta
import dateutil.parser

import json
import string

import click
from colorama import init, Fore, Back, Style
import coloredlogs, logging

from pymongo import MongoClient, monitoring
from wordcloud import WordCloud, ImageColorGenerator, STOPWORDS, random_color_func, get_single_color_func
import numpy as np
import matplotlib.pyplot as plt
import random
import time
from collections import Counter


coloredlogs.install(level='DEBUG')
logger = logging.getLogger(__name__)



class Config(object):
    def __init__(self):
        self.debug = False
        

pass_config = click.make_pass_decorator(Config, ensure=True)



@click.group()
@click.option('--debug', is_flag=True,
                help='Debug Mode')
@click.option('--working_directory', '-w', type=click.Path())
@pass_config
def main(config, debug, working_directory):
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
    



@main.command()
@click.option('--server_ip', default='localhost', 
                help='Server IPv4 address to MongoDB database')
@click.option('--server_port', default=27017, 
                help='Server IPv4 address to MongoDB database')
@click.option('--hours', default=24, 
                help='Time frame of query over the last X hours')
@click.option('--limit', default=100, 
                help='Limit query results')
@pass_config
   
def get_data(config,server_ip,server_port, hours, limit):
    
    '''Get data from MongoDB Twitter Database'''

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
    
    start_time = (datetime.now() - timedelta(hours=hours))
    logger.info(Fore.CYAN+'created_at start time - %s', start_time)
    end_time = datetime.now()
    logger.info(Fore.CYAN+'created_at end time - %s', end_time)

    query = []

    try:
        query = db.twitter_query.aggregate([
                { '$match' : {'created_at' : {'$gte' : start_time
                                                , '$lte' : end_time}}},
                { '$unwind' : '$entities.hashtags'},
                {'$group': {'_id': '$entities.hashtags.text',
                                'count' : { '$sum' : 1}}},
                { "$sort" : { 'count' : -1} },
                { '$limit' : limit } ])
    except Exception as err:
        logger.error(err)    
    word_list = []

    with open('query_words.txt', 'wb') as f:
        for i in query:
            printable = set(string.printable)
            text_filter = filter(lambda x: x in printable, i['_id'])
            logger.info(Fore.LIGHTRED_EX + text_filter + ' : ' + str(i['count']))
            words = str('\n'+text_filter).encode('utf-8', 'ignore')
            f.write(words)
    
    logger.warning('Operation complete')


@main.command()
@click.option('--width', default=1024, type=int,
                help='Image width')
@click.option('--height', default=768, type=int,
                help='Image height')
@click.option('--max_words', default=200, type=int,
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
@click.option('--prefer_horizontal', default=0.9, type=float,
                help='Prefer horizontal word alignment')
@click.option('--relative_scaling', default=0.5, type=float,
                help='Relative scaling between other words')
@click.option('--font_step', default=1, type=int,
                help='Steps between font sizes')
@click.option('--mode', default='RGB',
                help='Color mode ex."RGB"')
@click.option('--background_color', default='#000000',
                help='Background color in HEX')                                
@click.option('--stopwords', default=None, type=file,
                help='Set stopwords file')
@click.option('--normalize_plurals', default=False, type=bool,
                help='Normalize plurals')
@click.option('--font_path', default=None, type=file,
                help='Font path')

@pass_config
def gen_wordcloud(config, width, height, max_words, mask,margin,
                    random_state, min_font_size, max_font_size, ranks_only,
                    prefer_horizontal, relative_scaling, font_step, mode,
                    background_color, stopwords, normalize_plurals,
                    font_path):  
    '''
    Generates wordclouds based on query responces from MongoDB stored in the query_word.txt

    Wordcloud API reference - http://amueller.github.io/word_cloud/references.html
    '''
    logger.debug(config.working_directory)
    
    start_time = time.strftime("%Y%m%d_%H%M%S")
    output_file = str(config.working_directory+"/wordcloud_"+start_time+".png")
    
    d = path.dirname(__file__)

    # Read the whole text.
    text = open(path.join(d, 'query_words.txt')).read()

    # if stopwords is not None:
    #     stopwords = None
    
    # lower max_font_size
    wc = WordCloud(width=width, height=height, max_words=max_words, mask=mask, margin=margin,
               random_state=random_state, min_font_size=min_font_size, max_font_size=max_font_size, ranks_only=ranks_only,
               prefer_horizontal=prefer_horizontal, relative_scaling=relative_scaling, font_step=font_step, mode=mode,
               background_color=background_color, stopwords=stopwords, normalize_plurals=normalize_plurals,
               font_path=font_path).generate(text)
    plt.figure()
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    logging.warning('Saving file to %s', output_file)
    wc.to_file(output_file)
    plt.show()

