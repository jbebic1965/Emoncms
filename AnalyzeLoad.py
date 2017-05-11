# -*- coding: utf-8 -*-
"""
Created on Mon May 08 13:10:23 2017

@author: 200010679
"""

from datetime import datetime, timedelta
import time
import pytz

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import dates
import matplotlib.backends.backend_pdf as dpdf
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

#%% Select interval
def SelectInterval(df3,t1,t2,ts):
    ix1 = (t1+ts)*1000
    ix2 = (t2+ts)*1000
    df2 = df3[(df3.index >= ix1) & (df3.index < ix2)]
    return df2

def PrepForAccumulation(df2):
    pwr = df2['pwr1'].values + df2['pwr2'].values
    indf = (df2.index.values - df2.index.values[0])/1000
    ind = np.round(indf).astype(np.int)
    df2a= pd.DataFrame(data={'pwr':pwr,'ind':ind},index=ind)
    df2a= df2a.drop_duplicates(subset='ind',keep='first')
    df2a= df2a.reindex(np.arange(0,24*3600,10))
    df2a.drop('ind', axis=1, inplace=True)
    df2a.interpolate(method='linear', axis=0, limit=10, inplace=True) # up to 10 consequtive NaNs gets interpolated
    return df2a

def CrestFactorRMS(signal):
    peak = np.amax(signal)
    rms =  np.sqrt(np.mean(np.square(signal)))
    return peak/rms

def CrestFactorAvg(signal):
    peak = np.amax(signal)
    avg =  np.mean(signal)
    return peak/avg

