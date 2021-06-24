import locale
import time
locale.resetlocale()
#locale.setlocale(locale.LC_ALL, '')
import logging
import requests
import sys
import asyncio

# from pyppeteer_stealth import stealth -- MAY NEED TO REIMPLEMENT IN THE FUTURE

from pyppeteer import launch
from pyppeteer.network_manager import Request

from southwestalerts.southwest import Southwest
from southwestalerts import settings


async def catch_response(response):
    if response.url == "https://mobile.southwest.com/api/security/v4/security/token":
        user.account = await response.json()
        user.account['messageKey'] = 200
        user.account['code'] = 0
        if user.account is not None:
            if user.account['customers.userInformation.accountNumber'] is not None:
                logging.info('Detected account %s and captured headers.', user.account['customers.userInformation.accountNumber'])
    if response.url == "https://mobile.southwest.com/api/mobile-misc/v1/mobile-misc/page/upcoming-trips":
        user.trips = await response.json()
        logging.info('Found trips!')


async def get_page(browser, url):
    page = await browser.newPage()
    await page.goto(url)
    return page


async def request_callback(request: Request):
    # Prints: {'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/69.0.3494.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
    if request.url == "https://mobile.southwest.com/api/security/v4/security/token":
        user.headers = request.headers
        #logging.info(user.headers)
        await request.continue_()
    else:
        await request.continue_()


async def login_get_headers(url, username, password):
    f = 1
    while f < 5:
        logging.info('Attempt %s at capturing headers....', f)
        f = f+1
        browser = await launch({'headless': False, 'args': ['--no-sandbox', '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36']})
        page = await browser.newPage()
        # await stealth(page)
        # await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36")
        await page.goto(url, options={'timeout':600000})
        time.sleep(2)
        selector = ".login-button--box"
        await page.waitForSelector(selector)
        await page.click(selector)
        time.sleep(2)
        selector = 'div[class="input huge"]'
        await page.waitForSelector(selector)
        await page.click(selector)
        await page.keyboard.type(username)
        selector = 'input[type="password"]'
        await page.click(selector)
        await page.keyboard.type(password)
        selector = "#login-btn"
        await page.setRequestInterception(True)
        page.on('request', request_callback)
        time.sleep(2)
        page.on('response', catch_response)
        await page.click(selector)
        time.sleep(2)
        user.cookies = await page.cookies()
        await browser.close()
        #logging.info(user.headers['x-api-idtoken'])
        #logging.info(user.headers)
        #return user.headers
        if user.account is not None and user.account['messageKey'] is not None:
            if user.account['messageKey'] == 'ERROR':
                continue
        if user.account is not None and user.account['code'] == 429999999:
            continue
        if user.headers is not None and user.account is not None:
            user.headers['authorization'] = "Bearer " + user.account['access_token']
            user.headers['x-api-idtoken'] = user.account['id_token']
            await browser.close()
            return user.headers
        if user.account is None:
            continue
        else:
            logging.info('Failed to capture Southwest.com headers after 5 attempts -- exiting')
            quit()

# async def login_get_headers(url, username, password):
#     f = 1
#     while (user.headers is None) & (f < 5):
#         logging.info('Attempt %s at capturing headers....', f)
#         browser = await launch({'headless': False, 'args': ['--no-sandbox', '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"']})
#         page = await browser.newPage()
#         await stealth(page)
#         # await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36")
#         await page.goto(url, options={'timeout':100000})
#         time.sleep(2)
#         selector = ".login-button--box"
#         await page.waitForSelector(selector)
#         await page.click(selector)
#         time.sleep(2)
#         selector = 'div[class="input huge"]'
#         await page.waitForSelector(selector)
#         await page.click(selector)
#         await page.keyboard.type(username)
#         selector = 'input[type="password"]'
#         await page.click(selector)
#         await page.keyboard.type(password)
#         selector = "#login-btn"
#         await page.setRequestInterception(True)
#         page.on('request', request_callback)
#         await page.click(selector)
#         time.sleep(60)
#         await browser.close()
#         f += 1
#     if user.headers is not None:
#         logging.info('Success!')
#         return user.headers
#     else:
#         logging.info('Failed to capture Southwest.com headers after 5 attempts -- exiting')
#         quit()


