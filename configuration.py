# Reference: https://martin-thoma.com/configuration-files-in-python/
import logging

locationd = {
    'LOGGING_LEVEL'       : logging.INFO,
    'CACHE_FILE_NAME'     : '/var/cache/locationd/locationd.cache',
    'SOCKET_HOST'         : '127.0.0.1',   # Socket server
    'SOCKET_PORT'         : 9999,          # Socket server
    'MAX_TIME_DIFFERENCE' : 10,            # Max # seconds GPS can differ from system time
    'ALMANAC_ROUNDING'    : 3              # How many places to round almanac values to
}