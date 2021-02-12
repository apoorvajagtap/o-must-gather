import sys, os
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from omg.common.config import Config

# This function is used to calculate age of the objects
# We compare the time reported in the yaml definition,
# with the timestamp of the yaml file (i.e, when it was generated).
# This should give us age of the object at the time of must-gather
# By default, ts1 is considered in iso-8601 e.g: '2020-06-04T22:10:41Z'
# and ts2 is considered in unix/epoch format e.g: 1590912494.0 (returned by os.path.getmtime)

def age(ts1, ts2, ts1_type='iso', ts2_type='epoch'):

    try:
        if ts1_type == 'iso':
            dt1 = parse(ts1, ignoretz=True)
        elif ts1_type == 'epoch':
            dt1 = datetime.utcfromtimestamp(ts1)
    
        if ts2_type == 'iso':
            dt2 = parse(ts2, ignoretz=True)
        elif ts2_type == 'epoch':
            dt2 = datetime.utcfromtimestamp(ts2)        
        
        rd = relativedelta(dt2, dt1)
    except:
        return 'Unknown'

    if rd.days > 0:
        return str(rd.days)+'d'
    elif rd.hours > 9:
        return str(rd.hours)+'h'
    elif rd.hours > 0 and rd.hours < 10:
        return str(rd.hours)+'h'+str(rd.minutes)+'m'
    elif rd.minutes > 9:
        return str(rd.minutes) + 'm'
    elif rd.minutes > 0 and rd.minutes < 10:
        return str(rd.minutes)+'m'+str(rd.seconds)+'s'
    else:
        return str(rd.seconds)+'s'

# This is a helper function to load yaml files
# Input: yaml file path (yp)
# Output: python dict of the yaml
#
# This is handled in separate function instead of simply
# calling yaml.safe_load(),
# because some yamls generated by must-gather contain garbage lines
# at the end causing the yaml.safe_load() to error out.
# so if the first loading attempt fails, we will
# try to skip lines from the end and try to load the yaml
def load_yaml_file(yp, print_warnings):
    import yaml
    from click import echo
    try:
        # use C version if possible for speedup
        from yaml import CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeLoader

    with open(yp, 'r') as yf:
        yd = yf.read()
        try:
            res = yaml.load(yd, Loader=SafeLoader)
            return res
        except:
            # yaml load failed
            # try skipping lines from the bottom
            # Until we are able to load the yaml file
            # We will try until > 1 lines are left
            lines_total = yd.count('\n')
            lines_skipped = 0
            while yd.count('\n') > 1:
                # skip last line
                yd = yd[:yd.rfind('\n')]
                lines_skipped += 1
                try:
                    res = yaml.load(yd, Loader=SafeLoader)
                    if print_warnings:
                        echo("[WARN] Skipped " +
                            str(lines_skipped) + "/" + str(lines_total) +
                            " lines from the end of " + os.path.basename(yp) +
                            " to the load the yaml file properly",err=True)
                    return res
                except:
                    pass
            # Skipping lines from the bottom didn't help. Error out
            if print_warnings:
                print("[ERROR] Invalid yaml file. Parsing error in ", yp)
            sys.exit(1)
