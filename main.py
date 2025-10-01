# run the scraper
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from euraxess.spiders.euraxess import EuraxessScraper

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(EuraxessScraper)
    process.start()
