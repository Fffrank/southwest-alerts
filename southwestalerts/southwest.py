import json

import requests

BASE_URL = 'https://mobile.southwest.com'




class Southwest(object):
    def __init__(self, username, password, headers, cookies):
        self._session = _SouthwestSession(username, password, headers, cookies)

    def get_upcoming_trips(self):
        return self._session.getb(
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

    def get_available_flights_dollars(self, departure_date, origin_airport, destination_airport):
        url = '/api/mobile-air-booking/v1/mobile-air-booking/page/flights/products?origination-airport={origin_airport}&destination-airport={destination_airport}&departure-date={departure_date}&number-adult-passengers=1&number-senior-passengers=0&currency=USD'.format(
            origin_airport=origin_airport,
            destination_airport=destination_airport,
            departure_date=departure_date
        )
        return self._session.get(url)



class _SouthwestSession():
    def __init__(self, username, password, headers, cookies):
        self._session = requests.Session()
        self._login(username, password, headers, cookies)

    def _login(self, username, password, headers, cookies):
        headers['content-type']='application/vnd.swacorp.com.accounts.login-v1.0+json'
        data = requests.post(BASE_URL + '/api/customer/v1/accounts/login', json={
            'accountNumberOrUserName': username, 'password': password},
                             headers=headers
                                )
        data = data.json()
        self.account_number = data['accessTokenDetails']['accountNumber']
        self.access_token = data['accessToken']
        self.headers = headers
        self.cookies = cookies

    def get(self, path, success_codes=[200]):
        resp = self._session.get(self._get_url(path), headers=self._get_headers_all(self.headers))
        return self._parsed_response(resp, success_codes=success_codes)

    def getb(self, path, success_codes=[200]):
        resp = self._session.get(self._get_url(path), headers=self._get_headers_brief(self.headers))
        return self._parsed_response(resp, success_codes=success_codes)

    def post(self, path, payload, success_codes=[200]):
        resp = self._session.post(self._get_url(path), data=json.dumps(payload),
                                  headers=self._get_headers(self.headers))
        return self._parsed_response(resp, success_codes=success_codes)


    @staticmethod
    def _get_url(path):
        return '{}{}'.format(BASE_URL, path)

    def _get_cookies(self, cookies):
        for x in cookies:
            self._session.cookies.set(x['name'], x['value'], domain=x['domain'], path=x['path'])
        default = self._session.cookies
        return default


    def _get_headers_brief(self, headers):
        default = {
            'token': (self.access_token if hasattr(self, 'access_token') else None),
            'x-api-key': headers['x-api-key'],
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36',
            'origin': None,
            'content-type': None,
            'accept': None,
            'x-requested-with': None,
            'referer': None
        }
        tempheaders = {**headers, **default}
        return tempheaders

    def _get_headers_all(self, headers):
        default = {
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36",
        }
        tempheaders = {**headers, **default}
        tempheaders.pop('origin')
        tempheaders.pop('x-user-experience-id')
        #tempheaders.pop('user-agent')
        tempheaders.pop('content-type')
        tempheaders.pop('accept')
        tempheaders.pop('x-requested-with')
        tempheaders.pop('cookie')
        tempheaders.pop('referer')
        return tempheaders


    @staticmethod
    def _parsed_response(response, success_codes=[200]):
        if response.status_code not in success_codes:
            print(response.text)
            raise Exception(
                'Invalid status code received. Expected {}. Received {}.'.format(success_codes, response.status_code))
        return response.json()


