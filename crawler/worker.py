from threading import Thread

from utils.download import download
from collections import defaultdict
from utils import get_logger
from scraper import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
        
    def run(self):
        unique_link_set = set()
        max_word_count = 0
        word_freq_dict = defaultdict(int)
        subdomain_dict = defaultdict(int)
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                print("  Unique Link Count:", len(unique_link_set))
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper(tbd_url, resp)
            # print('scraped urls:', len(scraped_urls))
            unique_link_set = unique_link_set.union(set(scraped_urls))
            print("  Unique Link Count:", len(unique_link_set))
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
