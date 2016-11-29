from bs4 import BeautifulSoup
import requests
import re
from time import sleep

BASE_URL = 'http://www.amazon.com/gp/registry/wishlist/'
PETES_WISHLIST_ID = '1ZF0FXNHUY7IG'

#############################################
#
#   Quickie Functions
#
#############################################


def get_items_from_wishlist_page(wishlistID, pageNumber):
    """ Take a wishlist ID and a page number, and return a list of all items on that page

        Returns a list of dicts with these keys:
            itemURL = URL for that variation of the items
            date_added = date the item was added to the wishListPage
            ASIN = the amazon ASIN for that variation of the item

    """
    print 'getting items from page ' + str(pageNumber)
    page_url = "{0}/{1}/?page={2}".format(BASE_URL, wishlistID, str(pageNumber))
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    r = requests.get(page_url, headers=headers)

    wishListPage = BeautifulSoup(r.content, "html.parser")

    # for each product on this page:
        # get the name, URL, new price, prime status, used price
    itemList = []
    listOfItemsOnPage = wishListPage.findAll(id=re.compile('item_'))
    if len(listOfItemsOnPage) == 0:
        return []
    else:
        # each item div in the list has an ID that starts with item_
        for item in wishListPage.findAll(id=re.compile('item_')):
            # if it isn't released yet, we don't need to add it
            if item.find('This title will be released'):
                print "Not yet out, won't add to DB"
                continue
            itemURL = 'http://www.amazon.com' + item.find(class_='a-link-normal')["href"] .split("?", 1)[0]
            date_added = item.find(class_='dateAddedText').text.strip().split('\n')[0].replace("Added ", "")
            ASIN = itemURL.split("/")[-1]
            itemList.append({"ASIN": ASIN,
                             "date_added": date_added
                             })
        return itemList


def get_items_from_wishlist(wishlistID):
    """ Takes a wishlist ID, validates that it's usable, gets a list of all items on it
    """
    # connect to wishlist page
    wishlistURL = BASE_URL + wishlistID
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    }
    r = requests.get(wishlistURL, headers=headers)
    wishlistFirstPage = BeautifulSoup(r.content, "html.parser")

    if wishlistFirstPage.find(class_="a-pagination"):
        #if we have multiple pages:
        # get the number of pages on the wishlist. in the a-pagination div, there's a list of pages to go to.
        # the second to last is the last page of the wishlist. (the last one is "next")
        finalPage = int(wishlistFirstPage.find(class_="a-pagination").findAll('li')[-2].text)
        print 'wishlist has {0} pages'.format(finalPage)
    else:
        print 'wishlist only has 1 page'
        finalPage = 1

    allItems = []

    # only pull one page for testing
    # finalPage = 1

    print 'about to check all pages - have a final page of {0}'.format(str(finalPage))
    # run through each page:
    for i in range(1, finalPage+1):
        allItems += get_items_from_wishlist_page(wishlistID=wishlistID, pageNumber=i)
        sleep(1)

    return allItems


def main():
    items = get_items_from_wishlist(PETES_WISHLIST_ID)
    for i in items:
        print i


if __name__ == "__main__":
    main()
