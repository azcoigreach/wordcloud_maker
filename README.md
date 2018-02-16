## azcoigreach/wordcloud_maker

This program takes data from Tweets (currently: hashtags) and forms them into wordclouds.  

`wordcloud_maker get_data` - retrieves data from a Mongo nosql database.  
`wordcloud_maker gen_wordcloud` - creates a wordcloud PNG file from a list of words and 
frequencies stored in a pickle located in the working directory.

# INSTALL

```
$ pip install --editable .
```

# RUN

```
wordcloud_maker --help
```

# TODO
|Complete   |Priority   |Task                                                            |
|:---------:|:---------:|:---------------------------------------------------------------|
|           |High       |Implement settings.ini for all default options and directories. |
|2018/02/10 |Medium     |Get Fonts and Masks working.                                    |
|           |High       |Get Stopwords working.                                          |
|           |High       |Filter non ascii hashtags on gen_wordcloud.                     |
|           |Medium     |Posting capabilities for Twitter and Imgur.                     |
|           |Low        |Daemonize and Dockerize.                                        |