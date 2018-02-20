from bs4 import BeautifulSoup
import requests
import re
import os
from subprocess import check_output
from time import sleep

import logging
from datetime import datetime

current_date = datetime.now().strftime('%Y%m%d')
current_folder = os.path.dirname(os.path.realpath(__file__))
logfile = os.path.join(current_folder, 'log/wishlist_log_{0}.txt'.format(current_date))

logger = logging.getLogger(__name__)

fh = logging.FileHandler(logfile)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')
fh.setFormatter(formatter)
logger.addHandler(fh)

BASE_URL = 'https://www.amazon.com/gp/registry/wishlist/'
PETES_WISHLIST_ID = '1ZF0FXNHUY7IG'


def get_items_from_wishlist_page(wishlist_id, page_number):
    """ Take a wishlist ID and a page number, and return a list of all items on that page

        Returns a list of dicts with these keys:
            item_url = URL for that variation of the items
            date_added = date the item was added to the wishlist_page
            ASIN = the amazon ASIN for that variation of the item

    """
    logger.info('getting items from page ' + str(page_number))
    page_url = "{0}/{1}/?page={2}".format(BASE_URL, wishlist_id, str(page_number))

    # connect to wishlist page
    wishlist_url = BASE_URL + wishlist_id
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    r = requests.get(wishlist_url, headers=headers)
  
    if r.status_code == 200:
        logger.info('   Successful connection to wishlist page {0}'.format(str(page_number)))
    else:
        logger.warning('    Error connecting to wishlist page {0}'.format(str(page_number)))

    wishlist_page = BeautifulSoup(html_data, "html.parser")

    # for each product on this page:
        # get the name, URL, new price, prime status, used price
    item_list = []
    items_on_page = wishlist_page.findAll(id=re.compile('item_'))
    if len(items_on_page) == 0:
        logger.info('   no items found')
        return []
    else:
        # each item div in the list has an ID that starts with item_
        for item in items_on_page:
            # if it isn't released yet, we don't need to add it
            if item.find('This title will be released'):
                logger.info("   Not yet out, won't add to DB")
                continue
            item_url = 'http://www.amazon.com' + item.find(class_='a-link-normal')["href"].split("?", 1)[0]
            date_added = item.find(class_='dateAddedText').text.strip().split('\n')[0].replace("Added ", "")
            ASIN = item_url.split("/")[-1]
            item_list.append({"ASIN": ASIN,
                             "date_added": date_added
                             })
        return item_list


def get_items_from_wishlist(wishlist_id):
    """ Takes a wishlist ID, validates that it's usable, gets a list of all items on it
    """
    # connect to wishlist page
    wishlist_url = BASE_URL + wishlist_id
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    r = requests.get(wishlist_url, headers=headers)
  
    if r.status_code == 200:
        logger.info('   Successful connection to main wishlist page')
    else:
        logger.warning('    Error connecting to main wishlist page')
    
    wishlist_first_page = BeautifulSoup(r.content, "html.parser")

    if wishlist_first_page.find('div', id="wishlistPagination"):
        #if we have multiple pages:
        # get the number of pages on the wishlist. in the pagination div, there's a list of pages to go to.
        # the second to last is the last page of the wishlist. (the last one is "next")
        final_page = int(wishlist_first_page.find('div', id="wishlistPagination").findAll('li')[-2].text)
        logger.info('wishlist has {0} pages'.format(final_page))
    else:
        logger.info('wishlist only has 1 page')
        final_page = 1

    all_items = []


    logger.info('about to check all pages - have a final page of {0}'.format(str(final_page))
    # run through each page:
    for i in range(1, final_page+1):
        all_items += get_items_from_wishlist_page(wishlist_id=wishlist_id, page_number=i)
        sleep(1)

    return all_items


# def main():
#     items = get_items_from_wishlist(PETES_WISHLIST_ID)
    


# if __name__ == "__main__":
#     main()
