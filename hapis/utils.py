#---------------------------------------------------------------------------
# Various utility functions
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Setup functions
#---------------------------------------------------------------------------
def getSetupInfo(reqment):
    """This function will try and return the info from setuptools"""
    retval = {}
    try:
        from pkg_resources import get_distribution
        from pkg_resources import DistributionNotFound, VersionConflict
        try:
            pkgInfo = get_distribution(reqment).get_metadata('PKG-INFO')
        except (DistributionNotFound, VersionConflict, FileNotFoundError):
            pkgInfo = ""
        from email import message_from_string
        msg = message_from_string(pkgInfo)
        for key in msg:
            values = msg.get_all(key)
            newValues = []
            for value in values:
                newValues.append("".join(value.split("\n"))[:72])
            values = newValues
            if len(values) == 1:
                retval[key] = values[0]
            else:
                retval[key] = values

    except ImportError:
        pass # oh well never mind
    return retval

#---------------------------------------------------------------------------
# String/text functions
#---------------------------------------------------------------------------
import re
def secureSettings(settings):
    retval = {}
    for key, value in settings.items():
        if 'secret' in key:
            value = '$$$$$$$$$$$$$'
        elif 'password' in key:
            value = '*************'
        elif 'url' in key:
            pwdMatch = re.search(r'(.*:)([^@]+)(@.*)', value)
            if pwdMatch:
                value = "{0}**********{2}".format(*pwdMatch.groups())
        retval[key] = value
    return retval

def dollars(num):
    return "${:,.2f}".format(num) if num >= 0 else "-${:,.2f}".format(-num)

def asciiarrows(text):
    text = text.replace("\N{leftwards arrow}",     "<-")
    text = text.replace("\N{rightwards arrow}",    "->")
    text = text.replace("\N{horizontal ellipsis}", "...")
    return text

def pad3(text):
    padding = " " * (3 - len(text))
    return padding + text

#---------------------------------------------------------------------------
# Date/Time functions
#
# Globally, shutdown is from 16:00 to 17:00 US/Eastern (a standard in currency
# trading).  Months will start on last day of US/Eastern calendar month at
# 16:01 (though no trades will have an executed time earlier than 17:00) and
# will end on last day of US/Eastern calendar month at 16:00.  All credit
# limits, dropdowns, commission accounts etc. will be based on this month for
# all users.
# 
# We use an internal epoch of 1969-12-31 16:01 EST.
# This is only visible for periods that do no fit evenly into 12 months.
# It is used as the ultimate starting point of those periods.
# e.g. a 24month period covers 1969-12-31 16:01 EST -> 1971-12-31 16:01 EST.
#---------------------------------------------------------------------------
from calendar import monthrange
from datetime import timedelta, datetime
from collections import namedtuple
from numbers import Number
import pytz

# Months start on last day of US/Eastern calendar month at 16:01
tradingTZ = pytz.timezone("US/Eastern")
tradingDayStartOffset = timedelta(hours=7, minutes=59)
marketOpeningOffset = timedelta(hours=7)

# These functions return datetimes in the trading (US/Eastern) timezone
def tradingNow():
    """Time now in trading (US/Eastern) timezone"""
    return tradingTZ.fromutc(datetime.utcnow())

def tradingToday():
    """Date today in trading (US/Eastern) timezone"""
    return tradingTZ.fromutc(datetime.utcnow()).date()

def getTradingStartOfDay(year, month, day):
    """Get Start of Day in the trading (US/Eastern) timezone"""
    midnight = tradingTZ.localize(datetime(year, month, day, 0, 0))
    # this is safe because daylight savings changes at 2:00 a.m. local time
    return midnight - tradingDayStartOffset

def getTradingEndOfDay(year, month, day):
    """Get End of Day in the trading (US/Eastern) timezone"""
    return tradingTZ.localize(datetime(year, month, day, 16, 0))

def getTradingMarketOpening(year, month, day):
    """Get Market Opening time in the trading (US/Eastern) timezone"""
    midnight = tradingTZ.localize(datetime(year, month, day, 0, 0))
    # this is safe because daylight savings changes at 2:00 a.m. local time
    return midnight - marketOpeningOffset

def getTradingMonth(fromWhen):
    """
    Get Year and Month (and months-since-epoch) in the trading (US/Eastern)
    timezone from either a naive datetime, or the number of months since epoch
    """
    TradingMonth = namedtuple("TradingMonth", "year month monthsSinceEpoch")
    EpochYear = 1970
    if isinstance(fromWhen, datetime):
        assert(fromWhen.tzinfo is None)
        workingdt = tradingTZ.fromutc(fromWhen) + tradingDayStartOffset
        months = (workingdt.year - EpochYear) * 12 + workingdt.month - 1
        return TradingMonth(workingdt.year, workingdt.month, months)
    else:
        year  = EpochYear + fromWhen // 12
        month = 1 + fromWhen % 12
        return TradingMonth(year, month, fromWhen)

# These functions return naive datetimes in the UTC timezone
def getMarketOpening(year, month, day):
    """Get Market Opening time in the UTC timezone"""
    tradingdt = getTradingMarketOpening(year, month, day)
    return tradingdt.astimezone(pytz.utc).replace(tzinfo=None)

