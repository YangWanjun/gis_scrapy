import scrapy


class BaseSpider(scrapy.Spider):
    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }
