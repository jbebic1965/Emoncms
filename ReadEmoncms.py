#%%
import requests
import datetime

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import dates

#%% Function that retrieves all data from a feed by sequentially querying NQmax points at the time, set Nmax to max number of points to query, or 0 to get all
def retrieve_all(feedurl, feedId, apikey, feedParms, NQmax, Nmax):
    print 'Retrieving:', feedId
    Np = feedParms['npoints']
    ti = feedParms['interval']
    ts = feedParms['start_time']
    print '  Begins on:', datetime.datetime.fromtimestamp(ts)
    print '  Contains:', Np, 'points'    
    te = ts - ti # initial end time for query, see logic inside the while loop to understand why set like this initially
    nq = 0 # number of queried points
    vals = np.empty(shape=(0,2)) # empty array to hold the values
    
    if Nmax <= 0:
        Nmax = Np
    while nq < Nmax-NQmax:
        nq = nq + NQmax
        ts = te + ti # new start is the previous end plus one interval
        te = te + NQmax*ti
        print '  Querying interval:', datetime.datetime.fromtimestamp(ts), 'to:', datetime.datetime.fromtimestamp(te)
        feedVals = requests.get(url=feedurl, params={'id':feedId, 'start':ts*1000, 'end':te*1000, 'interval':ti, 'apikey':apikey}).json()
        vals = np.append(vals, np.array(feedVals), axis=0)
    # capturing the remaining points
    ts = te + ti
    te = te + (Nmax-nq)*ti
    print '  Querying interval:', datetime.datetime.fromtimestamp(ts), 'to:', datetime.datetime.fromtimestamp(te)
    feedVals = requests.get(url=feedurl, params={'id':feedId, 'start':ts*1000, 'end':te*1000, 'interval':ti, 'apikey':apikey}).json()
    vals = np.append(vals, np.array(feedVals), axis=0)
    return vals


#%% Authentication for Bebic5 home
apikey = '8704120f75b7369408fb893efdf00f6b'

#%% Open energy monitor configuration
feeds_url = 'https://emoncms.org/feed/'

get_list  = 'list.json'
get_meta  = 'getmeta.json?'
get_data  = 'data.json?'
get_avgs  = 'average.json?'

#%% Retrieving the list of feeds
feeds = requests.get(url= feeds_url + get_list, params={'apikey':apikey}).json()

#%% Retrieving the metadata for all feeds in the list
feeds_names = {}
feeds_metadata = {}
for d in feeds:
    # print d['id'], ':', d['name']
    feeds_names[d['id']] = d['name']
    feeds_metadata[d['id']]=requests.get(url=feeds_url+get_meta, params={'id':d['id'],'apikey':apikey}).json()
    
#%% These are the feed numbers I want to harvest, print their specifics
CT1pwrId = '66718'
CT2pwrId = '66719'
print feeds_names[CT1pwrId]
print '  Begins on:', datetime.datetime.fromtimestamp(feeds_metadata[CT1pwrId]['start_time'])
print '  Contains:', feeds_metadata[CT1pwrId]['npoints'], 'points'
print '  Lasts:', feeds_metadata[CT1pwrId]['npoints']/(3600/feeds_metadata[CT1pwrId]['interval'])/24, 'days'

print feeds_names[CT2pwrId]
print '  Begins on:', datetime.datetime.fromtimestamp(feeds_metadata[CT2pwrId]['start_time'])
print '  Contains:', feeds_metadata[CT2pwrId]['npoints'], 'points'
print '  Lasts:', feeds_metadata[CT2pwrId]['npoints']/(3600/feeds_metadata[CT2pwrId]['interval'])/24, 'days'

#%% Data retrieval packaged inside the function
NpQueryLim = 3000 # 3000 points is the query limit
Nmax = -1 # int(2*7*24*3600/10) # want to retrieve two weeks worth
print feeds_names[CT1pwrId]
pwr1 = retrieve_all(feeds_url+get_data, CT1pwrId, apikey, feeds_metadata[CT1pwrId], NpQueryLim, Nmax)
print feeds_names[CT2pwrId]
pwr2 = retrieve_all(feeds_url+get_data, CT2pwrId, apikey, feeds_metadata[CT2pwrId], NpQueryLim, Nmax)

#%% Prep to output a plot with timestamps on x axis
# convert epoch to matplotlib float format
nstart=200 # sets the starting sample, there is garbage in the first few samples
s = pwr1[nstart:,0]/1000
dts = map(datetime.datetime.fromtimestamp, s)
fds = dates.date2num(dts) # converted

# matplotlib date format object
# hfmt = dates.DateFormatter('%Y/%m/%d %H:%M')
hfmt = dates.DateFormatter('%Y/%m/%d')

#%% Generate figure
if False:
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(fds, pwr1[nstart:,1])
    ax.plot(fds, pwr2[nstart:,1])
    
    ax.xaxis.set_major_locator(dates.DayLocator())
    ax.xaxis.set_major_formatter(hfmt)
    # ax.set_ylim(ymin=-1000,ymax=6000)
    plt.xticks(rotation='vertical')
    plt.subplots_adjust(bottom=.3)
    plt.show()

#%% Transfer to pandas
# df1 = pd.DataFrame(data=pwr1[:,[1]], index=pwr1[:,[0]], columns=['unixtime', 'Pwr1'])
# df2 = pd.DataFrame(data=pwr2[:,[1]], index=pwr2[:,[0]], columns=['unixtime', 'Pwr2'])
df1 = pd.DataFrame(data=pwr1[:,1], index=pwr1[:,0], columns=['pwr1'])
df2 = pd.DataFrame(data=pwr2[:,1], index=pwr1[:,0], columns=['pwr2'])
df3 = df1.join(df2)

#%% Save as hdf file
h5store = pd.HDFStore('PwrData.h5')
h5store.put('dfpwr',df3)
h5store.close()

