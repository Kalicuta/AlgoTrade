from datetime import datetime


def string_to_time(date, time, ms=0):
    yy, mo, dd = date.split('/')
    hh, mi, ss = time.split(':')
    dt = datetime(int(yy), int(mo), int(dd), int(hh), int(mi), int(ss), microsecond=ms)
    return dt
