from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import sys

#### NEXT UP

# convert code to handle new DB layout
# test, test, test

# write mvp Django frontend


#TODO

    # Need
        # put this on petecartwright.com and schedule
        # set up email notification
        # handle textbook pages. ex: http://www.amazon.com/Beautiful-Code-Leading-Programmers-Practice/dp/0596510047/

    # Nice
        # paralell retrievals? (http://docs.python-requests.org/en/v0.10.6/user/advanced/)
        # design interface for web version
        # prime status for lowest used price - would need to "click through" to the used/new pages

    # Done
        # put these into a DB    
        # get the itemID
        # added amazon referrer in
        # handle empty wishlist - make fake acct to test
        # handle private wishlists
        # handle not yet released
        # handle all editions - paperback, hardcover, anything else.


def getItemsFromWishListPage(wishlistURL, wishlistID, pageNumber):
    print 'getting items from page ' + str(pageNumber)
    r = requests.get(wishlistURL+'/'+wishlistID+'/?page='+str(pageNumber))
    wishListPage = BeautifulSoup(r.content)

    # for each product on this page:
        # get the name, URL, new price, prime status, used price
    itemList = []
    # TODO PTC - handle empty wishlist
    listOfItemsOnPage = wishListPage.findAll(id=re.compile('item_'))
    if len(listOfItemsOnPage) == 0:
        return []
    else:
        # each item div in the list has an ID that starts with item_
        for item in wishListPage.findAll(id=re.compile('item_')):
            
            itemTitle = item.find(('a'))["title"]
            print itemTitle
            # if it isn't released yet, we don't need to add it
            if item.find('This title will be released'):
                print "Not yet out, won't add to DB"
                continue
            # start with the base URL, add the result from the link in the wishlist item
            # then split off everything after (and including) the first "?"
            itemURL = 'http://www.amazon.com' + item.find(class_='a-link-normal')["href"] .split("?",1)[0] + '?tag=thithargr-20'
            itemID = itemURL.split("/")[-1]
            fullPrice = item.find(id=re.compile('itemPrice_')).text.strip().split('$')[-1]

            dateAdded = item.find(class_='dateAddedText').text.strip().split('\n')[0]

            # get the star rating of the item - ranges from 1 to 5
            starRating = getStarRating(item)

            # get thumbnail image URL for displaying elsewhere

            # this URL will usually be in the format 
            # http://ecx.images-amazon.com/images/I/<<random text>>.<<qualifiers for size and Look Inside arrow>>.jpg
            # we want to take the first three sections, adding in the  "."s and then everything after the final "."
            # (probably always jpg but why not be sure)

            thumbnailURLParts = item.find("img")['src'].split(".")
            fullImageURL = thumbnailURLParts[0]+'.'+thumbnailURLParts[1]+'.'+thumbnailURLParts[2]+'.'+thumbnailURLParts[-1]

            itemList.append({"wishlistID": wishlistID,
                             "itemID": itemID,
                             "itemTitle": itemTitle,
                             "itemURL": itemURL,
                             "starRating": starRating,
                             "thumbnailURL": thumbnailURL,
                             "fullImageURL": fullImageURL
                             })
        return itemList


def getStarRating(itemSoup):

    if itemSoup.find(class_ = 'a-star-5'):
        starRating = '5'
    elif itemSoup.find(class_ = 'a-star-4-5'):
        starRating = '4.5'
    elif itemSoup.find(class_ = 'a-star-4'):
        starRating = '4'
    elif itemSoup.find(class_ = 'a-star-3-5'):
        starRating = '3.5'
    elif itemSoup.find(class_ = 'a-star-3'):
        starRating = '3'
    elif itemSoup.find(class_ = 'a-star-2-5'):
        starRating = '2.5'
    elif itemSoup.find(class_ = 'a-star-2'):
        starRating = '2'
    elif itemSoup.find(class_ = 'a-star-1-5'):
        starRating = '1.5'
    elif itemSoup.find(class_ = 'a-star-1'):
        starRating = '1'
    else:
        starRating = 'None'    

    return starRating    