def check_for_price_drops(username, password, email, headers, cookies, account):
    southwest = Southwest(username, password, headers, cookies, account)
    for trip in southwest.get_upcoming_trips()['upcomingTripsPage']:
        # for flight in trip['_links']:
            passenger = trip['_links']['viewReservationViewPage']['query']
            record_locator = trip['confirmationNumber']
            logging.info('Processing: %s', record_locator)
            # try:
            cancellation_details = southwest.get_cancellation_details(record_locator, passenger['first-name'], passenger['last-name'])
            if cancellation_details['cancelRefundQuotePage']['tripTotals'][0]['currencyCode'] == "PTS":
                itinerary_price = cancellation_details['cancelRefundQuotePage']['pointsToCreditTotal']['amount'].replace(',', '')
                itinerary_price = int(float(itinerary_price)/len(cancellation_details['cancelRefundQuotePage']['passengers'])) # support multi-passenger itineraries
            elif cancellation_details['cancelRefundQuotePage']['tripTotals'][0]['currencyCode'] == "USD":
                itinerary_price = float(cancellation_details['cancelRefundQuotePage']['nonRefundableFunds']['amount']) + float(cancellation_details['cancelRefundQuotePage']['refundableFunds'] or 0)
                itinerary_price = round((itinerary_price / len(cancellation_details['cancelRefundQuotePage']['passengers'])))  # support multi-passenger itineraries
            # except:
            #     logging.info("Failed to determine price paid for fare. International iten's not supported")
            #     continue
            # Calculate total for all of the legs of the flight
            matching_flights_price = 0
            if cancellation_details['cancelRefundQuotePage']['tripTotals'][0]['currencyCode'] == "PTS":
                logging.info('itinerary original total price: %s points', itinerary_price)
                for origination_destination in cancellation_details['cancelRefundQuotePage']['cancelBounds']:
                    # departure_datetime = origination_destination['segments'][0]['departureDateTime'].split('.000')[0][:-3]
                    departure_date = origination_destination['departureDate']
                    departure_time = origination_destination['departureTime']
                    # arrival_datetime = origination_destination['segments'][-1]['arrivalDateTime'].split('.000')[0][:-3]
                    arrival_time = origination_destination['arrivalTime']

                    origin_airport = origination_destination['departureAirportCode']
                    destination_airport = origination_destination['arrivalAirportCode']
                    available = southwest.get_available_flights(
                        departure_date,
                        origin_airport,
                        destination_airport
                    )

                    # Find that the flight that matches the purchased flight
                    matching_flight = next(f for f in available['flightShoppingPage']['outboundPage']['cards'] if f['departureTime'] == departure_time and f['arrivalTime'] == arrival_time)
                    if matching_flight['fares'] is None:
                        logging.info('This flight is not available for comparison, possible reason: %s', matching_flight['reasonIfUnavailable'])
                        break
                    else:
                        for faretype,fare in enumerate(matching_flight['fares']):
                            # Check to make sure the flight isnt sold out to avoid NoneType object is not subscriptable error
                            if fare['price'] is None:
                                logging.info("fare type %d is sold out",faretype)
                                # if fare type is sold out, then use next rate for calculations, so let this for loop continue
                            elif fare['price'] is None and fare['fareDescription'] == 'Business Select':
                                logging.info("All fare buckets for this iten are sold out")
                                break
                            else:
                                matching_flight_price = locale.atoi(matching_flight['fares'][faretype]['price']['amount'])
                                # if fare type isn't sold out, then set the price and break out of the faretype loop.
                                matching_flights_price += matching_flight_price
                                break


            elif cancellation_details['cancelRefundQuotePage']['tripTotals'][0]['currencyCode'] == "USD":
                logging.info('Itinerary original total price: $%s', itinerary_price)
                for origination_destination in cancellation_details['cancelRefundQuotePage']['cancelBounds']:
                    # OLD SEARCH CODE
                    # departure_datetime = origination_destination['segments'][0]['departureDateTime'].split('.000')[0][:-3]
                    # departure_date = departure_datetime.split('T')[0]
                    # departure_time = departure_datetime.split('T')[1]
                    # arrival_datetime = origination_destination['segments'][-1]['arrivalDateTime'].split('.000')[0][:-3]
                    # arrival_time = arrival_datetime.split('T')[1]
                    #
                    # origin_airport = origination_destination['segments'][0]['originationAirportCode']
                    # destination_airport = origination_destination['segments'][-1]['destinationAirportCode']
                    # available = southwest.get_available_flights_dollars(
                    #     departure_date,
                    #     origin_airport,
                    #     destination_airport
                    # )
                    #departure_datetime = origination_destination['segments'][0]['departureDateTime'].split('.000')[0][:-3]
                    departure_date = origination_destination['departureDate']
                    departure_time = origination_destination['departureTime']
                    #arrival_datetime = origination_destination['segments'][-1]['arrivalDateTime'].split('.000')[0][:-3]
                    arrival_time = origination_destination['arrivalTime']

                    origin_airport = origination_destination['departureAirportCode']
                    destination_airport = origination_destination['arrivalAirportCode']
                    available = southwest.get_available_flights_dollars(
                        departure_date,
                        origin_airport,
                        destination_airport
                    )
                # Find that the flight that matches the purchased flight
                matching_flight = next(f for f in available['flightShoppingPage']['outboundPage']['cards'] if f['departureTime'] == departure_time and f['arrivalTime'] == arrival_time)
                if matching_flight['fares'] is None:
                    logging.info('This flight is not available for comparison, possible reason: %s',
                                 matching_flight['reasonIfUnavailable'])
                    break
                else:
                    for faretype, fare in enumerate(matching_flight['fares']):
                     # Check to make sure the flight isnt sold out to avoid NoneType object is not subscriptable error
                        if fare['price'] is None:
                            logging.info("fare type %d is sold out", faretype)
                        # if fare type is sold out, then use next rate for calculations, so let this for loop continue
                        elif fare['price'] is None and fare['fareDescription'] == 'Business Select':
                            logging.info("All fare buckets for this iten are sold out")
                            break
                        else:
                            matching_flight_price = locale.atoi(matching_flight['fares'][faretype]['price']['amount'])
                        # if fare type isn't sold out, then set the price and break out of the faretype loop.
                            matching_flights_price += matching_flight_price
                            break

            # Calculate refund details (current flight price - sum(current price of all legs), and print log message
            refund_amount = itinerary_price - matching_flights_price
            if matching_flights_price == 0:
                base_message='(unavailable) 0'
            else:
                base_message='Price drop of {}'.format(refund_amount) if refund_amount > 0 else 'Price increase of {}'.format(refund_amount * -1)
            message = '{base_message} {currency} detected for flight {record_locator} from {origin_airport} to {destination_airport} on {departure_date}'.format(
                base_message=base_message,
                refund_amount=refund_amount,
                record_locator=record_locator,
                origin_airport=origin_airport,
                destination_airport=destination_airport,
                departure_date=departure_date,
                currency=cancellation_details['cancelRefundQuotePage']['tripTotals'][0]['currencyCode']
            )
            logging.info(message)
            if matching_flights_price > 0 and refund_amount > 0:
                logging.info('Sending email for price drop')
                resp = requests.post(
                    'https://api.mailgun.net/v3/{}/messages'.format(settings.mailgun_domain),
                    auth=('api', settings.mailgun_api_key),
                    data={'from': 'Southwest Alerts <southwest-alerts@{}>'.format(settings.mailgun_domain),
                          'to': [email],
                          'subject': 'Southwest Price Drop Alert',
                          'text': message})
                assert resp.status_code == 200


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    mobile_url="https://mobile.southwest.com/"
    loop = asyncio.get_event_loop()
    for user in settings.users:
        user.headers = loop.run_until_complete(login_get_headers(mobile_url, user.username, user.password))
        check_for_price_drops(user.username, user.password, user.email, user.headers, user.cookies, user.account)