def getNextTradeTime():
    """When is the next time we can make a trade in the UTC timezone"""
    tradingdt = tradingNow()
    today     = tradingdt.date()
    yesterday = today - timedelta(days=1)
    tradingClosed = getTradingEndOfDay(*yesterday.timetuple()[:3])
    tradingOpens  = getTradingMarketOpening(*today.timetuple()[:3])
    if tradingClosed < tradingdt < tradingOpens:
        tradingdt = tradingOpens
    return tradingdt.astimezone(pytz.utc).replace(tzinfo=None)

def getStartOfTradingDay(year, month, day):
    """Get the start of the trading day in the UTC timezone"""
    tradingdt = getTradingStartOfDay(year, month, day)
    return tradingdt.astimezone(pytz.utc).replace(tzinfo=None)

def getEndOfTradingDay(year, month, day):
    """Get the end of the trading day in the UTC timezone"""
    tradingdt = getTradingEndOfDay(year, month, day)
    return tradingdt.astimezone(pytz.utc).replace(tzinfo=None)

def getStartOfTradingMonth(year, month):
    """Get the start of the trading month in the UTC timezone"""
    return getStartOfTradingDay(year, month, 1)

def getEndOfTradingMonth(year, month):
    """Get the end of the trading month in the UTC timezone"""
    return getEndOfTradingDay(year, month, monthrange(year, month)[1])

def getStartOfTradingPeriod(naivedt, months):
    """Get the start of a trading period in the UTC timezone"""
    assert(naivedt.tzinfo is None)
    monthsSinceEpoch = getTradingMonth(naivedt).monthsSinceEpoch
    monthsSinceEpoch -= monthsSinceEpoch % months # round down
    year, month, _ = getTradingMonth(monthsSinceEpoch)
    return getStartOfTradingMonth(year, month)

def getEndOfTradingPeriod(naivedt, months):
    """Get the end of a trading period in the UTC timezone"""
    assert(naivedt.tzinfo is None)
    monthsSinceEpoch = getTradingMonth(naivedt).monthsSinceEpoch
    monthsSinceEpoch += months - monthsSinceEpoch % months - 1 # round up
    year, month, _ = getTradingMonth(monthsSinceEpoch)
    return getEndOfTradingMonth(year, month)

# These functions return datetimes in the timezone given
def localNow(tz):
    """Time now in the given timezone"""
    return tz.fromutc(datetime.utcnow())

def localToday(tz):
    """Date today in the given timezone"""
    return tz.fromutc(datetime.utcnow()).date()

def localDateTimeStr(naivedt, tz):
    """Formated string for the given datetime in the given timezone"""
    assert(naivedt.tzinfo is None)
    return tz.fromutc(naivedt).strftime("%Y-%m-%d %H:%M")

def localDateStr(naivedt, tz):
    """Formated string for the given date in the given timezone"""
    assert(naivedt.tzinfo is None)
    return tz.fromutc(naivedt).strftime("%Y-%m-%d")

# Grid conversion function
def recsToRows(recs, headings, tz=pytz.utc):
    """Translate records to lists of displayable strings"""
    rows = []
    for rec in recs:
        row = []
        for field, _ in headings:
            value = getattr(rec, field, "")
            if value is None:
                value = ""
            elif isinstance(value, datetime):
                value = localDateTimeStr(value, tz)
            elif isinstance(value, Number):
                value = "{:,}".format(value)
            else:
                value = str(value)
            row.append(value)
        rows.append(row)
    return rows

#---------------------------------------------------------------------------
# Process functions
#---------------------------------------------------------------------------
import sys
import time
import os
from os import path
import resource		# Resource usage information.

def daemonSpawn(cmd, *args, cwd="/", log="/dev/null", sleepChild=0):
    pid = os.fork()
    if pid > 0:
        return os.waitpid(pid, 0)
    # Child
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)
    except OSError as e:
        sys.stderr.write("Fork #2 failed: {}\n".format(e))
        os._exit(1)
    # Grandchild
    os.chdir(cwd)
    os.umask(0)
    sys.stdout.flush()
    sys.stderr.flush()
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = 2048
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:	# fd wasn't open to begin with (ignored)
            pass
    os.open("/dev/null", os.O_RDONLY)                      # reopen STDIN
    os.open(log, os.O_RDWR|os.O_CREAT|os.O_APPEND, 0o660)  # reopen STDOUT
    os.dup2(1, 2)                                          # reopen STDERR
    if sleepChild:
        time.sleep(sleepChild) # favour parent process
    os.execlp(cmd, path.basename(cmd), *args)

def launchPostMail(settings):
    here    = settings['here']
    cfgfile = settings['__file__']
    daemonSpawn("hapis_post_mail", "data/mail", "--config", cfgfile,
                cwd=here, log="post_mail.log", sleepChild=1.25)

def getPostMailLauncher(settings):
    return lambda: launchPostMail(settings)

def launchEvalOrders(settings):
    here    = settings['here']
    cfgfile = settings['__file__']
    daemonSpawn("hapis_eval_orders", cfgfile, cwd=here, log="eval_orders.log")

