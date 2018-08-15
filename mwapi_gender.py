import mwapi
from gender import getGenders


def get_genderize(name):
	"""
	Uses gender.py library to assign gender to first name using genderize.io API
	Must only use first name --> "Mark"

	name (string)
	"""
	info = getGenders(name)
	return info

def get_wikidata(name):

	"""
	uses mwapi to look up names in wikidata and assign gender 
	Must use full name --> "Mark Twain"

	name (string)
	"""
	USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12'

	session = mwapi.Session('https://en.wikipedia.org', user_agent = USER_AGENT)
	session2 = mwapi.Session('https://www.wikidata.org/', user_agent = USER_AGENT)

	query = session.get(action='query', titles = name, prop = 'pageprops')
	
	#retrieves page id --> used to get wikidata id
	for i in query['query']['pages']:
		pageid = i

	wd_id = query['query']['pages'][pageid]['pageprops']['wikibase_item']

	query2 = session2.get(action = 'wbgetentities', ids = wd_id, sites = 'wikidatawiki')

	
	gender = query2['entities'][wd_id]['claims']['P21'][0]['mainsnak']['datavalue']['value']['id']

	if gender == 'Q6581097':
		return "male"
	elif gender == "Q6581072":
		return "female"
	elif gender == "Q48270":
		return "Non-Binary"
	elif gender == "Q52261234":
		return "Neutral"

def get_Gender(name):
	"""
	combines get_genderize and get_wikidata to provide a more accurate assignment
	Must take in full name --> "Mark Twain"

	name (string)
	"""

	
	first,last = name.split(" ")

	genderize = get_genderize(first)

	if float(genderize[0][1]) >= .90:
		return genderize[0][0]
	else:
		try:
			return get_wikidata(name)
		except KeyError:
			if float(genderize[0][1]) > 0:
				return genderize[0][0]
			else:
				return "Unknown"


if __name__ == '__main__':
	print(get_Gender("Mark Twain"))

