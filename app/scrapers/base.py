from abc import ABC, abstractmethod
from typing import List, Any

class BaseScraper(ABC):
    @abstractmethod
    def get_articles(self, hours: int = 24) -> List[Any]:
        """
        Scrape and return articles published within the last 'hours'.
        """
        pass
