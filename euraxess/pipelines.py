# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import csv

import pandas as pd

# useful for handling different item types with a single interface

df = pd.read_csv("output/jobs.csv")
jobs_id = set(df["id"].tolist())


class EuraxessPipeline:
    def open_spider(self, spider):
        self.file = open("output/jobs.csv", "a", encoding="utf-8")
        fieldnames = [
            "id",
            "type",
            "country",
            "university",
            "posted_on",
            "title",
            "link",
            "description",
            "department",
            "location",
            "field",
            "profile",
            "funding_program",
            "application_deadline",
        ]
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        spider.logger.info("EuraxessPipeline initialized and file opened for writing.")

    def close_spider(self, spider):
        self.file.close()
        spider.logger.info("EuraxessPipeline closed and file saved.")

    def process_item(self, item, spider):
        job_id = item.get("id")
        if job_id in jobs_id:
            spider.logger.info(f"Job {job_id} already exists, skipping.")
            # Close the spider if the job already exists
            spider.crawler.engine.close_spider(spider, "Job already exists")
            return item
        self.writer.writerow(item)
        return item
