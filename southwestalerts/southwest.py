import json
import time

import asyncio

from pyppeteer import launch
from pyppeteer.network_manager import Request

import requests


API_KEY = 'l7xx0a43088fe6254712b10787646d1b298e'  # TODO: Retrieve this from https://mobile.southwest.com/js/config.js
BASE_URL = 'https://mobile.southwest.com'




class Southwest(object):
    def __init__(self, username, password, headers):
        self._session = _SouthwestSession(username, password, headers)

    def get_upcoming_trips(self):
        return self._session.get(
            '/api/customer/v1/accounts/account-number/{}/upcoming-trips'.format(self._session.account_number))

    def start_change_flight(self, record_locator, first_name, last_name):
        """Start the flight change process.

        This returns the flight including itinerary."""
        resp = self._session.get(
            '/api/extensions/v1/mobile/reservations/record-locator/{record_locator}?first-name={first_name}&last-name={last_name}&action=CHANGE'.format(
                record_locator=record_locator,
                first_name=first_name,
                last_name=last_name
            ))
        return resp

    def get_available_change_flights(self, record_locator, first_name, last_name, departure_date, origin_airport,
                                     destination_airport):
        """Select a specific flight and continue the checkout process."""
        url = '/api/extensions/v1/mobile/reservations/record-locator/{record_locator}/products?first-name={first_name}&last-name={last_name}&is-senior-passenger=false&trip%5B%5D%5Borigination%5D={origin_airport}&trip%5B%5D%5Bdestination%5D={destination_airport}&trip%5B%5D%5Bdeparture-date%5D={departure_date}'.format(
            record_locator=record_locator,
            first_name=first_name,
            last_name=last_name,
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date
        )
        return self._session.get(url)

    def get_price_change_flight(self, record_locator, first_name, last_name, product_id):
        url = '/api/reservations-api/v1/air-reservations/reservations/record-locator/{record_locator}/prices?first-name={first_name}&last-name={last_name}&product-id%5B%5D={product_id}'.format(
            record_locator=record_locator,
            first_name=first_name,
            last_name=last_name,
            product_id=product_id
        )
        return self._session.get(url)

    def get_cancellation_details(self, record_locator, first_name, last_name):
        url = '/api/reservations-api/v1/air-reservations/reservations/record-locator/{record_locator}?first-name={first_name}&last-name={last_name}&action=CANCEL'.format(
            record_locator=record_locator,
            first_name=first_name,
            last_name=last_name
        )
        return self._session.get(url)

    def get_available_flights(self, departure_date, origin_airport, destination_airport, currency='Points'):
        url = '/api/mobile-air-booking/v1/mobile-air-booking/page/flights/products?origination-airport={origin_airport}&destination-airport={destination_airport}&departure-date={departure_date}&number-adult-passengers=1&number-senior-passengers=0&currency=PTS'.format(
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date
        )
        return self._session.get(url)

    def get_available_flights_dollars(self, departure_date, origin_airport, destination_airport, currency='Dollars'):
        url = '/api/mobile-air-booking/v1/mobile-air-booking/page/flights/products?origination-airport={origin_airport}&destination-airport={destination_airport}&departure-date={departure_date}&number-adult-passengers=1&number-senior-passengers=0&currency=USD'.format(
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date
        )
        return self._session.get(url)


class _SouthwestSession():
    def __init__(self, username, password, headers):
        self._session = requests.Session()
        self._login(username, password, headers)

    def _login(self, username, password, headers):
        data = self.post('/api/customer/v1/accounts/login', headers, payload={
            'accountNumberOrUserName': username,
            'password': password
        })
        self.account_number = data['accessTokenDetails']['accountNumber']
        self.access_token = data['accessToken']
        self.headers = headers

    def get(self, path, headers, success_codes=[200]):
        resp = self._session.get(self._get_url(path), headers=self._get_headers(headers))
        return self._parsed_response(resp, success_codes=success_codes)

    def post(self, path, headers, payload, success_codes=[200]):
        resp = self._session.post(self._get_url(path), data=json.dumps(payload), headers=self._get_headers(headers))
        return self._parsed_response(resp, success_codes=success_codes)

    # async def _login_headers(self, url, username, password):
    #     await launch({"headless": False})
    #     page = await browser.newPage()
    #     await page.goto(url)
    #     time.sleep(2)
    #     selector = ".login-button--box"
    #     await page.waitForSelector(selector)
    #     await page.click(selector)
    #     selector = 'div[class="input huge"]'
    #     await page.waitForSelector(selector)
    #     await page.click(selector)
    #     await page.keyboard.type(username)
    #     selector = 'input[type="password"]'
    #     await page.click(selector)
    #     await page.keyboard.type(password)
    #     # await page.goto('http://example.com')
    #     selector = "#login-btn"
    #     await page.click(selector)
    #     time.sleep(5)
    #     await page.setRequestInterception(True)
    #     page.on('request', request_callback)
    #     await page.reload()
    #     return headers
    #
    # async def request_callback(request: Request):
    #     # Prints: {'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/69.0.3494.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
    #     headers = request.headers
    #     await request.continue_()


    @staticmethod
    def _get_url(path):
        return '{}{}'.format(BASE_URL, path)

    def _get_headers(self, headers):
        tempheaders = {
            'token': (self.access_token if hasattr(self, 'access_token') else None)
        }
        tempheaders = tempheaders.update(headers)
        return tempheaders

    @staticmethod
    def _parsed_response(response, success_codes=[200]):
        if response.status_code not in success_codes:
            print(response.text)
            #raise Exception(
            #    'Invalid status code received. Expected {}. Received {}.'.format(success_codes, response.status_code))
        return response.json()
