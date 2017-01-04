from bs4 import BeautifulSoup
import requests
import re
import os
from subprocess import check_output
from time import sleep

import logging

FORMAT = '%(asctime)-15s %(message)s'
current_folder = os.path.dirname(os.path.realpath(__file__))
logfile = os.path.join(current_folder, 'log/wishlist.txt')
logging.basicConfig(filename=logfile, level=logging.DEBUG, format=FORMAT)
logger = logging.getLogger(__name__)

BASE_URL = 'https://www.amazon.com/gp/registry/wishlist/'
PETES_WISHLIST_ID = '1ZF0FXNHUY7IG'

#############################################
#
#   Quickie Functions
#
#############################################


def get_data_via_curl(url):
    """ Take a standard URL, return the results from a curl call as a string"""
    curl_result = check_output(["curl", url])
    ##TODO - really need some error checking here
    return curl_result


def get_items_from_wishlist_page(wishlist_id, page_number):
    """ Take a wishlist ID and a page number, and return a list of all items on that page

        Returns a list of dicts with these keys:
            item_url = URL for that variation of the items
            date_added = date the item was added to the wishlist_page
            ASIN = the amazon ASIN for that variation of the item

    """
    print 'getting items from page ' + str(page_number)
    page_url = "{0}/{1}/?page={2}".format(BASE_URL, wishlist_id, str(page_number))
    html_data = get_data_via_curl(page_url)

    wishlist_page = BeautifulSoup(html_data, "html.parser")

    # for each product on this page:
        # get the name, URL, new price, prime status, used price
    item_list = []
    items_on_page = wishlist_page.findAll(id=re.compile('item_'))
    if len(items_on_page) == 0:
        print 'no items found'
        return []
    else:
        # each item div in the list has an ID that starts with item_
        for item in items_on_page:
            # if it isn't released yet, we don't need to add it
            if item.find('This title will be released'):
                print "Not yet out, won't add to DB"
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
    html_data = get_data_via_curl(wishlist_url)

    wishlist_first_page = BeautifulSoup(html_data, "html.parser")

    if wishlist_first_page.find('div', id="wishlistPagination"):
        #if we have multiple pages:
        # get the number of pages on the wishlist. in the pagination div, there's a list of pages to go to.
        # the second to last is the last page of the wishlist. (the last one is "next")
        final_page = int(wishlist_first_page.find('div', id="wishlistPagination").findAll('li')[-2].text)
        print 'wishlist has {0} pages'.format(final_page)
    else:
        print 'wishlist only has 1 page'
        final_page = 1

    all_items = []

    # only pull one page for testing
    # final_page = 1

    print 'about to check all pages - have a final page of {0}'.format(str(final_page))
    # run through each page:
    for i in range(1, final_page+1):
        all_items += get_items_from_wishlist_page(wishlist_id=wishlist_id, page_number=i)
        sleep(1)

    return all_items


def main():
    items = get_items_from_wishlist(PETES_WISHLIST_ID)
    for i in items:
        print i


if __name__ == "__main__":
    print logfile
    main()
