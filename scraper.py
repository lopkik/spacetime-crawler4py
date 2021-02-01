import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import defaultdict

def scraper(url, resp):
    links, words = extract_next_links(url, resp)
    # tokens = [text for text in soup.stripped_strings]
    # print(' '.join([text for text in soup.stripped_strings]))
    # print('past extract')
    return [link for link in links if is_valid(link)], words
    # return [], words

def is_path(parsed):
    try:
        if len(parsed.path) > 0 and len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
            # print('A PATH APPEARS', parsed.path)
            return True
        else:
            return False
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def in_domain(parsed):
    try:
        ics_match = re.match(r'^([\w\.]*\.)?ics\.uci\.edu$', parsed.netloc)
        cs_match = re.match(r'^([\w\.]*\.)?cs\.uci\.edu$', parsed.netloc)
        inf_match = re.match(r'^([\w\.]*\.)?informatics\.uci\.edu$', parsed.netloc) and re.match(r'^\/files.*', parsed.path) == None
        stat_match = re.match(r'^([\w\.]*\.)?stat\.uci\.edu$', parsed.netloc)
        today_match = re.match(r'^([\w\.]*\.)?today\.uci\.edu$', parsed.netloc) and re.match(r'^\/department\/information_computer_sciences', parsed.path)
        # if today_match:
        #     print(' today thing', parsed)
        return ics_match or cs_match or inf_match or stat_match or today_match
    except TypeError:
        print ("TypeError for ", parsed)
        raise
'''
Checks if a url is a path, 
then checks if its a complete url in the valid domain
'''
def is_valid(url):
    try:
        parsed = urlparse(url)

        is_file = re.match(
            r".*(\.)?(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4|ppsx"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
        if is_file: 
            return False

        if in_domain(parsed) or is_path(parsed):
            # if in_domain(parsed):
            #     print('IN DOMAIN NOW', url)
            # else:
            #     print('  Path=', url)
            return True
        else:
            return False

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def extract_next_links(url, resp):
    # print('extract')
    new_frontier = set()
    words = []
    # print(resp.raw_response.content)
    if (resp.raw_response != None):
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        words = (' '.join([text for text in soup.stripped_strings])).split()
        
        for link in soup.find_all('a'):
            # new_url is the urls to test to crawl
            new_url = link.get('href');
            parsed = urlparse(new_url)

            if type(new_url) == str and is_valid(new_url):
                if is_path(parsed):
                    if len(urlparse(url).path) == 0:
                        new_frontier.add(url + new_url)
                elif len(parsed.query) > 0:
                    new_frontier.add(new_url[:new_url.index('?')])
                elif len(parsed.fragment) > 0:
                    new_frontier.add(new_url[:new_url.index('#')])
                else:
                    new_frontier.add(new_url)
            # else:
            #     print('Invalid:', new_url, urlparse(new_url).netloc)
        # print('  FRONTIER', new_frontier)
    return list(new_frontier), words

def simhash(word_weights):
    v = [0]*32
    for k in word_weights.keys():
        # get the 32 bit binary rep of pythons hash for each word
        binhashstr = str(bin(hash(k) % 2**32))[2:]
        binhashstr = binhashstr.rjust(32, '0')
        # add weights to v 
        for i, bit in enumerate(binhashstr):
            if bit == '1':
                v[i] += word_weights[k]
            else:
                v[i] -= word_weights[k]

    page_hash = ''.join(['1' if bit > 0 else '0' for bit in v])
    return page_hash

def similarity(parent_url, tbd_url, page_hash_dict):
    parent_hash = page_hash_dict[parent_url]
    tbd_hash = page_hash_dict[tbd_url]
    print('SIMILARITY:', parent_hash, tbd_hash)
    sum_equal = 0
    for i in range(32):
        if parent_hash[i] == tbd_hash[i]:
            sum_equal += 1
    
    return sum_equal / 32