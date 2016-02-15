from bs4 import BeautifulSoup
import requests
import re
import sys
import random
import datetime
from time import sleep

BASE_URL = 'http://www.amazon.com/gp/registry/wishlist/'


#############################################
#
#   Quickie Functions
#
#############################################

def is_empty_wishlist(wishlistPage):
    """ Return True if the wishlist has no items in it, False otherwise

        ## TODO - Obviously this hardcoding sucks - add this to tests with "known bad" so we notice when they break
    """
    if wishlistPage.text.find("0 items on list") != -1:
        return True
    else:
        return False


def is_private_wishlist(wishlistPage):
    """ Return True if the wishlist is private, False otherwise

    ## TODO - Obviously this hardcoding sucks - add this to tests with "known bad" so we notice when they break
    """
    if wishlistPage.text.find("If this is your Wish List, please sign in") != -1:
        return True
    else:
        return False


def is_invalid_wishlist(wishListPage):
    """ Return True if the wishlist ID is not valid, False otherwise

        ## TODO - Obviously this hardcoding sucks - add this to tests with "known bad" so we notice when they break
    """
    if wishListPage.text.find("The Web address you entered is not a functioning page on our site") != -1:
        return True
    else:
        return False


def get_wishlist_name(wishlistID):
    """ Take an wishlistID and return the name of the wishlist (ex - "Pete's Wishlist" or "Christmas List" or "Kitchen Stuff I Want", etc)
    """
    print 'getting wishlist name for ' + str(wishlistID)
    r = requests.get(BASE_URL+'/'+wishlistID)
    wishListPage = BeautifulSoup(r.content, "html.parser")

    name = wishListPage.find(class_="a-size-extra-large stable clip-text").text.strip()

    return name


def get_items_from_wishlist_page(wishlistID, pageNumber):
    """ Take a wishlist ID and a page number, and return a list of all items on that page

        Returns a list of dicts with these keys:
            itemURL = URL for that variation of the items
            date_added = date the item was added to the wishListPage
            ASIN = the amazon ASIN for that variation of the item

    """
    print 'getting items from page ' + str(pageNumber)
    r = requests.get(BASE_URL+'/'+wishlistID+'/?page='+str(pageNumber))
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
            itemURL = 'http://www.amazon.com' + item.find(class_='a-link-normal')["href"] .split("?",1)[0]
            date_added = item.find(class_='dateAddedText').text.strip().split('\n')[0].replace("Added ","")
            ASIN = itemURL.split("/")[-1]
            itemList.append({"ASIN":ASIN,
                             "date_added": date_added
                             })
        return itemList


def get_items_from_wishlist(wishlistID):
    """ Takes a wishlist ID, validates that it's usable, gets a list of all items on it
    """
    # connect to wishlist page
    wishlistURL = BASE_URL+wishlistID
    r = requests.get(wishlistURL)
    wishlistFirstPage = BeautifulSoup(r.content, "html.parser")

    assert is_empty_wishlist(wishlistFirstPage) == False, wishlistID + ' is an empty wishlist!'
    assert is_private_wishlist(wishlistFirstPage) == False, wishlistID + ' is an private wishlist!'
    assert is_invalid_wishlist(wishlistFirstPage) == False, wishlistID + ' is a private or invalid wishlist!'

    if wishlistFirstPage.find(class_="a-pagination"):
        #if we have multiple pages:
        # get the number of pages on the wishlist. in the a-pagination div, there's a list of pages to go to.
        # the second to last is the last page of the wishlist. (the last one is "next")
        finalPage = int(wishlistFirstPage.find(class_="a-pagination").findAll('li')[-2].text)
    else:
        finalPage = 1

    allItems = []

    # only pull one page for testing
    finalPage = 1

    # run through each page:
    for i in range(1, finalPage+1):
        allItems += get_items_from_wishlist_page(wishlistID=wishlistID, pageNumber=i)
        sleep(1)

    return allItems


def main():
    items = get_items_from_wishlist('1ZF0FXNHUY7IG')
    for i in items:
        print i


if __name__ == "__main__":
    main()