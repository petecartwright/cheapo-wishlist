from bs4 import BeautifulSoup
import requests
import re
import sqlite3
import sys

#TODO

    # additional comments

    # Need
        # put this on petecartwright.com and schedule
        # set up email notification

    # Nice
        # handle all other editions - paperback, hardcover, anything else. pop into a dict?   "xxxxxxPrice": xxxxxxPrice?   
        # paralell retrievals? (http://docs.python-requests.org/en/v0.10.6/user/advanced/)
        # design interface for web version

    # Open Q?
        # can i get a wishlist from the Amazon email?

    # Done
        # put these into a DB    
        # get the itemID
        # added amazon referrer in
        # handle empty wishlist - make fake acct to test
        # handle private wishlists
        # handle not yet released


def getItemsFromWishListPage(amazonURL, wishlistID, pageNumber):
    print 'getting items from page ' + str(pageNumber)
    r = requests.get(amazonURL+'/?page='+str(pageNumber))
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
                continue

            # start with the base URL, add the result from the link in the wishlist item
            # then split off everything after (and including) the first "?"
            itemURL = 'http://www.amazon.com' + item.find(class_='a-link-normal')["href"] .split("?",1)[0] + '?tag=thithargr-20'

            itemID = itemURL.split("/")[-1]

            fullPrice = item.find(id=re.compile('itemPrice_')).text.strip().split('$')[-1]

            # not everything has a used and new price
            usedAndNewPrice = ''
            if item.find(class_="itemUsedAndNewPrice"):
                usedAndNewPrice = item.find(class_="itemUsedAndNewPrice").text.strip().split('$')[-1]

            dateAdded = item.find(class_='dateAddedText').text.strip().split('\n')[0]

            # get the star rating of the item - ranges from 1 to 5
            if item.find(class_ = 'a-star-5'):
                starRating = '5'
            elif item.find(class_ = 'a-star-4-5'):
                starRating = '4.5'
            elif item.find(class_ = 'a-star-4'):
                starRating = '4'
            elif item.find(class_ = 'a-star-3-5'):
                starRating = '3.5'
            elif item.find(class_ = 'a-star-3'):
                starRating = '3'
            elif item.find(class_ = 'a-star-2-5'):
                starRating = '2.5'
            elif item.find(class_ = 'a-star-2'):
                starRating = '2'
            elif item.find(class_ = 'a-star-1-5'):
                starRating = '1.5'
            elif item.find(class_ = 'a-star-1'):
                starRating = '1'
            else:
                starRating = 'None'

            # get thumbnail image URL for displaying elsewhere

            # this URL will usually be in the format 
            # http://ecx.images-amazon.com/images/I/<<random text>>.<<qualifiers for size and Look Inside arrow>>.jpg
            # we want to take the first three sections, adding in the  "."s and then everything after the final "."
            # (probably always jpg but why not be sure)

            thumbnailURL = item.find("img")['src']
            thumbnailURLParts = thumbnailURL.split(".")
            fullImageURL = thumbnailURLParts[0]+'.'+thumbnailURLParts[1]+'.'+thumbnailURLParts[2]+'.'+thumbnailURLParts[-1]

            if fullPrice != '' and usedAndNewPrice != '':
                priceDiff = float(fullPrice) - float(usedAndNewPrice)
            else:
                priceDiff = 'N/A'

            underABuck = False
            if usedAndNewPrice.find('.') != -1:
                if float(usedAndNewPrice) < 1.00:
                    underABuck = True

            if fullPrice.find('.') != -1:
                if float(fullPrice) < 1.00:
                    underABuck = True
                
            itemList.append({"wishlistID": wishlistID,
                             "itemID": itemID,
                             "itemTitle": itemTitle,
                             "itemURL": itemURL,
                             "fullPrice": fullPrice,
                             "usedAndNewPrice": usedAndNewPrice,
                             "starRating": starRating,
                             "thumbnailURL": thumbnailURL,
                             "fullImageURL": fullImageURL,
                             "underABuck": underABuck,
                             "priceDiff": priceDiff
                             })
        return itemList


