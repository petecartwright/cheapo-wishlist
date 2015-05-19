from bs4 import beautifulsoup
import requests


#TODO
    # parse each page for each item
        # get the prime status
            ## check on item page for "Yes, I want FREE Two-Day Shipping with Amazon Prime"
        # get the category

def getItemsFromWishListPage(amazonURI, pageNumber):
    r = requests.get(amazonURI+'/?page='+str(pageNumber))
    wishListPage = BeautifulSoup(r.content)

    # for each product on this page:
        # get the name, URL, new price, prime status, used price

    itemList = []
    # TODO PTC - handle empty wishlist
    f = open('itemlist.txt','w')
    # each item div in the list has an ID that starts with item_
    for item in wishListPage.findAll(id=re.compile('item_')):
        itemTitle = item.find(('a'))["title"]
        URL = 'http://www.amazom.com/' + item.find(class_='a-link-normal')["href"]
        fullPrice = item.find(id=re.compile('itemPrice_')).text.strip()
        # not everything has a used and new price
        usedAndNewPrice = ''
        if item.find(class_="itemUsedAndNewPrice"):
            usedAndNewPrice = item.find(class_="itemUsedAndNewPrice").text
        dateAdded = item.find(class_='dateAddedText').text.strip().split('\n')[0]

        if item.find(class_='a-icon-prime'):
            primeStatus = True
        else:
            primeStatus = False
        starRating = ''
        if item.find(class+'a-star-5'):
            starRating = '5'
        elif item.find(class+'a-star-4-5'):
            starRating = '4.5'
        elif item.find(class+'a-star-4'):
            starRating = '4'
        elif item.find(class+'a-star-3-5'):
            starRating = '3.5'
        elif item.find(class+'a-star-3'):
            starRating = '3'
        elif item.find(class+'a-star-2-5'):
            starRating = '2.5'
        elif item.find(class+'a-star-2'):
            starRating = '2'
        elif item.find(class+'a-star-1-5'):
            starRating = '1.5'
        elif item.find(class+'a-star-1'):
            starRating = '1'
        else:
            starRating = 'None'

        itemList.append({"fullPrice": fullPrice,
                         "usedAndNewPrice": usedAndNewPrice,
                         "itemTitle": itemTitle,
                         "primeStatus": primeStatus
                         })
    f.write(str(itemList))
    return itemList






if __name__ == "__main__":
    BASE_URI = 'http://www.amazon.com/gp/registry/wishlist/'
    WISHLIST_ID = '1ZF0FXNHUY7IG'

    # connect to wishlist page
    amazonURI = BASE_URL+WISHLIST_ID
    r = requests.get(amazonURI)
    wishlistFirstPage = BeautifulSoup(r.content)

    # check for multiple pages
    if wishlistFirstPage.find(class_="a-pagination"):
        #if we have multiple pages
        # get the number of pages on the wishlist
        # in the a-pagination div, there's a list of pages to go to
        # the last one is "next", and the second to last is the last page
        # of the wishlist
        finalPage = int(soup.find(class_="a-pagination").findAll('li')[-2].text)
    else:
        finalPage = 1

    allItems = []
    # run through each page:
    for i in range(1, finalPage):
        allItems += getItemsFromWishListPage(amazonURI=amazonURI, pageNumber=i)







