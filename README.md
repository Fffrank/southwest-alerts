Updated script from https://github.com/xur17/southwest-alerts

This now uses chromium to pull the required headers and login to the southwest site to scan for price changes.

# Details

This is an application that can be used to monitor booked southwest flights for
price changes. It logs into the accounts credentials are proided for, and
checks to see if rebooking the flight would result in a lower price. If a lower
price is available it will email you via the mailgun api. It will not
automatically rebook the flight for you. You will need to create a free mailgun
account to be able to receive the email notifications.

# Setup

## Option 1 - Run via Docker (recommended)

1. Install docker
   ([ubuntu](https://docs.docker.com/engine/installation/linux/ubuntu/#install-using-the-repository),
[windows](https://docs.docker.com/docker-for-windows/install/),
[osx](https://docs.docker.com/docker-for-mac/install/))

2. Create mailgun account

Setup a [mailgun account](https://www.mailgun.com/), and create an [api
key](https://app.mailgun.com/app/account/security). Use the default mailgun
domain (username.mailgun.org), or create a new one for the next step.

3. Run docker image (replacing everything on the right side of the equal sign with your values). You can add additional username#, password#, email# values as needed for additional southwest accounts.

```
docker run -e MAILGUN_DOMAIN=??? -e MAILGUN_API_KEY=??? -e USERNAME1=SOUTHWEST_USERNAME -e PASSWORD1=SOUTHWEST_PASSWORD -e EMAIL1=NOTIFICATION_EMAIL fffrank/southwest-alerts
```

## Option 2 - Run natively

1. Pull repository

```
git clone fffrank/southwest-alerts
cd southwest-alerts
```

2. Install dependencies

```
pip3 install -r requirements.txt
```

3. Set environment variables (replacing value with the appropriate value)

```
export MAILGUN_DOMAIN=VALUE
export MAILGUN_API_KEY=VALUE
export USERNAME1=VALUE
export PASSWORD1=VALUE
export EMAIL1=VALUE
```

4. Run

```
python southwestalerts/app.py
```

#Windows  Users
You may need to change the locale settings in app.py -- comment out the first line and uncomment the second.
```
#locale.resetlocale()
locale.setlocale(locale.LC_ALL, '')
```