# Introduction
This tool chain retrieves and analyzes residential load data to provide insight into the relationship of the number of homes and the shape of their aggregate load pattern. It is generally well understood that electric load of any single home has a rather intermittent consumption throughout the day and that this intermittency decreases as many homes are considered in aggregate. What is not well understood is the relationship between the two.

The key obstacle here is the absence of data: While it is relatively easy to instrument one home and collect power recordings every few seconds, it is  impractical to do this for a large number of homes. One way to overcome this problem is to hypothesize that the sum of recordings of N sequential days from a single residence is a representative substitute for aggregate load of N residences on a single day. In other words, it can be hypothesized that the Tuesday recordings from a monitored home are equivalent to would-be-Monday recordings of the first neighbor's load, the Wednesday recordings are equivalent to would-be-Monday recordings of the second neighbor's load, and so on. Such approach enables extracting the relationship between intermittency and the number of homes by collecting high-speed data from only one home.

The data is gathered by the open energy monitor (http://openenergymonitor.org)  collecting power data every 10 seconds. The recordings are archived on the associated Emoncms cloud service (http://emoncms.org). The system is installed on a five-person family home near Albany NY and has been in continuous operation since January 2015. The system is made up of: an emonTx, an emonTH, and an emonBase.

# Operation
There are two parts to the toolchain:
1. Data retrieval from the cloud and archival into hdf5 files.
1. Data processing supporting three functions:
    - interpolation
    - averaging, including time-shifted averaging, and
    - plotting

The following subsections describe the code operation for each function.

## Retrieval
The load data is retrieved from Emoncms cloud using ReadEmoncms.py function. The data retrieval is implemented sequentially to respects Emoncms-imposed limit of the number of points per read request. So far, only the power data is retrieved; other channels: voltage, temperature and humidity are available, but are not retrieved. There are two functions within the file: retrieve_range and retrieve_all, retrieve_range is in use in this code version. The read starts at the first full-day record and queries the maximum number of data points allowed by Emoncms. The query is then recofigured to read the subsequent interval, until either the end of date range is reached or the maximum number of points (Nmax) is read. Specifying a negative Nmax results in ignoring the limit. The retrieved recordings are sequentially placed into a growing numpy array. This numpy array is a return value from the function.

The outer calling script retrieves the desired power recordings (one from CT1 and another from CT2) then packages the returned numpy arrays into dataframes and saves them into hdf5 files.

## Analysis
The load data is retrieved from h5 files and processed to infer the relationship between the load patterns and the number of sequential days:
1. User inputs are hard-coded within the script to specify:
  - number of days to process and
  - the parameters for horizontal shifting of time recordings.
1.  Starting from the first record in the input dataframe, days are selected one at a time and added to aggregator dataframes. There are three aggregator dataframes:
  - the first sums the records without time shifting,
  - the second uses uniformly distributed time shift in the interval of +/- 2hours, and
  - the third uses normally distributed time shift with the mean value of zero and standard deviation of 40min.

Time shifting is used to further diversify load patterns on the basis that not all homes in the neighborhood start their day at the same time in the morning. The day's load and the aggregate load are plotted together to illustrate formation of daily load patterns. The process repeats user-specified number of times and generates as many pages in the pdf file. There are three pdf files: Results1 prepared with no time shifting, Results2 prepared with uniformly distributed time shift, and Results3 prepared with normally distributed time shift.  

The relationship between level of aggregation and load intermittency is quantified by calculating the crest factor of aggregate load. The crest factor of a signal is the peak value on the interval, divided by the RMS value on the same interval. As each day is processed, the crest factor is calculated for the aggregate loads. Two definitions of crest factors are used: the default (peak/RMS) and the modified (peak/average value). The plots of the crest factor as the function of number of homes are output in the Summary.pdf file.

Happy analysis!
