## azcoigreach/wordcloud_maker

This program takes data from Tweets (currently: hashtags) and forms them into wordclouds.  

`wordcloud_maker get_data` - retrieves data from a Mongo nosql database.  
`wordcloud_maker gen_wordcloud` - creates a wordcloud PNG file from a list of words and 
frequencies stored in a pickle located in the working directory.

Requires a self contained Twitter database for searching through tweets.  This program 
utilizes a [Mongodb](https://github.com/azcoigreach/mongodb_data_tools "Mongodb Data Tools") 
datasource which is being fed a [Twitter logger](https://github.com/azcoigreach/twitter_logger).

# INSTALL

```
$ pip install --editable .
```

# RUN

```
wordcloud_maker --help
```

Chain commands together to automate.
```
wordcloud_maker get_data gen_wordcloud post [--quiet]
```

# DOCKER

## RUN
```
docker run -tdi --name wordcloud_maker -v D:\apps\wordcloud_maker\app\output:/usr/src/app/output --restart
 unless-stopped -e DISPLAY=$DISPLAY wordcloud_maker
```


# TODO
|Complete   |Priority   |Task                                                            |
|:---------:|:---------:|:---------------------------------------------------------------|
|TODO       |High       |Get Stopwords working.                                          |
|TODO       |LOW        |Filter non ascii hashtags on gen_wordcloud.                     |
|Working    |Medium     |Posting capabilities for Twitter and Imgur.                     |
|In Progress|High       |Automate and Dockerize.                                         |

# MENTIONS

This code was inspired by or hacked together with code from the following sources.

https://github.com/defacto133/twitter-wordcloud-bot
https://github.com/amueller/word_cloud

