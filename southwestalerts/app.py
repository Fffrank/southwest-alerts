import locale
import time
locale.resetlocale()
#locale.setlocale(locale.LC_ALL, '')
import logging
import requests
import sys
import asyncio

from pyppeteer import launch
from pyppeteer.network_manager import Request

from southwestalerts.southwest import Southwest
from southwestalerts import settings


async def get_page(browser, url):
    page = await browser.newPage()
    await page.goto(url)
    return page

async def request_callback(request: Request):
    # Prints: {'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/69.0.3494.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
    if request.url == "https://mobile.southwest.com/api/security/v3/security/authorize":
        user.headers = request.headers
        await request.continue_()
    else:
        await request.continue_()


async def login_get_headers(url, username, password):
    browser = await launch({'headless': True, 'args': ['--no-sandbox', '--user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36"']})
    page = await browser.newPage()
    # await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36")
    await page.goto(url)
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
    await page.click(selector)
    user.cookies = await page.cookies()
    await browser.close()
    return user.headers

# async def login_get_headers(url, username, password):
#     f = 1
#     while (user.headers is None) & (f < 5):
#         logging.info('Attempt %s at capturing headers....', f)
#         browser = await launch({'headless': False, 'args': ['--no-sandbox', '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"']})
#         page = await browser.newPage()
#         # await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3494.0 Safari/537.36")
#         await page.goto(url)
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




def check_for_price_drops(username, password, email, headers, cookies):
    southwest = Southwest(username, password, headers, cookies)
    for trip in southwest.get_upcoming_trips()['trips']:
        for flight in trip['flights']:
            passenger = flight['passengers'][0]
            record_locator = flight['recordLocator']
            logging.info('Processing: %s', record_locator)
            # try:
            cancellation_details = southwest.get_cancellation_details(record_locator, passenger['firstName'], passenger['lastName'])
            if cancellation_details['currencyType'] == "Points":
                itinerary_price = cancellation_details['pointsRefund']['amountPoints']
                itinerary_price = int(itinerary_price/len(cancellation_details['passengers'])) # support multi-passenger itineraries
            elif cancellation_details['currencyType'] == "Dollars":
                itinerary_price = ((cancellation_details['availableFunds']['nonrefundableAmountCents'] + cancellation_details['availableFunds']['refundableAmountCents'])/100)
                itinerary_price = round((itinerary_price / len(cancellation_details['passengers'])))  # support multi-passenger itineraries
            # except:
            #     logging.info("Failed to determine price paid for fare. International iten's not supported")
            #     continue
            # Calculate total for all of the legs of the flight
            matching_flights_price = 0
            if cancellation_details['currencyType'] == "Points":
                logging.info('itinerary original total price: %s', itinerary_price)
                for origination_destination in cancellation_details['itinerary']['originationDestinations']:
                    departure_datetime = origination_destination['segments'][0]['departureDateTime'].split('.000')[0][:-3]
                    departure_date = departure_datetime.split('T')[0]
                    departure_time = departure_datetime.split('T')[1]
                    arrival_datetime = origination_destination['segments'][-1]['arrivalDateTime'].split('.000')[0][:-3]
                    arrival_time = arrival_datetime.split('T')[1]

                    origin_airport = origination_destination['segments'][0]['originationAirportCode']
                    destination_airport = origination_destination['segments'][-1]['destinationAirportCode']
                    available = southwest.get_available_flights(
                        departure_date,
                        origin_airport,
                        destination_airport
                    )

                    #Find that the flight that matches the purchased flight
                    matching_flight = next(f for f in available['flightShoppingPage']['outboundPage']['cards'] if f['departureTime'] == departure_time and f['arrivalTime'] == arrival_time)
                    if matching_flight['fares'] is None:
                        logging.info('This flight is not available for comparison, possible reason: %s', matching_flight['reasonIfUnavailable'])
                        break
                    else:
                        for faretype,fare in enumerate(matching_flight['fares']):
                            # Check to make sure the flight isnt sold out to avoid NoneType object is not subscriptable error
                            if fare['price'] is None:
                                logging.info("fare type %d is sold out",faretype)
                                #if fare type is sold out, then use next rate for calculations, so let this for loop continue
                            elif fare['price'] is None and fare['fareDescription'] == 'Business Select':
                                logging.info("All fare buckets for this iten are sold out")
                                break
                            else:
                                matching_flight_price = locale.atoi(matching_flight['fares'][faretype]['price']['amount'])
                                #if fare type isn't sold out, then set the price and break out of the faretype loop.
                                matching_flights_price += matching_flight_price
                                break


            elif cancellation_details['currencyType'] == "Dollars":
                logging.info('itinerary original total price: $%s', itinerary_price)
                for origination_destination in cancellation_details['itinerary']['originationDestinations']:
                    departure_datetime = origination_destination['segments'][0]['departureDateTime'].split('.000')[0][:-3]
                    departure_date = departure_datetime.split('T')[0]
                    departure_time = departure_datetime.split('T')[1]
                    arrival_datetime = origination_destination['segments'][-1]['arrivalDateTime'].split('.000')[0][:-3]
                    arrival_time = arrival_datetime.split('T')[1]

                    origin_airport = origination_destination['segments'][0]['originationAirportCode']
                    destination_airport = origination_destination['segments'][-1]['destinationAirportCode']
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
                currency=cancellation_details['currencyType']
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
        check_for_price_drops(user.username, user.password, user.email, user.headers, user.cookies)
