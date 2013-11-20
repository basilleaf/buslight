import re
import urllib2
from secrets import SECRETS
import RPi.GPIO as GPIO
from time import sleep, mktime
from datetime import datetime

# blink behavior
start_time = 20  # max bus ETA to begin blinking, minutes
slow_blink_time = 10  # counting down from start_time, blink slow until this time
fast_blink_time = 2  # blink fast until this time, counting down from slow_blink_time
slow_blink_delay = 1.  # blink delay when the bus is bt 7-15 minutes away
fast_blink_delay = .3  # blink delay when the bus is < 7 minutes away

# LED pins
pin = 13
GPIO.setup(pin, GPIO.OUT)

# API setup
check_delay = 60  # how often to check the api
resource_url = 'http://services.my511.org/Transit2.0/GetNextDeparturesByStopCode.aspx'
token = SECRETS['api_token']  # get one here: http://511.org/developer-resources_api-security-token_rtt.asp
stop_code = SECRETS['stop_code']  # see http://www.nextbus.com/wirelessConfig/stopNumbers.jsp?a=actransit
consecutive_fails = 0  # keep track of API fails
max_tries = 10  # max tries

# begin
url = '%s?token=%s&stopcode=%s' % (resource_url, token, stop_code)
last_check = mktime(datetime.now().timetuple()) - check_delay
while True:

    # see if we need to check the api again
    t_now = mktime(datetime.now().timetuple())
    if t_now > (last_check + check_delay - 5):  # making sure it triggers the first time
        # it's been > check_delay seconds since we checked the api, go for it:
        last_check = t_now
        page = urllib2.urlopen(url).read()
        m = re.compile('<DepartureTime>(.*?)</DepartureTime>', re.DOTALL).search(page)
        try:
            minutes = m.group(1)  # too lazy for xml futzing
        except AttributeError:
            # no departure time, likely API call failed, move along..
            consecutive_fails += 1
            if consecutive_fails > max_tries:
                print "API fail, exceeded max tries"
                import sys
                sys.exit()
            sleep(15)  # let em rest then try again
            continue

    # blink an LED or turn it off
    if slow_blink_time <= int(minutes) <= start_time:
        # bus is approaching in a few minutes, blink slow
        GPIO.output(pin, True)
        sleep(slow_blink_delay)
        GPIO.output(pin, False)
        sleep(slow_blink_delay)

    elif fast_blink_time <= int(minutes) <= slow_blink_time:
        # bus is iminent, blink fast
        GPIO.output(pin, True)
        sleep(fast_blink_delay)
        GPIO.output(pin, False)
        sleep(fast_blink_delay)

    else:
        # bus is gone, turn LED off
        GPIO.output(pin, False)
        sleep(check_delay)  # when there is no bus we can sleep between loops

