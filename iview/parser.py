import gtk
import comm
from BeautifulSoup import BeautifulStoneSoup

def parse_config(soup):
	"""	There are lots of goodies in the config we get back from the ABC.
		In particular, it gives us the URLs of all the other XML data we
		need.
	"""

	soup = soup.replace('&amp;', '&#38;')

	xml = BeautifulStoneSoup(soup)

	# should look like "rtmp://cp53909.edgefcs.net/ondemand"
	rtmp_url = xml.find('param', attrs={'name':'server_streaming'}).get('value')
	rtmp_chunks = rtmp_url.split('/')

	return {
		'rtmp_url'  : rtmp_url,
		'rtmp_host' : rtmp_chunks[2],
		'rtmp_app'  : rtmp_chunks[3],
		'index_url' : xml.find('param', attrs={'name':'index'}).get('value'),
		'categories_url' : xml.find('param', attrs={'name':'categories'}).get('value'),
	}

def parse_auth(soup):
	"""	There are lots of goodies in the auth handshake we get back,
		but the only ones we are interested in are the RTMP URL, the auth
		token, and whether the connection is unmetered.
	"""

	xml = BeautifulStoneSoup(soup)

	# should look like "rtmp://203.18.195.10/ondemand"
	rtmp_url = xml.find('server').string

	if rtmp_url is not None:
		# the ISP provides their own iView server, i.e. unmetered
		rtmp_chunks = rtmp_url.split('/')
		rtmp_host = rtmp_chunks[2]
		rtmp_app = rtmp_chunks[3]
	else:
		# we are a bland generic ISP

		if not comm.iview_config:
			comm.get_config()

		rtmp_url = comm.iview_config['rtmp_url']
		rtmp_host = comm.iview_config['rtmp_host']
		rtmp_app = comm.iview_config['rtmp_app']

	return {
		'rtmp_url'  : rtmp_url,
		'rtmp_host' : rtmp_host,
		'rtmp_app'  : rtmp_app,
		'token'     : xml.find("token").string,
		'free'      : (xml.find("free").string == "yes")
	}

def parse_index(soup, programme):
	"""	This function parses the index, which is an overall listing
		of all programs available in iView. The index is divided into
		'series' and 'items'. Series are things like 'beached az', while
		items are things like 'beached az Episode 8'.
	"""
	xml = BeautifulStoneSoup(soup)

	for series in xml.findAll('series'):
		series_iter = programme.append(None, [series.find('title').string, series.get('id'), None, None])
		programme.append(series_iter, ['Loading...', None, None, None])

def parse_series_items(series_iter, soup, programme):
	# HACK: replace <abc: with < because BeautifulSoup doesn't have
	# any (obvious) way to inspect inside namespaces.
	soup = soup \
		.replace('<abc:', '<') \
		.replace('</abc:', '</')

	# HACK: replace &amp; with &#38; because HTML entities aren't
	# valid in plain XML, but the ABC doesn't know that.
	soup = soup.replace('&amp;', '&#38;')

	series_xml = BeautifulStoneSoup(soup)

	for program in series_xml.findAll('item'):
		programme.append(series_iter, [
				program.find('title').string,
				None,
				program.find('videoasset').string.split('.flv')[0],
				# we need to chop off the .flv off the end
				# as that's the way we need to give it to
				# the RTMP server for some reason
				program.find('description').string,
			])