def getPrimeStatus(itemSoup):
    ''' take a BeautifulSoup object of an item and return its 
        prime status as a string
    '''
    # look for it either being fulfilled by amazon or sold by. Those should be all (?) Prime?
    if (   itemSoup.find(text=re.compile("Fulfilled by Amazon")) 
        or itemSoup.find(text=re.compile("Ships from and sold by Amazon.com."))
        ):
        primeStatus = 'Prime'
    elif itemSoup.find(text=re.compile("Ships with any qualifying order")):
        primeStatus = 'Add-on item'
    else:
        primeStatus = 'Not Prime'

    return primeStatus


def getCategories(itemSoup):
    ''' take a BeautifulSoup object of an item's page 
        return a list of the categories we think it's in as a comma seperated string
    '''
    categoriesList = []
    breadCrumbs = itemSoup.find(id='wayfinding-breadcrumbs_container')
    if breadCrumbs is not None:
        breadCrumbList = breadCrumbs.findAll('li')
        for l in breadCrumbList:        
            # they use the "single right-pointing angle quotation mark" as a divider
            if l.text.strip() != u"\u203A":
                categoriesList.append(l.text.strip())

    categories = ",".join(categoriesList)

    return categories


def getVersions(itemSoup):

    versions = []

    # books will have the little boxes with the 'Hardcover $24.95 | used from $21.45 | New from $22.34' boxes
    # amazon calls those swatches. If they exist, get all the data from them.
    if itemSoup.find(id='tmmSwatches'):
        swatchElements = itemSoup.find(id='tmmSwatches').findAll('li',class_="swatchElement")
        for e in swatchElements:
            itemType = e.find(class_='a-button-text').find('span').text  # Hardcover
            basePrice = e.find(class_=re.compile('a-color-')).text.strip().strip('from ').strip('$')  # 24.95
            usedPrice = None
            newPrice = None
            collectiblePrice = None
            if e.find(class_='tmm-olp-links'):
                if e.find(class_='olp-used'):
                    usedPrice = e.find(class_='olp-used').find(class_='olp-from').nextSibling.strip().strip('$')       # 21.95
                if e.find(class_='olp-new'):
                    newPrice = e.find(class_='olp-new').find(class_='olp-from').nextSibling.strip().strip('$')
                if e.find(class_='olp-collectible'):
                    collectiblePrice = e.find(class_='olp-collectible').find(class_='olp-from').nextSibling.strip().strip('$')

            versions.append({'itemType': itemType, 
                             'basePrice': basePrice, 
                             'usedPrice': usedPrice, 
                             'newPrice': newPrice,
                             'collectiblePrice': collectiblePrice})
    else:
        # if not, it's probably not a book.
        # this one is a good example of three prices - From Amazon, New, and Used
        # http://www.amazon.com/dp/B004C3CAB8/
        
        basePrice = itemSoup.find(id='priceblock_ourprice')
        spans = itemSoup.findAll('span')
        for s in spans:
            if s.find(class_='a-color-price'):
                itemType = re.search(r'condition=([a-zA-Z]+)',str(s.a)).groups(0)[0]
                price = s.find(class_='a-color-price').text.strip('$')
                print 'condition: {0}, price: {1}'.format(condition, price)


        


    return versions