#%% function definitions
def OutputDayPage(pltPdf, df2, df1, na, cf):
    fig, (ax0,ax1) = plt.subplots(nrows=2, ncols=1,
                                              figsize=(8,6),
                                              sharex=True)
    
    ts = df2.index.values[0]/1000
    # fig.suptitle(datetime.fromtimestamp(ts)) # This titles the figure
    fig.suptitle(datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S %a')) # This titles the figure

    time = (df2.index.values - df2.index.values[0])/1000/3600

    majorLocator = MultipleLocator(6)
    majorFormatter = FormatStrFormatter('%d')
    minorLocator = MultipleLocator(1)

    ax0.set_title('pwr1, pwr2 [kW]')
    ax0.plot(time, df2['pwr1']/1000)
    ax0.plot(time, df2['pwr2']/1000)
    ax0.set_ylim([0,10])
    ax0.grid(True, which='both')

    ax1.set_title('Cumulative pwr [kW], Cf = %4.2f, Na = %d' % (cf, na))
    ax1.plot(df1.index.values/3600., df1['pwr']/1000.)
    # ax1.set_ylim([-500,500])
    ax1.set_xlim([0,24])
    ax1.set_ylim(bottom=0)
    ax1.xaxis.set_major_locator(majorLocator)
    ax1.xaxis.set_major_formatter(majorFormatter)
    ax1.xaxis.set_minor_locator(minorLocator)
    ax1.set_xlabel('Time [h]')
    ax1.grid(True, which='both')

    pltPdf.savefig() # Saves fig to pdf
    plt.close() # Closes fig to clean up memory
    return

#%% Retrieve hdf records
h5store = pd.HDFStore('PwrData.h5')
df3 = h5store.get('dfpwr')
h5store.close()

#%% Fetching start and end date
ts = df3.index.values[0]/1000
te = df3.index.values[-1]/1000

print 'Records begin on:', datetime.fromtimestamp(ts)
print 'Records end on:', datetime.fromtimestamp(te) 

#%% Open pdf files for plots
print "Opening: Results1.pdf"
pltPdf1 = dpdf.PdfPages('Results1.pdf')
print "Opening: Results2.pdf"
pltPdf2 = dpdf.PdfPages('Results2.pdf')
print "Opening: Results3.pdf"
pltPdf3 = dpdf.PdfPages('Results3.pdf')

#%% Prep for plotting
temp = datetime.fromtimestamp(ts) 
temp = temp.replace(hour=0,minute=0,second=0)
temp = temp + timedelta(days=2) # Skip day 1
# print 'Records temp:', datetime.fromtimestamp(time.mktime(temp.timetuple())) 

# User specified parameters
hmax = 2. # max horizontal shift in hours
Ndays = 51 # number of days to aggregate
temp1 = temp + timedelta(days=Ndays)
temp1 = temp1 + timedelta(hours=-hmax)
tee =  time.mktime(temp1.timetuple())
if tee > te:
    print 'The desired end date is beyond records end, reseting to records end'
    tee = te

# temp = temp + timedelta(days=1)
t1 = time.mktime(temp.timetuple())

temp = temp + timedelta(days=1)
t2 = time.mktime(temp.timetuple())
print 'Start of 1st day after records begin:', datetime.fromtimestamp(t1)
print 'Start of 2nd day after records begin:', datetime.fromtimestamp(t2)

# zeroed dataframe to hold sum of power
df1  = pd.DataFrame(data=np.zeros(shape=(24*3600/10,1)),index=np.arange(0,24*3600,10),columns=['pwr'])
df1n = pd.DataFrame(data=np.zeros(shape=(24*3600/10,1)),index=np.arange(0,24*3600,10),columns=['pwr'])
df1u = pd.DataFrame(data=np.zeros(shape=(24*3600/10,1)),index=np.arange(0,24*3600,10),columns=['pwr'])

na  = 0 # Number of aggregates
cf1  = np.zeros(shape=(Ndays-1,1))
cf1n = np.zeros(shape=(Ndays-1,1))
cf1u = np.zeros(shape=(Ndays-1,1))
cf2  = np.zeros(shape=(Ndays-1,1))
cf2n = np.zeros(shape=(Ndays-1,1))
cf2u = np.zeros(shape=(Ndays-1,1))

#%% Plotting
while t2 < tee:
    # no shifting
    df2 = SelectInterval(df3, t1, t2, 0)
    df2a= PrepForAccumulation(df2)
    df1 = df1.add(df2a, fill_value=0.0)
    cf1[na] = CrestFactorRMS(df1['pwr'].values)
    cf2[na] = CrestFactorAvg(df1['pwr'].values)
    OutputDayPage(pltPdf1, df2, df1, na+1, cf1[na])

    # Uniformly distributed shifting
    a = -hmax*3600
    b = hmax*3600
    tsu = np.random.uniform(low=a, high=b)
    df2u= SelectInterval(df3, t1, t2, tsu)
    df2b= PrepForAccumulation(df2u)
    df1u= df1u.add(df2b, fill_value=0.0)
    cf1u[na] = CrestFactorRMS(df1u['pwr'].values)
    cf2u[na] = CrestFactorAvg(df1u['pwr'].values)
    OutputDayPage(pltPdf2, df2u, df1u, na+1, cf1u[na])

    # Normally distributed shifting
    mu = 0.
    sigma = hmax/3.*3600
    tsn = np.random.normal(loc=mu, scale=sigma)
    df2n = SelectInterval(df3, t1, t2, tsn)
    df2c= PrepForAccumulation(df2n)
    df1n = df1n.add(df2c, fill_value=0.0)
    cf1n[na] = CrestFactorRMS(df1n['pwr'].values)
    cf2n[na] = CrestFactorAvg(df1n['pwr'].values)
    OutputDayPage(pltPdf3, df2n, df1n, na+1, cf1n[na])

    # Troubleshooting
    print 't1=', t1, 't2=', t2, 'tsu=', tsu, 'tsn=', tsn

    # Prepare for the next pass
    t1 = t2
    temp = temp + timedelta(days=1)
    t2 = time.mktime(temp.timetuple())
    na = na + 1

#%% Close pdf files
print "Closing: Results1.pdf"
pltPdf1.close() # Close the pdf file
print "Closing: Results2.pdf"
pltPdf2.close() # Close the pdf file
print "Closing: Results3.pdf"
pltPdf3.close() # Close the pdf file

#%% Output summary pages
print "Opening: Summary.pdf"
pltPdf  = dpdf.PdfPages('Summary.pdf')

if True:
    fig, (ax0) = plt.subplots(nrows=1, ncols=1, figsize=(8,6))
    fig.suptitle('Crest factor as a function aggregation') # This titles the figure
    
    x = np.arange(0,na)
    
    ax0.set_title('CrestFactor1=Peak/RMS')
    ax0.plot(x+1, cf1, 'k-', label="cf1")
    ax0.plot(x+1, cf1n, 'b-', label="cf1n")
    ax0.plot(x+1, cf1u, 'r-', label="cf1u")
    ax0.grid(True, which='both')
    ax0.set_xlim(left=0)
#    ax0.set_ylim(bottom=0)
    ax0.set_ylim([0, 4])
    ax0.grid(True, which='both')
    ax0.set_xlabel('Number of homes')
    ax0.set_ylabel('Crest factor')
    ax0.legend(loc='upper right')
    pltPdf.savefig() # Saves fig to pdf
    plt.close() # Closes fig to clean up memory

if True:
    fig, (ax0) = plt.subplots(nrows=1, ncols=1, figsize=(8,6))
    fig.suptitle('Crest factor as a function aggregation') # This titles the figure
    
    x = np.arange(0,na)
    
    ax0.set_title('CrestFactor2=Peak/Avg')
    ax0.plot(x+1, cf2, 'k-', label="cf2")
    ax0.plot(x+1, cf2n, 'b-', label="cf2n")
    ax0.plot(x+1, cf2u, 'r-', label="cf2u")
    ax0.grid(True, which='both')
    ax0.set_xlim(left=0)
#    ax0.set_ylim(bottom=0)
    ax0.set_ylim([0, 4])
    ax0.grid(True, which='both')
    ax0.set_xlabel('Number of homes')
    ax0.set_ylabel('Crest factor')
    ax0.legend(loc='upper right')
    pltPdf.savefig() # Saves fig to pdf
    plt.close() # Closes fig to clean up memory


print "Closing: Summary.pdf"
pltPdf.close() # Close the pdf file
