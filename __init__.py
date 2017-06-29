import sys
import datetime
import pytz
import atexit

import clr
import pandas as pd

sys.path.append('C:\\Program Files\\PIPC\\AF\\PublicAssemblies\\4.0\\')

clr.AddReference('OSIsoft.AFSDK')
from OSIsoft import AF
from OSIsoft.AF import Analysis
from OSIsoft.AF import Asset
from OSIsoft.AF import Collective
from OSIsoft.AF import Data
from OSIsoft.AF import Diagnostics
from OSIsoft.AF import EventFrame
from OSIsoft.AF import Modeling
from OSIsoft.AF import Notification
from OSIsoft.AF import PI
from OSIsoft.AF import Search
from OSIsoft.AF import Time
from OSIsoft.AF import UI
from OSIsoft.AF import UnitsOfMeasure

piServer = None
piafServer = None
piafDB = None

def connectPIServer(serverName = ''):
    global piServer
    piServers = PI.PIServers()
    if serverName == '':
        piServer = piServers.DefaultPIServer
    else:
        piServer = piServers[serverName]
    piServer.Connect(False)

def connectPIAFServer(serverName = ''):
    global piafServer
    global piafDB
    piServers = AF.PISystems()
    if serverName == '':
        piafServer = piServers.DefaultPISystem
    else:
        piafServer = piServers[serverName]
    piafServer.Connect()
    piafDB = piafServer.Databases.DefaultDatabase

def SearchTags(query, source = None):
    global piServer
    if not piServer:
        connectPIServer()
    tags = PI.PIPoint.FindPIPoints(piServer, query, source, None)
    return [tag.Name for tag in tags]

def CurrentValue(tagname):
    global piServer
    if not piServer:
        connectPIServer()
    tag = PI.PIPoint.FindPIPoint(piServer, tagname)
    lastData = tag.Snapshot()
    return pd.DataFrame([__value_to_dict(lastData.Value, lastData.Timestamp.UtcTime)])

def CompressedData(tagname, starttime, endtime):
    global piServer
    if not piServer:
        connectPIServer()
    timeRange = Time.AFTimeRange(starttime, endtime)
    tag = PI.PIPoint.FindPIPoint(piServer, tagname)
    pivalues = tag.RecordedValues(timeRange, Data.AFBoundaryType.Inside, None, None)
    return pd.DataFrame([__value_to_dict(x.Value, x.Timestamp.UtcTime) for x in pivalues])

def SampledData(tagname, starttime, endtime, interval):
    global piServer
    if not piServer:
        connectPIServer()
    timeRange = AFTimeRange(starttime, endtime)
    span = AFTimeSpan.Parse(interval)
    tag = PIPoint.FindPIPoint(piServer, tagname)
    pivalues = tag.InterpolatedValues(timeRange, span, "", False)
    return pd.DataFrame([__value_to_dict(x.Value, x.Timestamp.UtcTime) for x in pivalues])

def __value_to_dict(value, timestamp):
    local_tz = pytz.timezone('Europe/Amsterdam')
    return {
        'Value': value,
        'Timestamp': datetime.datetime(timestamp.Year,
                                       timestamp.Month,
                                       timestamp.Day,
                                       timestamp.Hour,
                                       timestamp.Minute,
                                       timestamp.Second,
                                       timestamp.Millisecond*1000).replace(tzinfo = pytz.utc).astimezone(local_tz)
    }

def __disconnect():
    global piServer
    global piafServer
    if piServer:
        piServer.Disconnect()
        piServer = None
    if piafServer:
        piafServer.Disconnect()
        piafServer = None
atexit.register(__disconnect)