def getInfoFromItemPage(item):
    """ takes an amazon item dict
        returns a dict with :
            prime status
            categories (as string)
            all versions and prices (as list of dicts)

    """

    r = requests.get(item["itemURL"])
    itemSoup = BeautifulSoup(r.content)
    
    primeStatus = getPrimeStatus(itemSoup)
    categories = getCategories(itemSoup)
    
    # array of dicts - one for each version of the product - hardcover, paperback, kindle, etc
    versions = getVersions(itemSoup)

    # check to see if it's a textbook - if it is, skip for now.
    if itemSoup.text.find('Try the eTextbook free') != -1:
        print "Can't handle textbooks yet!"
        dictToReturn = {"primeStatus": None,
                        "categories": None,
                        "versions": None
                       }
        return dictToReturn
    
    dictToReturn = {"primeStatus": primeStatus,
                    "categories": categories,
                    "versions": versions
                    }

    return dictToReturn


def addItemsToDB(itemList):

    # set up connection
    con = sqlite3.connect('wishlist.db')

    with con:
        cur = con.cursor()
        # clear out the table (for now)
        cur.execute('delete from wishlist where wishlistID = "' + itemList[0]['wishlistID'] + '";')
        for item in itemList:
            # insert into the wishlistItem table 

            tupleToInsert = (item['wishlistID'],
                             item['itemID'],
                             item['itemURL'],
                             item['itemTitle'],
                             item['starRating'],
                             item['fullImageURL'],
                             item['thumbnailURL']
                             )

            cur.execute('insert into wishlistItems values (?,?,?,?,?,?,?)', tupleToInsert)


def isEmptyWishlist(wishlistPage):
    if wishlistPage.text.find("0 items on list") != -1:
        return True
    else:
        return False

def isPrivateWishlist(wishlistPage):
    if wishlistPage.text.find("If this is your Wish List, please sign in") != -1:
        return True
    else:
        return False


def removeWishlistFromDB(wishlistID):
    """ remove a wishlist and items from wishlistItems table
        does not affect anything in the Items table
    """
    con = sqlite3.connect('wishlist.db')
    
    with con:
        cur = con.cursor()
        removeSQL = "delete from wishlistItems where wishlistId = '{0}'".format(wishlistID)
        cur.execute(removeSQL)


def refreshWishlist(wishlistID):

    # delete all items from wishlist in DB

    BASE_URL = 'http://www.amazon.com/gp/registry/wishlist/'
    # connect to wishlist page
    wishlistURL = BASE_URL+wishlistID
    r = requests.get(wishlistURL)
    wishlistFirstPage = BeautifulSoup(r.content)

    if isEmptyWishlist(wishlistFirstPage):
        print wishlistID + 'is an empty wishlist!'
        sys.exit()

    if isPrivateWishlist(wishlistFirstPage):
        print wishlistID + 'is an private wishlist!'
        sys.exit()

    if wishlistFirstPage.find(class_="a-pagination"):
        #if we have multiple pages:
        # get the number of pages on the wishlist
        # in the a-pagination div, there's a list of pages to go to
        # the second to last is the last page of the wishlist
        # (the last one is "next")
        finalPage = int(wishlistFirstPage.find(class_="a-pagination").findAll('li')[-2].text)
    else:
        finalPage = 1

    allItems = []

    # only pull one page for testing
    finalPage = 1

    # run through each page:
    for i in range(1, finalPage+1):
        allItems += getItemsFromWishListPage(wishlistURL=BASE_URL, wishlistID=wishlistID, pageNumber=i)

    # get the info from the item page for each item
    # category, prime status, etc    
    for item in allItems:
        print 'getting info for item ' +  item['itemTitle']
        item.update(getInfoFromItemPage(item))

    addItemsToDB(allItems)



def refreshAllWishlists():
    
    # get wishlists from DB
    wishlists = []

    con = sqlite3.connect('wishlist.db')
    with con:
        cur = con.cursor()
        sql = 'select wishlistID from wishlist group by 1;'
        cur.execute(sql)
        data = cur.fetchAll()
        for d in data:
            wishlists.append(d[0])

    for w in wishlist:
        # TODO - can this be parallellized without angering Amazon?
        refreshWishlist(w)


def main():

    refreshWishlist('1ZF0FXNHUY7IG')




if __name__ == "__main__":

    main()
