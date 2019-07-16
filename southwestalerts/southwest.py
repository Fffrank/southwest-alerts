import json
import time

import requests

API_KEY = 'l7xx0a43088fe6254712b10787646d1b298e'  # TODO: Retrieve this from https://mobile.southwest.com/js/config.js
BASE_URL = 'https://mobile.southwest.com'


class Southwest(object):
    def __init__(self, username, password):
        self._session = _SouthwestSession(username, password)

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


class _SouthwestSession():
    def __init__(self, username, password):
        self._session = requests.Session()
        self._login(username, password)

    def _login(self, username, password):
        data = self.post('/api/customer/v1/accounts/login', payload={
            'accountNumberOrUserName': username,
            'password': password
        })
        self.account_number = data['accessTokenDetails']['accountNumber']
        self.access_token = data['accessToken']

    def get(self, path, success_codes=[200]):
        resp = self._session.get(self._get_url(path), headers=self._get_headers())
        return self._parsed_response(resp, success_codes=success_codes)

    def post(self, path, payload, success_codes=[200]):
        resp = self._session.post(self._get_url(path), data=json.dumps(payload), headers=self._get_headers())
        return self._parsed_response(resp, success_codes=success_codes)

    @staticmethod
    def _get_url(path):
        return '{}{}'.format(BASE_URL, path)

    def _get_headers(self):
        return {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/vnd.swacorp.com.accounts.login-v1.0+json',
            'x-5ku220jw-b': "-fwo40b",
            'x-5ku220jw-c': "A2kfcPxrAQAAOQVScgNrPWMcEUNqMvpep3AUTuXsFaHt7mNPTCT6RUd6yD2oAawUHfH6K-8VwH8AAOfvAAAAAA==",
            'x-5ku220jw-a': "wsdkWyzlfzIBA9fkFCHcnmfrxuIiUCW01qIm6CIJLbR9KpFA3Mkk5G4=tZ2nK-H=AzM=uJm=bU7n7kfnW7IlfeuZU9nzkR8mQ7pdAy6odPftxkcArO7HrEcExec=vqnnWyl-kfN01xn57u8LaJSz1ecoxmftkEumAW79beui7Uem9pIlIano7ZMd7dGqFtm=1jI3ksyXgzklVB4L7-Nk1-u2A3bXbTIPY95Ab80f79rtaZxvAaAE93gLfett-LG3zzd0EyU31B5THEtlUgXh1T5TaB40bUrSfKX=Iyu8IFb29Zgqn2uq7OW01QI8HkYTjv4fFOktxzALuvYl9mkAQA-zKCtTCeum1TmAN4zKrmSnxLB9kme=7AdeAUIS4U4AnydzFtYqwysA1Pfn1CucIAI3b80O=gcl6CU=6TEykAs-bs=Twytn1_pOw-e3txVLFannriHlvAIPzzalw8kA-PpEFUbEnMQHIyWSQy5TYCU=atK--7MMA8czAqv4uiABkZIofmfn5TaK9Kp3=zA9E3dSUSfE-yu890An5CgTjy9kzzWR4BnMatm=F7Y09LmA9z5pb3x-kqu31mm3efNFnek5necRQ-fnkeco14k9kVxm5=aiYCzz4xul1BIl7qYhWy-qb6An7OankOmdk6zEfAc8u0nWG-ArAM7z77I8fsGi77d7zbI277znvOdiAUBZGUFT1ecE1n2t7M806lAtW-Hq7xI83MuXWyIM1C=oUS6VTPP3kM43Hub01xY3AwpEfss5b7M3K8cnbCTW4Mf=QdG2atKaFiy047fm7In0A8tl4AdSYAH3ACYmA4fB9UILUBo_bSfd7tzzxzW83ydn7BY314p8gZ7r6euZaLAmFtRqby3R65UZtsHTNUI7PlGqXF5=mEtAaZ6HbZ6AktdqNvY3aCzsUBne9nbqlz_-eO9Exe0T7HNl19ztNnnOYl9_NzYS1BKXH4u83IX25x43aiccxM4dxzsmotnn1MI3AQI=NubyA7m=LLAEUsSnUW4=KFpXnm7_aa7AaS4OdM-t79z0FSnluB3nWMfL1Iy17lnvaOzCw-doNM7mb2Mw6xe=fecL0ItTA7dAkzAmkfuib7e=tZYnFtm3FS=lYzdRUSzWgBfplZHJevYl9sIMkmmTksGcW4zn7PpmcyuS171fk7zFA4MTF8tK7QsrFZWdEEI3bimHrzdlF7adFSznkFnE7VAAFCYYuOH=kz0A7m8OALGAWyS9NAzH1qM=I7pJ9TnkNmpOacHSFVmTNA7n7-dmFXnAIypXAU4z1eu3fzHdxMm4fknq7CY9Fy69w-MLbamZ7VgAR41Tak6A1SfnVAzwfs7e9PNA-Szyk7zlF75BbUAlk3knNXGTxsj=NnMd=MYc1PeAk3N9A8ezaSHg1yH7iCW8nMY2_MOtyeHnYlmvn8eTaXg3SvuczZOnLM4z94ze6W0=A7MKAe6qQa3rvzYTAMyXbY03wekAWyYmkZY36SM=baffWUuu19Iq-Bul-YdqFUKO3Zk9k0K96ge=fubqAQY5aCgWkZlSA8c3=Buc1mfn7ykLNsUOW1ccTtmTWbIrJ-znb3knAamm7-aPAYGST77nA4noAnaH9sY3AyY8qtG4a0dVJiGZ6gtAtzYTyMpZyyd0xeciuMI3kOAA6T4=724Os-noYBI3I7AH1Tkt3zucnsgTn-nRGLnON0N05HGcAU4=1BuSbArn7C1Katdm7_So7r57c-ndkCu3fmn7o-u5UCbS7AIExetlxeETkE4tAyHeb71SQFpSxAndb0YAazWW7gtAQZ=AaAAnx7In1Ec91LZ7AZPT-sU0Ise57xYlaZg=F7M3nAsXneX7Yy-H4ee=xz3q6C9zaqYO9vYAdBI8-stzTdImQvYrxmflaSmOqv7llZ9Afk4=Q7-TcaAIaLoAaCgtf9fWA7dqYzvsAa5TE4poM2ncWsFT1Ya9IyGT-Tzlixyjte03Kv7nWVg=d7zr-s2H6Bcc6TdM7wf=kAM3ag6lv0nL1lnAky=mkMc-aOztaaWvW7M=9tj=kUnTbLc8xAdlI7zTA48L6iNdAa_guEAlk2n216IFk0GSj8c3NmznbguRAsc3sstnr-HBxn03=6nL=mm9hS3faSAAAMITfMRqQ4dnVCGPUiIWUC=z=gtnxk-Txs==1sU31TdmkzY37Adigee=tAVOA-dPA740mAdlASecb8m3xe0zEtznl7MZAH1=fMAnN7IM9v-Tkx-Vk0d3xzfzUBVAL4NEAb43-Ec=aZGJbZiqAYIMQBHE6CbCklL-wNVP98boxAdois38W-QeaE0g7cHTI9dZUlSqU6urbAL=NFP0==eAre0caZiVIy-zAOMP1NhTnsulKMpv=im3TU0=6iks4i4O1TAl7meLr2j31TzBA-8uME03N4Wl-UAA_qudF3GaKV5z5xk9kUY76tmi4BUAxmm96BpO5Tdec4-9nN03km5T7sdlw8cobVtlNuAnvta0FycUWec2kYGdYkFtztN-vSe=bE0=SPI-4LWAb7N3rP4AEYa7AbCAxexX4gm=nUuWUBIXFgcdAhu213gmtYgS4E0mk0dMIqFtM4nSY9ocbA7Hl=o3-tz-fsHc66nn9p4PtqYS7Y6AkmAqaxIia62y-2OmFYGOVd0AQs=rn7U=bsY-p0n_N-3SaAn4w8OnWU7nI4Fb3AmANmzH=TM=wyM=NsiAAZdP3zkn5SH3QMpC1UttbO85nqYhaktnQfboQKpEk7uE49dE9Lanu8uSkMWdAPbENsGindW39dAauXABkiAAe7dLz8u7tdKF5ST3A7s0Aq-n9MfH4A4GA4z9Ket9kFtPxsGoa_Szbam3xAn9k0dS9csFaXnL4spLtW5AkqeFUgu889dLt36AzIco59zEdnnTaCi3b7do59MObgknWs=Skygz7Op9N6nk1g3q-MIcNM7HuZIqH6tn78tnFtzo7y_--m53aetduMp-FSd37iktAUuTkzOnaWR23AHdkaAnATYEnMNZ-sc8kZB=6innnsHlALgCfsklz64=kEucr3uEqAGmLq-6rZjqAy3l16MEFOgAnOLvYlLXxzdo4Em=163Xkncilmun9M7nmOI3kxul1OeAFy539dklc4tlbQknk0K57-am4CWVuBb-kmYFbvYO=eud1a6q52p7W8ucqabqUlm69sM3Aw5=fMRL1TKnFyzI7SksjSYl7gt9NH-lxAznaPnoIVjTkt-RA8ti5sGeaAdr1Bk9uLg=FCGAfk69kO69FVWA59dStecPaTnckZT=aBpkYOWRV6PO1ydlwmzqa3al0AX-UCy-uotnNsS9fzz9AE0tu4pqUC4TnLe=79piAM=L-lGnAyGLnsWlIYz_xkMT=T4TwEtlA7I3FyilWazHYL=nS7AnWmh3cs4LkMftm3TTA-CTvzpAHpVVQOLXHyi8Fy-AY7d3wMuUAzdS=BOfIyd8Vxzj4_5Tfe03aBIob7tlneOCH80d6ST=xyW3uecCwU7nuQ-BwytnI6AzW7I45Pe76SHF4WceFyu39sdcatdSxAWW7M4THe0TFi7zUgumg2Y8AFmt7QUpA8tt4ecX7zuO5T=la0tBfstnNIUs4Z13fk=taP4Ofm7eU=nSne0=_tT5SsWXA-d=3sU=5ih=xmpcalnqxApibyYeFyNnAOGmbUWvYTAnxKm0F-RSbyHOzze=FXc8A7dz7yG84J5AW8tTAsaAFUVXWVLznmAt9zeU7tcc=xU3AsHd7Vck1mKt9ub3AYuAfLP3A7m9xAz=UxklQUpVkstnfAYlby7EkVnokz6zIJfHkRIei9M36BE0bdhuAqIC76-AfvY9L743y2ATUC7=bzrtFqU==S=GAU3mH8k96lAt7Cjuk77tN4m5bAAeUBpou7zz1xY8nMy9xAnRW-znRQB3fsY7I9pqWAnAN-n3QAHnA4fHUBpnNVSzn4dS3k5t78=Se4ACxzzdt6n2ABI3xMu0S8cj9z-HbG4=nkuAfzm=Iy8cxsiMbbET9Ek9w4sf9knB=9fznkNoYCHF1Oed4ZIMkM9nAYL=7tr_7zfL-gcmkqUnb-=9kQUg4ZYok6NCxSdVAQYOaC=79m4=bM7z7-G5b0nm480ddRaA6ju3HOndkUpnkE3n49dnaHn8IAfEbdNn6CYBYy53tO6HAYdOsKpRwV6Lne00kpbc4BIJSyznFNOn5jnc7aoT0YFEFYGSkyWm4CWUwBe0Ucdq57W3xsU3WUU=nyRma=9VxvISkypm6uAn2EXiAyFnkdgZ3mnEfmfTHyU9-XAmLZ5AIgvMAUOzuCdAkv131iNk2gtu1CIeU9ddAaYBnA4=TAnlAkYdFVG2bak9azHAWyziAgc=-oImA-NMk0m=gPM4I-fzAYVp7CeA1tdcI9zEyA7l59Ic4zvy197Axe0=HBf0kXG_rZ30b34Tv7dT69rHbydcnAni_PfB=Od3WyYEtARn3zGl4Jp81PIYFxM=asY3NI0=N8tiOPtnxzrnWkuokCclxzeZI9z94A4TnM-nNy-z12noYCboW8tt6SRi5Si-yWIANmnApZBsA-ucGhfpr-L3nMVXnA33rZ3LBJ5=c6P0xsUW-et9YeuE3d6p3eu59m43vgXA7CM3A4AB3tAA7Z-laPm=FQU=ys9TaS6LN-A97OdA7CHmHyjOA4pSQTmOAYxL1PISb7Ock7zlkAnc9cYR67MTkE8yWtd8aOd9Ns-97BISHaW2Y9IoAY-q4-AR6lPTnEtE4s-A1ZdTWzfq1qUu9dala1HrAXAtnEXLxLniW-WS9PN83MIhxvYla0dm5ZG07yuUkAzd1S9YuRil7Se3bUVtFCgAH7M3xAdl1s5AxAeT-VnkkTu=FZ7zQ4c39n1Lfz=lAsOAAyRc7sNcb49nA8c0AdG3kA9AK7=lkQYO1BuE9ypR6SNFAYzHAa7lxAkWks-A1dn0QM4_4AIcmYu7AC=ta0p77xNoNn=z1MkEbAN9FydEfMf9NM8=xMn8-z3nfAdMxmfLuS2n5tOzkOp3kPknLZ7l7U71oEtzkAv-Wb3vxzPUnAdS8AtHF7cc4BpeAyj=EEuEw7d3W81dxkYdxMc0adG75AdMxSGd70kt7-X-bUplAEcE1ysuUC6yLzpdnkRR9kAfYMf7ZNPAAMu3Gtn716m97COLKk5=aMe=fAIdgg0=wFpSW-H3KCYE9-zzFZGcKUn8Qs-z7Etn-dILL0cEzzR84Sp8YZUTa6nlAL6eRXt9BMr7QSe=Iyc=wUInoA2KAZdmfAmyAYGdV9dnLc059x9n-XOHxMO9WYKxUg0=kOLO16mTY9fl3s2l7yB3fsuZ7T8TxsfmYabSiAzznVnEF9-KNSd3FO9nfvY0ndpoHi4TxsBswCWlzzok-A5A6imOw4cAfzuAas3Mb4fub8c39uNm1sI4Ay8AFZftxzdZ1CyXTEuOWyY2kP7n-A7AxAkz1yieA8coOznIAY2zadM=18tLktIQ9moOF80A7SzraZFH1sWM9sF9wy7L1kFlWqYX6TRAkIAtNdnAk-N=k6tikZdqbBI-FEu8nsbpusMT=E0=w-A91afTxzNA=mAlrXcEA7IWBUpvA80=W8kOI4n0Yz5=bVnlfzeAaLAzaT2qbVeIb-p3xmMCxv-L7zzrfdUO6mnkUHSLNNYqwikzaJT0As5z1ZkumxYlWyG4m9doFSft7e0=HEtzt-ftA7m3KVnYHZP=aMITatU=bYN0uA7K6U7CsyYitxu3AsYYSl6z1Tpc1P5=4ze=vUVXuLb9fL8TbaA9BXAnFS=lK--U9MoMT4At1EudAXjAFTAEAfT=1mYqXJoPIyZ7zydMYEuC4TEsaLA9fAztW7dTWZk9bg0SWUYT9siA7Ya9WBIi1auLfv-d6LnOA48=A7JA7tmTbeeQAyHcW4AB9mdmA8ulAVnvApI8IU3nRdFAMdAlxzd-YCTdkzpEALj7iXndVLnTfAIR1PYnkMIc1t7L4LP=asc2QPpUnU0LxMY86B7nkzdmxMe=IydigLAPARWE1kTT-_fl6i6TN6LXH6piAaNOF-EANm30-2RA14OR_3YiaBflkVn3WFtnALnMLdp2xfNck0ftb7ien9MnfLciaC-znu2irEu2uvU=7yYqHOAL9eznYs-zkXWqQt4zkmfZb8cn9HN3UBAznKWS1Q-Afzvf5G50LAIn6CNL-zuSbyG5fH7Bxzfxw4n-EA7Cuu0=kPAl4mp2Nekn16e=LAdYfmnO=yIv3Munasu3-LGlUcIruZiTFVHmxQn96gu-AAmYwUe0IxYdxec4fknlIgkC9ZNuV86l7LI2-0icbUY39MpS7AdOAtGEudYrgBpC9ZxuAzdYkEefaZdm9bcl7lW3u2fl2EM0wz806ig-AyuLNUIdUS94FbIexMAlfsWMAuonNYpobk3EfLtALCYUAUIE19knK-SvkanSfM5Jfs8=5ZbE7ydZtqd8uy6fkOmT1mcaYBIZ5TpSWzdWksd3ATzzlZuqYmAAI6n3bUe3XykzlnoPfspW3sYckecl=6ki5tpF9zn8fAdL-EcLCVL-49k94AI3ueb4PrnAxLA93AdXWNplUC-9n0Wr1x4TYianY5uckZg=7AnraZOCb-mA66AzbVndA7pSCze3Aajk1S39rltnatmVYCdufs6EktISWUI3iSaAAvb3b803GtzA8s6txM4310dl4_FLFZSnUlm35Zd-1Zj=U_ph1gtjU9dR90dmLLGA4yIE9iGS9zAl9sOm1-94W4nA1UI7-C6nW4YSLsW9w8klICUATyY7cB3pyA",
            'x-channel-id': "MWEB",
            'x-5ku220jw-uniquestatekey': "A1cwcPxrAQAAYQWte2_wVfwTBUP7hQqLXkyHzD2VJYbsH5S22gHYc4rsUtbQAawUHfGucsmZwH8AABszAAAAAA==",
            'x-5ku220jw-d': "0",
            'User-Agent': None, 'Connection': None, 'Accept-Encoding': None,
            'token': self.access_token if hasattr(self, 'access_token') else None
        }

    @staticmethod
    def _parsed_response(response, success_codes=[200]):
        if response.status_code not in success_codes:
            print(response.text)
            raise Exception(
                'Invalid status code received. Expected {}. Received {}.'.format(success_codes, response.status_code))
        return response.json()
