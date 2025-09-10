# scrapers/base_scraper.py

from abc import ABC, abstractmethod
from models.review import Review
from typing import List
import logging

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, floor: str):
        self.floor = floor
        self.reviews: List[Review] = []

    @abstractmethod
    def scrape(self) -> List[Review]:
        pass

    def add_review(self, review: Review):
        self.reviews.append(review)

    def get_reviews(self) -> List[Review]:
        return self.reviews