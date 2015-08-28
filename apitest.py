import amazonproduct

api = amazonproduct.API(locale='us')
result = api.item_lookup('1445566230', ResponseGroup='OfferFull',Condition='All')

for item in result.Items.Item:
	print '%s (%s)' % (item.ItemAttributes.Title, item.ASIN)