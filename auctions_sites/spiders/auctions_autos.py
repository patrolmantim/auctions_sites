# -*- coding: utf-8 -*-
from scrapy import Spider, Request


class AuctionsAutosSpider(Spider):
    name = "auctions_autos"

    start_urls = [
        # "https://auctions.asm-autos.co.uk/account/sign-in/"
        "https://auctions.asm-autos.co.uk/auction/items/",
    ]

    handle_httpstatus_list = [
        400, 401, 402, 403, 404, 405, 406, 407, 409,
        500, 501, 502, 503, 504, 505, 506, 507, 509,
    ]

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'records_asm_autos.csv',
    }

    meta = {
        'handle_httpstatus_list': handle_httpstatus_list,
    }

    headers = {
        'authority': 'auctions.asm-autos.co.uk',
        'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        # 'referer': 'https://auctions.asm-autos.co.uk/account/sign-in/',
        'accept-language': 'en-US,en;q=0.9',
    }

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, meta=self.meta)

    def parse(self, response):
        for sel in response.css(".list_title")[:]:
            yield response.follow(sel.css('a::attr(href)').get(),
                                  # headers=self.headers,
                                  callback=self.parse_details, meta=self.meta)

        next_page_link = response.css('.page-item.active + .page-item a::attr(href)').get()
        if next_page_link:
            yield response.follow(next_page_link,
                                  # headers=self.headers,
                                  callback=self.parse, meta=self.meta)

    def parse_details(self, response):
        item = dict()
        item['details-title'] = response.css('.details-title::text').get()

        item.update(self.get_item_details(response))
        item.update(self.get_seller_details(response))
        item.update(self.get_vehicle_details(response))
        item.update(self.get_other_details(response))

        item['image_urls'] = response.css('*::attr(data-post-load)').getall()
        item['link'] = response.url

        # keys = response.css('.list-group.list-group-flush')[7].css('li span:first-child span::text').getall()
        # values = response.css('.list-group.list-group-flush')[7].css('li .list-group-text-item::text').getall()

        # seller_keys = response.css('.list-group.list-group-flush')[8].css('li span:first-child span::text').getall()
        # seller_values = response.css('.list-group.list-group-flush')[8].css('li .list-group-text-item a::text').getall()
        #
        # keys = [s.css('span:first-child span::text').get() for s in response.css('.list-group.list-group-flush')[9].css('li')]
        # values = [s.css('.list-group-text-item::text').get() for s in response.css('.list-group.list-group-flush')[9].css('li')]
        #
        # other_keys = [s.css('span:first-child span a::text').get() or s.css('span:first-child::text').get() for s in response.css('.list-group.list-group-flush')[10].css('li')]
        # other_values = [s.css('span:last-child::text').get() for s in response.css('.list-group.list-group-flush')[10].css('li')]
        # item['image_urls'] = response.css('#mainimg::attr(src)').get()

        return item

    def get_other_details(self, response):
        # other_details = {s.css('span:first-child span a::text').get(): s.css('span:last-child::text').get('').strip()
        #                  for s in response.css('.list-group.list-group-flush')[10].css('li')}

        other_details = {}
        for s in response.css('.list-group.list-group-flush')[10].css('li'):
            key = s.css('span:first-child span a::text').get('').strip()
            if not key:
                continue
            other_details[key] = s.css('span:last-child::text').get('').strip()

        return other_details

    def get_vehicle_details(self, response):
        # {
        #     s.css('span:first-child span::text').get(): s.css('.list-group-text-item::text').get() or s.css(
        #         '.list-group-text-small::text').get() or ', '.join(
        #         e.strip() for e in s.css('span:last-child ::text').getall() if e and e.strip()) for s in
        #     response.css('.list-group.list-group-flush')[9].css('li')}

        vehicle_details = {}

        for s in response.css('.list-group.list-group-flush')[9].css('li'):
            key = s.css('span:first-child span::text').get('').strip()
            if not key:
                continue

            vehicle_details[key] = s.css('.list-group-text-item::text').get() or \
                                   s.css('.list-group-text-small::text').get() or \
                                   ', '.join(e.strip() for e in s.css('span:last-child ::text').getall()
                                             if e and e.strip())

        return vehicle_details

    def get_seller_details(self, response):
        # seller_details = {
        #     s.css('span:first-child span::text').get(): s.css('li .list-group-text-item a::text').get() or s.css(
        #         '.list-group-text-small::text').get() for s in
        #     response.css('.list-group.list-group-flush')[8].css('li')}

        seller_details = {}

        for s in response.css('.list-group.list-group-flush')[8].css('li'):
            key = s.css('span:first-child span::text').get('').strip()
            if not key:
                continue

            seller_details[key] = s.css('li .list-group-text-item a::text').get() or \
                                  s.css('.list-group-text-small::text').get()

        return seller_details

    def get_item_details(self, response):
        # item_details = {
        #     s.css('span:first-child span::text').get(): s.css('li .list-group-text-item::text').get() or s.css(
        #         '.list-group-text-small::text').get() or ', '.join(
        #         d.strip() for d in s.css('.list-group-text-description::text').getall() if d and d.strip()) for s in
        #     response.css('.list-group.list-group-flush')[7].css('li')}

        item_details = {}

        for s in response.css('.list-group.list-group-flush')[7].css('li'):
            key = s.css('span:first-child span::text').get('').strip()
            if not key:
                continue

            item_details[key] = s.css('li .list-group-text-item::text').get() or \
                                s.css('.list-group-text-small::text').get() or \
                                ', '.join(d.strip() for d in s.css('.list-group-text-description::text').getall()
                                          if d and d.strip())

        return item_details
