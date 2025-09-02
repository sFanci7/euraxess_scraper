# -*- coding: utf-8 -*-

import datetime
from typing import Any, Generator

import pandas as pd
import scrapy
from dateutil import parser
from scrapy.exceptions import CloseSpider


class EuraxessScraper(scrapy.Spider):
    name = "euraxess_scraper"

    base_url = "https://euraxess.ec.europa.eu"
    start_urls = [f"{base_url}/jobs/search?page=0"]
    current_page = 0
    today = datetime.datetime.now().strftime("%Y%m%d")

    # Check if already exists
    try:
        df = pd.read_csv("output/jobs.csv")
        df["posted_on"] = pd.to_datetime(df["posted_on"], errors="coerce")
        last_date = df["posted_on"].max() - datetime.timedelta(days=1)
        print(f"Last date in existing data: {last_date}")
    except FileNotFoundError:
        last_date = None

    # This is custom FEEDS only for this spider
    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    # let this parse be a metadata extactor, for now the only metadata is the final number of web pages to scrape
    def parse(self, response) -> Generator[scrapy.Request, Any, Any]:
        if response.status != 200:
            raise CloseSpider(f"Failed to fetch the page: {response.url}")
        else:
            print(f"Successfully fetched the page: {response.url}")

        # This is the xpath for final number
        if self.current_page == 0:
            self.final_number = response.xpath('//*[@id="oe-list-container"]/div[3]/div/nav/ul/li[5]/a/text()').get()
            self.final_number = int(self.final_number.strip()) if self.final_number else 0

            print(f"Final number: {self.final_number}")

        def _clean_line_breaks(text: str) -> str:
            """Utility function to clean line breaks from text."""
            return text.replace("\n", "").strip() if text else None

        # Extracting the job listings from the current page
        job_list = response.xpath('//*[@id="oe-list-container"]/div[3]/div/ul/li')
        print(f"Number of jobs found on this page: {len(job_list)}")
        for job in job_list:
            job_data = {
                "id": response.urljoin(job.xpath(".//h3/a/@href").get()).split("/")[-1],
                "type": job.xpath(".//div/div[1]/ul/li[1]/span/text()").get(),
                "country": job.xpath(".//div/div[1]/ul/li[2]/span/text()").get(),
                "university": job.xpath(".//article/div/ul[1]/li[1]/a/text()").get(),
                "posted_on": job.xpath(".//article/div/ul[1]/li[2]/text()").get().replace("Posted on ", ""),
                "title": job.xpath(".//h3/a/span/text()").get(),
                "link": response.urljoin(job.xpath(".//h3/a/@href").get()),
                "description": job.xpath('.//div[@class="ecl-content-block__description"]/p/text()').get(),
                "department": _clean_line_breaks(job.xpath('.//div[contains(@class,"id-Department")]//div[2]/text()').get()),
                "location": _clean_line_breaks(job.xpath('.//div[contains(@class,"id-Work-Locations")]//div[2]/text()').get()),
                "field": _clean_line_breaks(";".join(job.xpath('.//div[contains(@class,"id-Research-Field")]/div[2]//text()').getall())),
                "profile": _clean_line_breaks(";".join(job.xpath('.//div[contains(@class,"id-Researcher-Profile")]//a/text()').getall())),
                "funding_program": job.xpath('.//div[contains(@class,"id-Funding-Programme")]//a/text()').get(),
                "application_deadline": job.xpath('.//div[contains(@class,"id-Application-Deadline")]//time/text()').get(),
            }
            posted_date = parser.parse(job_data["posted_on"], fuzzy=True)
            if self.last_date and posted_date <= self.last_date:
                self.logger.info(f"Job {job_data['id']} posted on {job_data['posted_on']} is older than the last date {self.last_date}. Return.")
                return

            yield job_data

        self.current_page += 1

        next_url = f"{self.base_url}/jobs/search?page={self.current_page}"
        if self.current_page > self.final_number:
            print(f"Reached the final page: {self.current_page}")
            raise CloseSpider(f"Reached the final page: {self.current_page}")

        yield scrapy.Request(
            url=next_url,
            callback=self.parse,
        )
