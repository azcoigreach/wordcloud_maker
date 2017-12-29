from setuptools import setup

setup(
    author="azcoigreach",
    author_email="azcoigreach@gmail.com",
    name = 'Wordcloud Maker',
    version = '0.1.2',
    py_modules = ['mongo_wordcloud'],
    install_requires = [
        'click',
        'colorama',
        'coloredlogs',
        'pymongo',
        'matplotlib', 
        'numpy>=1.6.1', 
        'pillow',
        'wordcloud',
    ],
    entry_points = '''
        [console_scripts]
        wc_maker=wordcloud_maker:main
    ''',
)