#!bin/python

###########
# modules #
###########

import os
import sys
import datetime

import numpy as np
import pcraster as pcr

sys.path.insert(0,'/home/rens/Scripts/pylib')

from spatialDataSet2PCR import spatialAttributes, setClone, spatialDataSet
from ncRecipes_fixed import getNCDates, createNetCDF, writeField
from read_temporal_info_to_pcr import getTimedPCRData

##########
# global #
##########

NoneType = type(None)

#############
# functions #
#############

def recast_real_as_natural_ratio(r_f):
    '''Returns the ratio r_n which is the ratio of the natural number n, \
so that r_n= 1:n or r_n= n:1 on the basis of the float r_f provided that \
r_f is non zero, otherwise r_n= 0 is retunred.

At the moment, no check on precision is included.

    Input:
    ======
    r_f:                    float

    Output:
    =======
    r_n:                    float, the ratio of 1:n or n:1, or zero,
                            dependent on the sign and value of r_f
    n_s:                    integer, the selected root to which the decimal
                            part of r_f is scaled; n_s * r_f should again
                            return an integer, including zero.

'''

    #-Initialization
    #-check on r_f
    if not isinstance(r_f, float) and not isinstance(r_f, int):
        sys.exit('r_n is not a float or cannot be recast as a float')
    elif isinstance(r_f, int):
        r_f= float(r_f)
    #-initialize r_n and n_s
    # r_n is set to zero and this value is returned if r_f is zero
    n_s= 1
    r_n= 0.0
    # a precision is defined, a value of zero requires an exact match
    # so that r_f * n_s % 1 equals zero
    precision= 1.0e-5
    n_max= int(1 // precision + 1)

    #-Start
    # If r_f is not zero, split the absolute number abs(r_f) into its inte-
    # ger root and decimal fraction and keep its sign, test on d and return
    # the new value of r_n
    if r_f != 0:
        #-sign, integer and decimal part of r_f
        if r_f < 0:
            s_f= -1.0
        else:
            s_f=  1.0
        m_r= int(abs(r_f))
        d_r= abs(r_f) % 1
        if d_r <= (precision**0.5 * m_r) and m_r > 0:
            d_r= 0.0

        #-recast d_r as n_r
        # Get the absolute inverse of d_r, n_r, and create a list of integers
        # up to the order of n_r + 1, n_list; next, check when the ratio of
        # an element of n_list, n_s over d_r returns an integer (or a float
        # close to one), then return n_s and n_r to compute the ratio that
        # constitutes the decimal part of r_n= m_r + n_r / n_s
        if d_r > 0:
            # get the list of integers to process
            n_list= list(range(2, n_max+1))
            # start at n_s is 1 and compute n_r,
            # next check whether n_r is an integer and if not, repeat
            # by getting n_s from n_list in ascending order until this
            # condition is met
            n_s= 1
            n_r= d_r * n_s
            while abs(n_r - round(n_r)) > precision and len(n_list) > 0:
                n_s= n_list.pop(0)
                n_r= d_r * n_s
        #-return r_n, the sum of the integer and the decimal part, the
        # latter being n_r / n_s; the total sum is multiplied by the sign.
        n_r= round(d_r * n_s)
        r_n= s_f* (m_r + n_r / n_s)

    #-Return
    #-return r_n and n_s
    return r_n, n_s

########
# main #
########

def main():

    ##################
    # initialization #
    ##################

    # dummy variable name and missing value identifier
    dummyvariablename = 'dummy'
    missing_value = -999.9


    # define the file names of the maps to use as clone and the cell area (m2)
    clone_filename    = '/projects/0/dfguu/data/hydroworld/PCRGLOBWB20/input5min/routing/lddsound_05min.map'
    cellarea_filename = '/projects/0/dfguu/data/hydroworld/PCRGLOBWB20/input5min/routing/cellsize05min.correct.map'

    # years to be analyzed
    startyear = 2001
    endyear   = 2010

    # types of irrigation and their alliases
    irrigation_types = { \
                        'paddy'    : 'irrPaddy', \
                        'nonpaddy' : 'irrNonPaddy', \
                       }

    # irrigated areas; give the conversion factor to bring it to m2
    irrig_efficiency_filename = '/projects/0/dfguu/data/hydroworld/PCRGLOBWB20/input30min/landSurface/waterDemand/efficiency/efficiency.map'
    irrig_area_factor         = 1.0e4
    irrig_area_path           = '/scratch-shared/edwindql/irrigated_areas_aqueduct_historical/'
    irrig_area_files          = {'paddy'    : os.path.join(irrig_area_path, \
                                              'paddy_irrigated_areas_historical_1960-2019_hectar.nc'),\
                                 'nonpaddy' : os.path.join(irrig_area_path, \
                                              'non_paddy_irrigated_areas_historical_1960-2019_hectar.nc')}

    # crop factors - monthly phenology
    crop_factor_climatology = True
    crop_factor_path        = '/projects/0/dfguu/users/edwin/data/joyce_land_cover_parameters/05min/hyde_5min_1900'
    crop_factor_files       = {'paddy'    : os.path.join(crop_factor_path, \
                                              'cropCoefficient_paddy.nc'),\
                               'nonpaddy' : os.path.join(crop_factor_path, \
                                              'cropCoefficient_non_paddy_crops.nc')}

    # kc_min to identify the fraction of bare soil evaporation and
    # to denote the start and end of the growing season
    kc_min = 0.20

    # file of the monthly potential evaporation
    pot_evap_fileroot   = '/scratch-shared/rens/aqueduct_comparison/aqueduct3/referencePotET_PenmanMonteith_1979-2012.nc'
    pot_evap_filesuffix = '_%d-01-31_to_%d-12-31'

    # file of the monthly actual evaporation over the irrigated area
    act_evap_monthly    = False
    act_evap_fileroot   = '/scratch-shared/rens/aqueduct_comparison/aqueduct3/evaporation_from_irrigation_annuaTot_output.nc'
    act_evap_filesuffix = '_%d-01-31_to_%d-12-31'

    ##########
    # output #
    ##########

    # output path
    outputpath = '/scratch-shared/rens/aqueduct_comparison/aqueduct3'
    if not os.path.isdir(outputpath): os.makedirs(outputpath)

    # ******************
    # * model products *
    # ******************
    # define the model products, set the settings to create the netCDF files
    # and initialize the netCDF files

    # *********************
    # * netCDF attributes *
    # *********************
    ncattributes= {}
    ncattributes['history']= 'created on %s.' % (datetime.datetime.now())

    # model products that are written in the approprate places
    # in the dynamic section
    # full_report lists additional variables that can be reported
    modelproducts= {}

    # total irrigation water demand
    variablename= 'irrigation_demand_total'
    modelproducts[variablename]= {}
    modelproducts[variablename]['alias']= variablename
    modelproducts[variablename]['conversionfactor']= 1.00
    modelproducts[variablename]['unit']= 'm3/year'
    modelproducts[variablename]['filename']= os.path.join(\
        outputpath, '%s.nc' % variablename.lower())

    # irrigation water demand over growing season
    variablename= 'irrigation_demand_growing_season'
    modelproducts[variablename]= {}
    modelproducts[variablename]['alias']= variablename
    modelproducts[variablename]['conversionfactor']= 1.00
    modelproducts[variablename]['unit']= 'm3/year'
    modelproducts[variablename]['filename']= os.path.join(\
        outputpath, '%s.nc' % variablename.lower())

    # total irrigation water supply
    variablename= 'irrigation_supply_total'
    modelproducts[variablename]= {}
    modelproducts[variablename]['alias']= variablename
    modelproducts[variablename]['conversionfactor']= 1.00
    modelproducts[variablename]['unit']= 'm3/year'
    modelproducts[variablename]['filename']= os.path.join(\
        outputpath, '%s.nc' % variablename.lower())

    # irrigation water supply over growing season
    variablename= 'irrigation_supply_growing_season'
    modelproducts[variablename]= {}
    modelproducts[variablename]['alias']= variablename
    modelproducts[variablename]['conversionfactor']= 1.00
    modelproducts[variablename]['unit']= 'm3/year'
    modelproducts[variablename]['filename']= os.path.join(\
        outputpath, '%s.nc' % variablename.lower())


    ##############
    # Processing #
    ##############

    ###########
    # initial #
    ###########

    # echo to screen
    print (' * Processing the irrigation water demand *'.upper())

    # set the years
    years = range(startyear, endyear + 1)

    # Set the clone on the basis of the spatial attributes of the clone map
    cloneattributes= spatialAttributes(clone_filename)
    setClone(cloneattributes)

    #########################
    # initialize the output #
    #########################
    # resolution, number of rows and columns
    productResolution, scale_division = recast_real_as_natural_ratio(\
            cloneattributes.xResolution)
    number_rows= (cloneattributes.yUR - cloneattributes.yLL + \
        0.5 * productResolution) // productResolution
    number_cols= (cloneattributes.xUR - cloneattributes.xLL + \
        0.5 * productResolution) // productResolution

    # set latitudes and longitudes
    latitudes =  -np.arange(number_rows) /\
        scale_division + cloneattributes.yUR - 0.5 * productResolution
    longitudes =  np.arange(number_cols) /\
        scale_division + cloneattributes.xLL + 0.5 * productResolution

    # initialize the netCDF files
    print (' * initializing the netCDF output files:')
    for variablename in modelproducts.keys():
        # initialize the netCDF output

        variablelongname= variablename
        createNetCDF(modelproducts[variablename]['filename'], \
            longitudes, latitudes, 'longitude', 'latitude', 'time',\
            modelproducts[variablename]['alias'], modelproducts[variablename]['unit'],\
            missing_value, ncattributes, varLongName= variablelongname)

        print (' - %s initialized' % modelproducts[variablename]['filename'])

    ##################
    # read the input #
    ##################
    # get the land mask
    landmask = pcr.defined(pcr.readmap(clone_filename))

    # get the cell area
    cellarea = pcr.cover(getattr(spatialDataSet(dummyvariablename,\
        cellarea_filename, 'FLOAT32', 'Scalar',\
        cloneattributes.xLL, cloneattributes.xUR, cloneattributes.yLL, cloneattributes.yUR,\
        cloneattributes.xResolution, cloneattributes.yResolution,\
        pixels= cloneattributes.numberCols, lines= cloneattributes.numberRows), dummyvariablename), 0)

    # set the default year
    defaultyear = startyear

    # initialize the crop factors
    crop_factor = {}

    ###########
    # dynamic #
    ###########
    # iterate over the years
    for year in years:

        nc_date_info = {}

        # initialize the potential evaporation
        # and the actual evaporation per year as a total and
        # for the growing season in units of [m3 / m2/ year]
        irrig_demand_total   = pcr.ifthen(landmask, pcr.scalar(0))
        irrig_demand_growing = pcr.ifthen(landmask, pcr.scalar(0))
        irrig_supply_total   = pcr.ifthen(landmask, pcr.scalar(0))
        irrig_supply_growing = pcr.ifthen(landmask, pcr.scalar(0))

        # set the evaporation files
        if '%s' in pot_evap_fileroot:
            pot_evap_filename = pot_evap_fileroot % \
                (pot_evap_filesuffix % (year, year))
        else:
            pot_evap_filename = pot_evap_fileroot

        if '%s' in act_evap_fileroot:
            act_evap_filename = act_evap_fileroot % \
                (act_evap_filesuffix % (year, year))
        else:
            act_evap_filename = act_evap_fileroot

        # add the information on the dates
        # dates for fixed files
        nc_date_info[pot_evap_filename]         = getNCDates(pot_evap_filename)
        nc_date_info[act_evap_filename]         = getNCDates(act_evap_filename)

        # dates for files dependent on irrigation type: area
        for irrigation_type, nc_filename in irrig_area_files.items():
            nc_date_info[nc_filename] = getNCDates(nc_filename)

        # dates for files dependent on irrigation type: crop factor
        for irrigation_type, nc_filename in crop_factor_files.items():
            nc_date_info[nc_filename] = getNCDates(nc_filename)

        # efficiency is not necessarily a timed nc file, so deal with this
        try:
            nc_date_info[irrig_efficiency_filename] = getNCDates(irrig_efficiency_filename)
        except:
            nc_date_info[irrig_efficiency_filename] = np.array([datetime.datetime(defaultyear, 1, 1)])
        efficiency = None

        # iterate over the months
        for month in range(1, 13):

            # set the dates
            date    = datetime.datetime(year,        month, 1)
            defdate = datetime.datetime(defaultyear, month, 1)

            # echo to screen
            print (' * processing %s' % date)

            # if the effiency is a timed nc file, read as intended,
            # otherwise, if the date is the default date and the
            # efficiency is not known,
            # read the value, otherwise, keep the value
            message_str = None
            if nc_date_info[irrig_efficiency_filename].size > 1:
                efficiency, returned_date, message_str= \
                getTimedPCRData(irrig_efficiency_filename,\
                    nc_date_info[irrig_efficiency_filename], \
                    date, dateSelectionMethod= 'nearest',\
                    dataAttributes= cloneattributes)
            elif isinstance(efficiency, NoneType):
                    
                efficiency, returned_date, message_str= \
                getTimedPCRData(irrig_efficiency_filename,\
                    nc_date_info[irrig_efficiency_filename], \
                    defdate, dateSelectionMethod= 'nearest',\
                    dataAttributes= cloneattributes)
#~                 else:
#~                     efficiency = pcr.cover(getattr(spatialDataSet(dummyvariablename,\
#~                         irrig_efficiency_filename, 'FLOAT32', 'Scalar',\
#~                         cloneattributes.xLL, cloneattributes.xUR, cloneattributes.yLL, cloneattributes.yUR,\
#~                         cloneattributes.xResolution, cloneattributes.yResolution,\
#~                         pixels= cloneattributes.numberCols, lines= cloneattributes.numberRows, test = True), dummyvariablename), 0)
            else:
                pass
            # print the message string
            if not isinstance(message_str, NoneType):
                print (str.join(' ', \
                    (' - irrigation efficiency read', message_str)))

            # get the crop factors per irrigation type
            # the monthly value to be used is stored as the actual value and added
            # to the climatology if this is used
            for irrigation_type, nc_filename in crop_factor_files.items():
                if irrigation_type not in crop_factor.keys():
                    crop_factor[irrigation_type] = {}

                # if the climatology has to be used, fill the values first
                if (crop_factor_climatology and date == defdate) or \
                         not crop_factor_climatology:

                    # read in the crop factor
                    value , returned_date, message_str= \
                        getTimedPCRData(nc_filename,\
                            nc_date_info[nc_filename], \
                            date, dateSelectionMethod= 'exact',\
                            dataAttributes= cloneattributes,
                            allowYearSubstitution = crop_factor_climatology)
                    # add the date to the dictionary
                    crop_factor[irrigation_type][date] = value

                    # print the message string
                    print (str.join(' ', \
                        (' - %s crop factor read' % irrigation_type, \
                         message_str)))

                # set the value to use
                if crop_factor_climatology:

                    # get the value using the default date
                    crop_factor[irrigation_type]['actual'] = crop_factor[irrigation_type][defdate]

                else:

                    # get the value and remove the date
                    crop_factor[irrigation_type]['actual'] = crop_factor[irrigation_type][date]

                    # cut the crap - remove the value
                    crop_factor[irrigation_type].remove(date)

            # read in the irrigation area per irrigation type
            irrig_area = {}
            irrig_area['total'] = pcr.scalar(0)
            for irrigation_type, nc_filename in irrig_area_files.items():

                # read in the crop factor
                value, returned_date, message_str= \
                        getTimedPCRData(nc_filename,\
                            nc_date_info[nc_filename], \
                            date, dateSelectionMethod= 'exact',\
                            dataAttributes= cloneattributes)
                # set the value
                irrig_area[irrigation_type] = irrig_area_factor * value
                irrig_area['total'] = irrig_area['total']  + irrig_area[irrigation_type]

                # print the message string
                print (str.join(' ', \
                    (' - %s irrigated area read' % irrigation_type, \
                     message_str)))

            # get the potential evaporation
            pot_evap, returned_date, message_str= \
                getTimedPCRData(pot_evap_filename,\
                    nc_date_info[pot_evap_filename], \
                    date, dateSelectionMethod= 'after',\
                    dataAttributes= cloneattributes)
            print (str.join(' ', \
                (' - potential evaporation read', message_str)))

            # get the actual evaporation
            if act_evap_monthly:
                act_evap, returned_date, message_str= \
                    getTimedPCRData(act_evap_filename,\
                        nc_date_info[act_evap_filename], \
                        date, dateSelectionMethod= 'after',\
                        dataAttributes= cloneattributes)
                print (str.join(' ', \
                    (' - actual evaporation read', message_str)))

            # all relevant values are read, compute the irrigation water demand
            # for the irrigation type
            growing_season_total = pcr.boolean(0)
            for irrigation_type, irrigation_type_alias in irrigation_types.items():

                # print the message string
                message_str = ' - computing the %s irrigation water demand' % irrigation_type
                print (message_str)

                # compute the flux: kc x pet x area / efficiency
                irrigation_demand = crop_factor[irrigation_type]['actual'] * \
                                          pot_evap * irrig_area[irrigation_type] / \
                                          efficiency

                # is this in the growing season?
                growing_season       = crop_factor[irrigation_type]['actual'] > kc_min
                growing_season_total = growing_season_total | growing_season

                # update the totals
                irrig_demand_total   = irrig_demand_total   + irrigation_demand
                irrig_demand_growing = irrig_demand_growing + pcr.ifthenelse( growing_season, \
                                                          irrigation_demand, 0)

            # get the actual evaporation if specified
            if act_evap_monthly:

                # print the message string
                message_str = ' - computing the irrigation total supply'
                print (message_str)

                # compute the irrigation total supply
#~                 irrigation_total_supply = act_evap * irrig_area['total']
                irrigation_total_supply = act_evap * cellarea / efficiency

                # update the totals
                irrig_supply_total   = irrig_supply_total   + irrigation_total_supply
                irrig_supply_growing = irrig_supply_growing + pcr.ifthenelse(growing_season_total, \
                                                          irrigation_total_supply, 0)

        # yearly totals are complete, unless the actual evaporation
        # is supplied on an annual basis
        if not act_evap_monthly:

            # set the date, standard PCR-GLOBWB output is set to the
            # last day of the year
            firstdate = datetime.datetime(year,  1, 1)
            lastdate  = datetime.datetime(year, 12, 31)

            # set the date_selection_method
            date_selection_method = 'exact'
            if   lastdate in nc_date_info[act_evap_filename]:
                    date = lastdate
            elif firstdate in nc_date_info[act_evap_filename]:
                date = firstdate
            else:
                date_selection_method = 'nearest'

            act_evap, returned_date, message_str= \
                getTimedPCRData(act_evap_filename,\
                    nc_date_info[act_evap_filename], \
                    date, dateSelectionMethod= 'after',\
                    dataAttributes= cloneattributes)
            print (str.join(' ', \
                (' - actual evaporation read', message_str)))

            # print the message string
            message_str = ' - computing the irrigation total supply'
            print (message_str)

            # compute the irrigation total supply
#~             irrigation_total_supply = act_evap * irrig_area['total']
            irrigation_total_supply = act_evap * cellarea / efficiency

            # update the totals
            growing_season_total = pcr.boolean(1)
            irrig_supply_total       = irrig_supply_total   + irrigation_total_supply
            irrig_supply_growing     = irrig_supply_growing + pcr.ifthenelse(growing_season_total, \
                                                      irrigation_total_supply, 0)

        ##################
        # write output   #
        # to netCDF file #
        ##################
        date = datetime.datetime(year,  1, 1)
        poscnt = years.index(year)

        # iterate over the output
        for variablename, variabledata in { \
                          'irrigation_demand_total'          : irrig_demand_total, \
                          'irrigation_demand_growing_season' : irrig_demand_growing, \
                          'irrigation_supply_total'          : irrig_supply_total, \
                          'irrigation_supply_growing_season' : irrig_supply_growing}.items():
                       
            # echo to screen
            print (' - writing info on %s to netCDF file for %s' % \
                    (variablename, date))

            # write to netCDF
            writeField(modelproducts[variablename]['filename'], \
                    pcr.pcr2numpy(variabledata, missing_value), \
                    modelproducts[variablename]['alias'],\
                    date, poscnt, 'time', missing_value)

    # all done
    print (' * all information on the irrigation water demand and supply written')


#######
# main#
#######

if __name__ == "__main__":

    main()
