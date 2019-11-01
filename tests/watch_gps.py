from gps import *

if __name__ == '__main__':
    try:
        gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE)
        while True:
            report = gpsd.next()
            print(report['class'])
    except KeyboardInterrupt:
        gpsd.close()
