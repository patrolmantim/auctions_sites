# -*- coding: utf-8 -*-
import json
from copy import deepcopy

from scrapy import Spider, Request, FormRequest


class HbcSpider(Spider):
    name = u"hbc_spider"
    base_url = u"https://www.hbc.co.uk"
    items_url = u"https://www.hbc.co.uk/cgi-bin/zyview2/D=vehicles/V=reserve_all?AUCTION_TYPE=OLO+%3A%3A+OLA+%3A%3A+future&AUCTION_TYPE_ZV_AND_OR=&TYPE_ZV_AND_OR=or&AUTOBIDDER_NONSALVAGE=&AUTOBIDDER_THEFT=&AUTOBIDDER_UNRECORDED=&TYPE=&ZV_MHV_LEN=20&ZV_AND_OR=and&SORT1_ZV_ENABLED=no&SORT1=&LOC_AREA=North+%3A%3A+Central+%3A%3A+South+%3A%3A+NorthWest+%3A%3A+SouthWest+%3A%3A+Scotland+%3A%3A+Ireland&LOC_AREA_ZV_AND_OR=or&CATEGORY=Repairable"

    start_urls = [
        u"https://www.hbc.co.uk/vehicle-auction/cgi-bin/as/login.pl"
    ]
    handle_httpstatus_list = [
        400, 401, 402, 403, 404, 405, 406, 407, 409,
        500, 501, 502, 503, 504, 505, 506, 507, 509,
    ]

    custom_settings = {
        u'FEED_FORMAT': 'csv',
        u'FEED_URI': 'records_hbc.csv',
    }
    meta = {
        'handle_httpstatus_list': handle_httpstatus_list,
    }
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, headers=self.headers, meta=self.meta)

    def parse(self, response):
        data = {
            u'User': u'wilsonspropertymgt@gmail.com',
            u'Passwd': u'nUaXkAM@wNpS3',
            # 'Stage': 'stage2',
            # 'FID_ID': '',
            # 'mode': '',
            # 'FID_REFERER': 'NO_FID_REF',
            # 'r': '',
            # 'CONTINUE': 'Login'
        }
        return FormRequest.from_response(response, formdata=data, callback=self.parse_login,
                                         headers=self.headers, meta=response.meta)

    def parse_login(self, response):
        return Request(self.items_url, callback=self.parse_listings,
                       headers=self.headers, meta=response.meta)

    def parse_listings(self, response):
        listing_urls = response.css('*[href^="/cgi-bin/zyview/D=vehicles/V=bidding/"]::attr(href)').getall()
        for url in listing_urls:
            url = self.base_url + url
            yield Request(url, callback=self.parse_details,
                          meta=self.meta, headers=self.headers)

        params = {
            'AUTOBIDDER': '',
            'AUTOBIDDER_NONSALVAGE': '',
            'AUTOBIDDER_THEFT': '',
            'AUTOBIDDER_UNRECORDED': '',
            'VEHICLE_CATNOS_ZV_ENABLED': 'no',
            'SHOW_SEL_BUTTON': '1',
            'SHOW_SEL_BUTTON_ZV_ENABLED': 'no',
            'ZV_MHV_LEN': '20',
            'ZV_AND_OR': 'and',
            'BID_ENDING': '',
            'AUCTION_TYPE': 'OLO :: OLA :: future',
            'AUCTION_TYPE_ZV_AND_OR': 'or',
            'LOC_AREA': 'North :: Central :: South :: NorthWest :: SouthWest :: Scotland :: Ireland',
            'LOC_AREA_ZV_AND_OR': 'or',
            'CATEGORY': 'Repairable',
        }

        post_url = u"AUTOBIDDER=&AUTOBIDDER_NONSALVAGE=&AUTOBIDDER_THEFT=&AUTOBIDDER_UNRECORDED=&VEHICLE_CATNOS_ZV_ENABLED=no&SHOW_SEL_BUTTON=1&SHOW_SEL_BUTTON_ZV_ENABLED=no&ZV_MHV_LEN=20&ZV_AND_OR=and&BID_ENDING=&AUCTION_TYPE=OLO+%3A%3A+OLA+%3A%3A+future&AUCTION_TYPE_ZV_AND_OR=or&LOC_AREA=North+%3A%3A+Central+%3A%3A+South+%3A%3A+NorthWest+%3A%3A+SouthWest+%3A%3A+Scotland+%3A%3A+Ireland&LOC_AREA_ZV_AND_OR=or&CATEGORY=Repairable"

        headers = deepcopy(self.headers)
        headers['Referer'] = response.url

        for next_page_url in response.css(u'.pageNumbers a::attr(href)').getall()[1:]:
            pre_url = next_page_url.split(u"('")[-1].split(u"'")[0].replace(u' ', u'%20')
            if pre_url in response.meta.get(u'scraped_urls', []):
                continue
            response.meta.setdefault(u'scraped_urls', []).append(pre_url)

            # url = f"{urljoin(self.base_url, pre_url)}?{post_url}"
            # url = urljoin(self.base_url, pre_url)
            url = self.base_url + pre_url
            yield Request(url, meta=response.meta, headers=headers,
                          callback=self.parse_listings, body=json.dumps(params))

    def parse_details(self, response):
        item = dict()

        for index, sel in enumerate(response.css('table')[8].css('tr')):
            raw = [e.strip() for e in sel.css('*::text').getall() if e and e.strip()]

            if index == 0:
                item[u'Title'] = raw[0] if raw else ''
                item[raw[1].replace(':', '')] = raw[2] if raw[2:] else ''
                item[u'Description'] = raw[3] if raw[3:] else ''
                item[u'ABI'] = raw[5] if raw[5:] else ''
                a = 0

            valid_values = []

            if index == 2:
                for e in raw:
                    e = unicode(e.replace(u':', u'')).replace(u'\xa0', u'').strip()
                    if e:
                        valid_values.append(e)

                keys = valid_values[:8]
                values = valid_values[8:]
                item.update({unicode(k): unicode(v) for k, v in zip(keys, values)})

                if not item.get(u'Reg. number'):
                    mid = int(len(valid_values) / 2)
                    keys = valid_values[:mid]
                    values = valid_values[mid:]
                    item.update({unicode(k): unicode(v) for k, v in zip(keys, values)})
                    a = 0

        item.setdefault(u'Location', '')
        item.setdefault(u'Auto/Manual', '')
        item.setdefault(u'Eng.Capacity', '')
        item.setdefault(u'Fueltype', '')
        item.setdefault(u'Odometer Reading', '')
        item.setdefault(u'Key', '')

        valid_hbc = response.url.split(u'R=')[-1]
        self.validate_item(item, valid_hbc)

        item[u'image_urls'] = response.css(u'.image-container img::attr(src)').getall()
        item[u'link'] = response.url
        return item

    def validate_item(self, item, valid_hbc):
        temp = deepcopy(item)
        temp.pop(u'Title')
        temp.pop(u'Description')

        if not self.check([u'speed'], item[u'Auto/Manual']):
            item[u'Auto/Manual'] = self.get_value([u'speed'], temp)

        if not self.check([u'cc'], item[u'Eng.Capacity']):
            item[u'Eng.Capacity'] = self.get_value([u'cc'], temp)

        if not self.check([u'fuel', u'petrol', u'diesel', u'hybrid', u'electric'], item[u'Fueltype']):
            item[u'Fueltype'] = self.get_value([u'fuel', u'diesel', u'petrol', u'hybrid', u'electric'], temp)

        if u'yes' != item[u'Key'] or u'no' != item[u'Key']:
            item[u'Key'] = u'Yes' if [unicode(v) for v in item.values() if v
                                      and unicode(v).lower().strip() == u'yes'] else u'No'

        if not unicode(item[u'Odometer Reading']).isnumeric():
            item[u'Odometer Reading'] = ([unicode(v) for k, v in temp.items() if unicode(v).isnumeric()
                                          and unicode(k) != u'HBC Cat. No.'] or [u''])[0]

        loc = (item.setdefault(u'Location', u'').lower() or u'').strip()
        loc_condition = (u'speed' in loc or u'cc' in loc or u'yes' == u'loc' or u'no' == loc)

        if u'HBC Cat. No.' in item and unicode(item[u'HBC Cat. No.']) != valid_hbc and loc_condition:
            item[u'Location'] = unicode(item[u'HBC Cat. No.'])

        loc = unicode(item[u'Location'].lower())
        if u'speed' in loc or u'cc' in loc or u'yes' == u'loc' or u'no' == loc or u'petrol' in loc \
                or u'deisel' in loc or u'hybrid' in loc or u'electric' in loc:
            item[u'Location'] = u''

        item[u'HBC Cat. No.'] = valid_hbc
        item[u'Odometer Reading'].strip(u'!!!')

        if item[u'Odometer Reading'].strip() == u'!!!':
            item[u'Odometer Reading'] = u''

    def check(self, keys, value):
        value = unicode(value)
        for k in keys:
            if unicode(k) in (value or u'').lower():
                return True

    def get_value(self, keys, item):
        return ([unicode(v) for v in item.values() if v and self.check(keys, v)] or [u''])[0]
