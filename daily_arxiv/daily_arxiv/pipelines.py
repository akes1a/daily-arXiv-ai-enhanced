# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import arxiv
import json
import os
import sys
from datetime import datetime, timedelta
from scrapy.exceptions import DropItem


class DailyArxivPipeline:
    def __init__(self):
        self.page_size = 100
        self.client = arxiv.Client(self.page_size)
        categories = os.environ.get("CATEGORIES") or "cs.RO"
        self.target_categories = {
            category.strip() for category in categories.split(",") if category.strip()
        }

    def process_item(self, item: dict, spider):
        item["pdf"] = f"https://arxiv.org/pdf/{item['id']}"
        item["abs"] = f"https://arxiv.org/abs/{item['id']}"
        search = arxiv.Search(
            id_list=[item["id"]],
        )
        paper = next(self.client.results(search))
        primary_category = getattr(paper, "primary_category", paper.categories[0])
        if primary_category not in self.target_categories:
            raise DropItem(
                f"Paper {item['id']} has primary category {primary_category}, "
                f"not one of {sorted(self.target_categories)}"
            )
        item["authors"] = [a.name for a in paper.authors]
        item["title"] = paper.title
        item["categories"] = [primary_category]
        item["comment"] = paper.comment
        item["summary"] = paper.summary
        return item
