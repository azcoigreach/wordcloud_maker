from setuptools import setup

setup(
    author="azcoigreach",
    author_email="azcoigreach@gmail.com",
    name = 'Wordcloud Maker',
    version = '0.5.2',
    py_modules = ['wordcloud_maker'],
    install_requires = [
        'click',
        'colorama',
        'coloredlogs',
        'pymongo',
        'matplotlib',
        'pillow',
        'wordcloud',
        'pyfiglet',
        'numpy',
        'twitter',
        'imgurpython',
        'configparser', 
        
    ],
    entry_points = '''
        [console_scripts]
        wordcloud_maker=wordcloud_maker:main
    ''',
)