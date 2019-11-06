#!/usr/bin/env python3

################################################################################
#
#    Service to accumulate gps and imu data from BerryGPS/IMU and make it easily available
#    Service control file for user service at /usr/lib/systemd/user/locationd.service
#    NOTE: changed from user to system service and moved control file to /etc/systemd/system/locationd.service
#    Article on develping Python services: https://github.com/torfsen/python-systemd-tutorial
#    Additional functionality:
#        When GPS state transitions to 2 or 3 and system time has not been set since service started:
#            Check to see if system time is more than 5 seconds different than GPS time.
#            If time differs, et system time
#    Van Kichline, September 2019
#    October:
#        Adding planetary almanac, initially for Sun and Moon
#        Functionality is astro.py module
#
#    Names of the GpsState properties:
#        mode(int), time(str), lat(float deg), lon(float deg), alt(int M), speed(float M/s), climb(float deg)
#        persistance_version is added when writing to cache
#
################################################################################

# Load the settings dictionary and access settings as: cfg.get['KEY']
import configuration as cfg
import time, signal, threading, json, datetime, os, socket, sys, math, logging, astro, DayCalc

logging.basicConfig(format='%(levelname)s:%(message)s', level=cfg.locationd['LOGGING_LEVEL'])
logging.info('Configuration file loaded. Logging level: %s', cfg.locationd['LOGGING_LEVEL'])

PERSISTENCE_VER     = 4  # Version of persistence file. If versions don't match, file is ignored.
CACHE_FILE_NAME     = cfg.locationd['CACHE_FILE_NAME']
SOCKET_HOST         = cfg.locationd['SOCKET_HOST']
SOCKET_PORT         = cfg.locationd['SOCKET_PORT']
MAX_TIME_DIFFERENCE = cfg.locationd['MAX_TIME_DIFFERENCE']
ALMANAC_ROUNDING    = cfg.locationd['ALMANAC_ROUNDING']


################################################################################
#
#    This class runs a thread that acquires the latest data from gpsd.
#    To begin acuiring data, run:
#        gpsp = GpsPoller()
#        gpsp.start()
#    To acquire the dictionary of current TVP values, call:
#        gpsp.value()
#    To shut down the poller, call:
#        gpsd.join()
#
################################################################################

import gps
class GpsPoller(threading.Thread):

    def __init__(self):
        self._stopevent    = threading.Event() # Used to shut down the poller
        self.current_value = {}
        self.system_time_has_been_set = False
        self.session = None
        try:
            threading.Thread.__init__(self)
            self.session  = gps.gps(mode=WATCH_ENABLE)
            self.watching = True
            logging.info('GPS monitoring started.')
        except:
            self.watching = False
            logging.warning('Failed to open GPS stream. Falling back on cached values.')

    def value(self):
        return self.current_value

    def run(self):
        while self.watching and not self._stopevent.isSet():
            try:
                report = self.session.next()
                if report['class'] == 'TPV':
                    self.current_value = self.session.next()
                    if not self.system_time_has_been_set:
                        self.check_set_system_time(report)
            except:
                logging.error('Error reading gpsd data.')
            time.sleep(0.2) # tune this, you might not get values that quickly

    def check_set_system_time(self, report):
        if report['mode'] >= 2:
            self.system_time_has_been_set = True
            rep_time  = datetime.datetime.strptime(report['time'], '%Y-%m-%dT%H:%M:%S.%f%z')
            sys_time  = datetime.datetime.now(datetime.timezone.utc)
            time_diff = abs((sys_time - rep_time).total_seconds())
            if time_diff > MAX_TIME_DIFFERENCE:
                logging.info('Sys time = %s', sys_time)
                logging.info('GSP time = %s', rep_time)
                logging.info('System time differes from GPS time by %s seconds. Updating.', int(time_diff))
                try:
                    os.system('date -s ' + report['time'])
                except:
                    logging.error('Failed to set system time.')

    def join(self, timeout=None):
        self._stopevent.set()
        time.sleep(0.5) # Time for current operation to end
        if self.session is not None:
            self.session.close()
        threading.Thread.join(self, timeout)


################################################################################
#
#    Location Service guts:
#        global variables
#        startup/shutdown
#        GpsPoller -> state variable interface
#
################################################################################

