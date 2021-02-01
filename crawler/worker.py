import time
import nltk
import re
import string

from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper, simhash, similarity
from collections import defaultdict
from nltk.corpus import stopwords
from urllib.parse import urlparse

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
    
    def run(self):
        counter = 0
        unique_link_set = set()
        max_word_count = ('', 0)
        word_freq_dict = defaultdict(int)
        subdomain_dict = defaultdict(int)
        page_hash_dict = dict()

        while True:
            parent_url ,tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                print('  Unique Link Count:    ', len(unique_link_set))
                print('  Max Word Count URL:   ', max_word_count)
                print('  Words and Frequencies:')
                for k, v in sorted(word_freq_dict.items(), key=lambda x: -x[1])[:50]:
                    print(' ', k, '\t', v)
                print('  Subdomains and Pages: ')
                for k, v in sorted(subdomain_dict.items(), key=lambda x: x[0]):
                    print(' ', k, '\t', v)
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls, words = scraper(tbd_url, resp)

            counter += 1
            # try to move this stuff below into scraper function
            # 1 
            unique_link_set = unique_link_set.union(set(scraped_urls))
            # 2 find and track max_word_count url and count
            stop_words = set(stopwords.words('english'))
            tokens = [w.lower().strip(string.punctuation) for w in words if not w.lower().strip(string.punctuation) in stop_words and re.match(r'^[\w-]+$', w.strip(string.punctuation))]
            if len(tokens) > max_word_count[1]:
                max_word_count = (tbd_url, len(tokens))
            #3 process word frequencies and use nltk to filter stop words
            #   also get weights of words for simhash
            word_weights = defaultdict(int)
            for token in tokens:
                word_weights[token] += 1
                word_freq_dict[token] += 1
            #4 use the re for ics_match to determine if subdomain
            parsed = urlparse(tbd_url)
            if re.match(r'^([\w\.]*\.)?ics\.uci\.edu$', parsed.netloc):
                subdomain_dict[parsed.netloc] += 1

            print('  Link Scraped Counter:', counter)
            print('  Unique Link Count:   ', len(unique_link_set))
            print('  Max Word Count URL:  ', max_word_count)
            print('  Word Freq Length:    ', len(word_freq_dict))
            print('  Subdomain Length:    ', len(subdomain_dict))
            # print('  page_hash_dict:      ', page_hash_dict)

            # get the hash value for the page
            page_hash_dict[tbd_url] = simhash(word_weights)
            sim_score = 0
            if parent_url != '':
                sim_score = similarity(parent_url, tbd_url, page_hash_dict)
                print('  Parent:', parent_url, '- tbd:', tbd_url, '- sim_score:', sim_score)
            # if tbd_url is a seed url, put all scraped urls in frontier
            #   else checkif not similar to parent url
            #       
            if parent_url == '' or sim_score <= 0.85:
                for scraped_url in scraped_urls:
                    self.frontier.add_url(tbd_url, scraped_url)
                self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