def getInfoFromItemPage(item):
    """ takes an amazon item dict
        checks for: prime shipping
                    category
                    if it's a kindle edition and if so, the hardcover and paperback URLs

    """

    r = requests.get(item["itemURL"])
    itemSoup = BeautifulSoup(r.content)

    # look for it either being fulfilled by amazon or sold by. Those should be all (?) Prime?
    if (   itemSoup.find(text=re.compile("Fulfilled by Amazon")) 
        or itemSoup.find(text=re.compile("Ships from and sold by Amazon.com."))
        ):
        primeStatus = 'Prime'
    elif itemSoup.find(text=re.compile("Ships with any qualifying order")):
        primeStatus = 'Add-on item'
    else:
        primeStatus = 'Not Prime'

    # get the category - getting all for now. how granular do we need this?
    categoriesList = []
    breadCrumbs = itemSoup.find(id='wayfinding-breadcrumbs_container')
    if breadCrumbs is not None:
        breadCrumbList = breadCrumbs.findAll('li')
        for l in breadCrumbList:        
            # they use the "single right-pointing angle quotation mark" as a divider
            if l.text.strip() != u"\u203A":
                categoriesList.append(l.text.strip())

    categories = ",".join(categoriesList)

    # find out if it's a kindle edition, and if it is
    # get the URLs for the paperback and hardcopy editions
    if itemSoup.find(text=re.compile("[Kindle Edition]")):
        kindleStatus = 'Kindle'
        # if itemSoup.find('a',text=re.compile("Hardcover")):
            # hardcoverPrice = 
            # paperbackURL = itemSoup.find('a',text=re.compile("Paperback"))['href']
            # paperbackPrice = 
    else:
        kindleStatus = 'Not Kindle'
        # hardcoverURL = ''
        # paperbackURL = ''


    dictToReturn = {"primeStatus": primeStatus,
                    "categories": categories,
                    "kindleStatus": kindleStatus
                    # "hardcoverURL": hardcoverURL,
                    # "paperbackURL": paperbackURL
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
            tupleToInsert = (item['wishlistID'],
                             item['itemID'],
                             item['itemURL'],
                             item['itemTitle'],
                             item['fullPrice'],
                             item['usedAndNewPrice'],
                             item['primeStatus'],
                             item['kindleStatus'],
                             item['starRating'],
                             item['categories'],
                             item['fullImageURL'],
                             item['thumbnailURL'],
                             item['underABuck'],
                             item['priceDiff']
                             )

            cur.execute('insert into wishlist values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)', tupleToInsert)


def main():

    BASE_URL = 'http://www.amazon.com/gp/registry/wishlist/'
    WISHLIST_ID = '1ZF0FXNHUY7IG'
    # connect to wishlist page
    amazonURL = BASE_URL+WISHLIST_ID
    r = requests.get(amazonURL)
    wishlistFirstPage = BeautifulSoup(r.content)

    # check for multiple pages

    if wishlistFirstPage.text.find("0 items on list") != -1:
        print WISHLIST_ID + 'is an empty wishlist!'
        sys.exit()

    if wishlistFirstPage.text.find("The Web address you entered is not a functioning page on our site") != -1:
        print WISHLIST_ID + ' is a private or invalid wishlist!'
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
        
        allItems += getItemsFromWishListPage(amazonURL=amazonURL, wishlistID=WISHLIST_ID, pageNumber=i)

    # get the info from the item page for each item
    # category, prime status, etc    
    for item in allItems:
        print 'getting info for item ' +  item['itemTitle']
        item.update(getInfoFromItemPage(item))

    addItemsToDB(allItems)
    # f = open('itemlist.txt','w')
    # f.write(str(allItems))
    # f.close()



if __name__ == "__main__":
    main()
