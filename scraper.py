import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

netlocSet = {'www.ics.uci.edu', 'www.cs.uci.edu', 'www.informatics.uci.edu', 'www.stat.uci.edu'}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    print('  hello', url)
    # print(' '.join([text for text in soup.stripped_strings]))
    return [link for link in links if is_valid(link)]

def is_path(url):
    try:
        parsed = urlparse(url)
        if len(parsed.path) > 0 and len(parsed.scheme) == 0 and len(parsed.netloc) == 0:
            # print('A PATH APPEARS', parsed.path)
            return True
        else:
            return False
    except TypeError:
        print ("TypeError for ", parsed)
        raise
'''
Checks a url if they have a scheme
if not, then check if they have a valid netloc
'''
def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            if parsed.netloc in netlocSet:
                return True
            else:
                return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def extract_next_links(url, resp):
    new_frontier = []
    if (resp.raw_response != None):
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        
        for link in soup.find_all('a'):
            new_url = link.get('href');
            if is_valid(new_url):
                print('URL=', is_valid(new_url), new_url)
                new_frontier.append(new_url)
            elif is_path(new_url):
                print('Path=', is_path(new_url), url, '+', new_url)
                new_frontier.append(urljoin(url, new_url))
            else:
                print('DIDNT QUALIFY:', new_url)
        print('  FRONTIER', new_frontier)
    return []

