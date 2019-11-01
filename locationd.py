#!/usr/bin/env python3

################################################################################
#
# Service to accumulate gps and imu data from BerryGPS/IMU and make it easily available
# Service control file for user service at /usr/lib/systemd/user/locationd.service
# NOTE: changed from user to system service and moved control file to /etc/systemd/system/locationd.service
# Article on develping Python services: https://github.com/torfsen/python-systemd-tutorial
# Additional functionality:
#    When GPS state transitions to 2 or 3 and system time has not been set since service started:
#        Check to see if system time is more than 5 seconds different than GPS time.
#        If time differs, et system time
# Van Kichline, September 2019
# October:
#    Adding planetary almanac, initially for Sun and Moon
#    Functionality is astro.py module
#
# Names of the GpsState properties:
#    mode(int), time(str), lat(float deg), lon(float deg), alt(int M), speed(float M/s), climb(float deg)
#    persistance_version is added when writing to cache

import time, signal, threading, json, datetime, os, math, astro, TimeCalc, DayCalc
from gps import *

CACHE_FILE_NAME     = '/var/cache/locationd/locationd.cache'
PERSISTENCE_VER     = 4             # Version of persistence file. If versions don't match, file is ignored.
HOST                = '127.0.0.1'   # for this machine only
PORT                = 9999          # Arbitrary non-privileged port
MAX_TIME_DIFFERENCE = 10            # Max # seconds GPS can differ from system time
ALMANAC_ROUNDING    = 3             # How many places to round almanac values to


################################################################################
#
# This class runs a thread that acquires the latest data from gpsd.
# To begin acuiring data, run:
#    gpsp = GpsPoller()
#    gpsp.start()
# To acquire the dictionary of current TVP values, call:
#    gpsp.value()
# To shut down the poller, call:
#    gpsd.join()
#
class GpsPoller(threading.Thread):

    def __init__(self):
        self._stopevent = threading.Event() # Used to shut down the poller
        self.current_value = {}
        self.system_time_has_been_set = False
        self.session = None
        try:
            threading.Thread.__init__(self)
            self.session = gps(mode=WATCH_ENABLE)
            self.watching = True
            print('GPS monitoring started.')
        except:
            self.watching = False
            print('Failed to open GPS stream. Falling back on cached values.')

    def value(self):
        return self.current_value

    def run(self):
        while self.watching and not self._stopevent.isSet():
            try:
                report = self.session.next()
                if report['class'] == 'TPV':
                    self.current_value = self.session.next()
                    #print(self.current_value)
                    if not self.system_time_has_been_set:
                        self.check_set_system_time(report)
            except:
                print('Error reading gpsd data.')
            time.sleep(0.2) # tune this, you might not get values that quickly

    def check_set_system_time(self, report):
        if report['mode'] >= 2:
            self.system_time_has_been_set = True
            rep_time = datetime.datetime.strptime(report['time'], '%Y-%m-%dT%H:%M:%S.%f%z')
            sys_time = datetime.datetime.now(datetime.timezone.utc)
            time_diff = abs((sys_time - rep_time).total_seconds())
            if time_diff > MAX_TIME_DIFFERENCE:
                print('Sys time = %s' % (sys_time))
                print('GSP time = %s' % (rep_time))
                print('System time differes from GPS time by %i seconds. Updating.' % (int(time_diff)))
                try:
                    os.system('date -s ' + report['time'])
                except:
                    print('Failed to set system time.')

    def join(self, timeout=None):
        self._stopevent.set()
        time.sleep(0.5) # Time for current operation to end
        if self.session is not None:
            self.session.close()
        threading.Thread.join(self, timeout)


gpsp            = GpsPoller()
state           = {'mode':0, 'time':'?', 'lat':0.0, 'lon':0.0, 'alt':0, 'speed':0.0, 'climb':0.0 }


# Handle SIGTERM signal
def signal_term_handler(signal, frame):
    shutdown()
signal.signal(signal.SIGTERM, signal_term_handler)


# Save the current global state values to a cache value for quick startup
# The persistance format is lines of Property=Value pairs.
def persist_state():
    global state

    state['persistance_version'] = PERSISTENCE_VER
    cache = open(CACHE_FILE_NAME, 'w')
    cache.write(json.dumps(state, sort_keys=False, indent=4, separators=(',', ': ')))
    cache.close()
    del state['persistance_version']