gpsp   = GpsPoller()
state  = {'mode':0, 'time':'?', 'lat':0.0, 'lon':0.0, 'alt':0, 'speed':0.0, 'climb':0.0 }

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
            logging.warning('Cache file wrong version, ignoring.')
            return
        state = loaded_state
        del state['persistance_version']
        state['mode'] = -1
        logging.info('Cache loaded.')
    except IOError:
        logging.error('Error reading cache file.')
    except:
        logging.error('Error loading cache file.')


# Termination routine
def shutdown():
    persist_state()
    gpsp.join() # Shuts down poller
    exit(0)


# Update the global 'state' dictionary from the GpsPoller
def update_state():
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


################################################################################
#
#    The socket server makes IPC with the system service possible.
#    Short keyword messages are sent to the socket, and JSON strings are returned.
#    Valid selectors:
#        gps    Returns the state dictionary
#        time   Returns the output from a TimeCalc (utc, lcoal, solar, sidereal, etc)
#        day    Returns the shape-of-day for the current local day
#        sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto
#           Returns name, alt, azm, and distance in miles
#
################################################################################

# Return a JSON string representing the current state:
def get_json():
    update_state()
    return json.dumps(state)


# Generate the shape-of-day info dictionary, convert to JSON and return.
# Note: this is extremely expensive on the RPiZero.
def get_day_info():
    update_state()
    di = DayCalc.DayCalc(state['lat'], state['lon'], state['alt'])
    return di.as_json()


# Return JSON representing TimeCalc info
def get_time_info():
    update_state()
    result             = {}
    tcalc              = astro.get_TimeCalc(state['lat'], state['lon'])
    result['utc']      = tcalc.getUtcTime().strftime('%H:%M:%S')
    result['local']    = tcalc.getLocalTime().strftime('%H:%M:%S')
    result['solar']    = tcalc.getSolarTime().strftime('%H:%M:%S')
    result['timezone'] = tcalc.getTimeZoneName()
    result['jdate']    = tcalc.getJDate()
    result['gmst']     = tcalc.decimalHoursToHMS(tcalc.getGMST())
    result['lmst']     = tcalc.decimalHoursToHMS(tcalc.getLMST())
    result['doy']      = tcalc.getDOY(tcalc.getLocalTime())
    strResult          = json.dumps(result)
    logging.debug('Result: %s', strResult)
    return strResult


# Return an almanac json blob for the body requested
def get_almanac(body_name):
    logging.debug('Generating almanac for %s', body_name)
    result = {}
    target = astro.body_from_name(body_name)
    if target is None:
        return'{"error": "name"}'
    update_state()
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
    logging.debug('Result: %s', strResult)
    return strResult


# Never return: wait for socket connections
def socket_server():
    logging.info('Starting socket server.')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.debug('socket created.')
    #Bind socket to local host and port
    try:
        sock.bind((SOCKET_HOST, SOCKET_PORT))
        logging.info('Socket bound to port %s on host %s.' % (SOCKET_PORT, SOCKET_HOST))
    except socket.error as msg:
        logging.critical('Socket bind failed.')
        sys.exit()
    except Exception as e:
        logging.warning('Unknown exception:')
        logging.warning(e)
        logging.warning('Continuing...')
    #Start listening on socket
    sock.listen(10)
    logging.info('Socket now listening')

    #now keep talking with the client
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = sock.accept()
        data = conn.recv(16)
        msg = data.decode()
        logging.info("Server received: '%s' from %s:%s" % (msg, addr[0], str(addr[1])))
        if 'gps' == msg:
            reply = get_json()
        elif 'time' == msg:
            reply = get_time_info()
        elif 'day' == msg:
            reply = get_day_info()
        elif msg in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']:
            reply = get_almanac(msg)
        else:
            logging.warning('Unexpected selector in socket msg: %s' % (msg))
            reply = '{"error":"' + msg + '"}'
        conn.sendall(reply.encode())
        conn.close()
    sock.close()


################################################################################
#
#    Location Service startup code
#
################################################################################

if __name__ == '__main__':
    load_state()
    gpsp.start()
    logging.info('gpsd started.')
    try:
        while True:
            socket_server()
    except Exception as ex:
        logging.critical('locationd is shutting down due to an exception.')
        logging.critical('Exception: %s', ex)
        shutdown()
