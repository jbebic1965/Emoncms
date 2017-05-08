#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun May  7 07:56:54 2017

@author: jbebic
@url: http://stackoverflow.com/questions/5498510/creating-graph-with-date-and-time-in-axis-labels-with-matplotlib
"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import dates
import datetime

a = np.array([
    [1293605162197, 0, 0],
    [1293605477994, 63, 0],
    [1293605478057, 0, 0],
    [1293605478072, 2735, 1249],
    [1293606162213, 0, 0],
    [1293606162229, 0, 0]])

d = a[:,0]
y1 = a[:,1]
y2 = a[:,2]

# convert epoch to matplotlib float format
s = d/1000
ms = d-1000*s  # not needed?
dts = map(datetime.datetime.fromtimestamp, s)
fds = dates.date2num(dts) # converted

# matplotlib date format object
hfmt = dates.DateFormatter('%m/%d %H:%M')

fig = plt.figure()
ax = fig.add_subplot(111)
ax.vlines(fds, y2, y1)

ax.xaxis.set_major_locator(dates.MinuteLocator())
ax.xaxis.set_major_formatter(hfmt)
ax.set_ylim(bottom = 0)
plt.xticks(rotation='vertical')
plt.subplots_adjust(bottom=.3)
plt.show()