# Load the saved state into the global state object
def load_state():
    global state

    state['mode'] = 0
    try:
        with open(CACHE_FILE_NAME, 'r') as cache:
            content = cache.read()
        loaded_state = json.loads(content)
        if loaded_state['persistance_version'] != PERSISTENCE_VER:
            print('Cache file wrong version, ignoring.')
            return
        state = loaded_state
        del state['persistance_version']
        state['mode'] = -1
        print('Cache loaded.')
    except IOError:
        print('Error reading cache file.')
    except:
        print('Error loading cache file.')


# Termination routine
def shutdown():
    persist_state()
    gpsp.join() # Shuts down poller
    exit(0)


# Get the current gps data and create a json string fron it.
def get_json():
    global state
    report = gpsp.value()

    # if mode is zero or 1, there is no fix. Do not replace -1 (from cache) unless there is a fix
    val = getattr(report,'mode',0)
    if state['mode'] == -1:
        if 'n/a' != val and int(val) > 1: state['mode'] = int(val)
    else:
        if 'n/a' != val: state['mode'] = int(val)

    state['time']  = getattr(report,'time',state['time'])
    state['lat']   = getattr(report,'lat',state['lat'])
    state['lon']   = getattr(report,'lon',state['lon'])
    state['alt']   = getattr(report,'alt',state['alt'])
    state['speed'] = getattr(report,'speed',state['speed'])
    state['climb'] = getattr(report,'climb',state['climb'])
    return json.dumps(state)


def get_day_info():
    di = DayCalc.DayCalc(state['lat'], state['lon'], state['alt'])
    return di.as_json()


# Return JSON representing TimeCalc info
def get_time_info():
    tcalc = TimeCalc.TimeCalc(state['lat'], state['lon'])
    result             = {}
    result['utc']      = tcalc.getUtcTime().strftime('%H:%M:%S')
    result['local']    = tcalc.getLocalTime().strftime('%H:%M:%S')
    result['solar']    = tcalc.getSolarTime().strftime('%H:%M:%S')
    result['timezone'] = tcalc.getTimeZoneName()
    result['jdate']    = tcalc.getJDate()
    result['gmst']     = tcalc.decimalHoursToHMS(tcalc.getGMST())
    result['lmst']     = tcalc.decimalHoursToHMS(tcalc.getLMST())
    result['doy']      = tcalc.getDOY(tcalc.getLocalTime())
    strResult          = json.dumps(result)
    print('Result: %s' % (strResult))
    return strResult


# Return an almanac json blob for the body requested
def get_almanac(body_name):
    print('Generating almanac for %s' % (body_name))
    result = {}
    target = astro.body_from_name(body_name)
    if target is None:
        return'{"error": "name"}'
    obsv   = astro.loc_from_data(state['lat'], state['lon'], state['alt'])
    # Use default system time; locationd has done its best to set it correctly
    name, alt, azm, dist, illum = astro.info(target, obsv, True)
    
    result['name'] = name
    result['alt']  = round(alt,  ALMANAC_ROUNDING)
    result['azm']  = round(azm,  ALMANAC_ROUNDING)
    result['dist'] = round(dist, ALMANAC_ROUNDING)
    if illum is not None:
        result['illum'] = round(illum, ALMANAC_ROUNDING)
    strResult = json.dumps(result)
    print('Result: %s' % (strResult))
    return strResult


# Never return: wait for socket connections
def socket_server():
    print('Starting socket server.')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('socket created.')
    #Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
        print('Socket bound to port %s on host %s.' % (PORT, HOST))
    except socket.error as msg:
        print('Bind failed. Error Code : %s, Message: %s' & (str(msg[0]), str(msg[1])))
        sys.exit()
    except Exception as e:
        print('Unknown exception:')
        print(e)
        print('Continuing...')
    #Start listening on socket
    s.listen(10)
    print('Socket now listening')

    #now keep talking with the client
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        data = conn.recv(16)
        msg = data.decode()
        print("Server received: '%s' from %s:%s" % (msg, addr[0], str(addr[1])))
        if 'gps' == msg:
            reply = get_json()
        elif 'time' == msg:
            reply = get_time_info()
        elif 'day' == msg:
            reply = get_day_info()
        elif msg in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']:
            reply = get_almanac(msg)
        else:
            print('Error: unexpected selector in socket msg: %s' % (msg))
            reply = '{"error":"' + msg + '"}'
        conn.sendall(reply.encode())
        conn.close()
    s.close()


if __name__ == '__main__':
    load_state()
    gpsp.start()
    print('gpsd started.')
    try:
        while True:
            socket_server()
    except:
        shutdown()
