#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import datetime

import pcraster as pcr
from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

# time object
from currTimeStep import ModelTime

from outputNetcdf import OutputNetcdf
import virtualOS as vos

import logging
logger = logging.getLogger(__name__)

class CalcFramework(DynamicModel):

    def __init__(self, cloneMapFileName,\
                       modelTime, \
                       input_files, \
                       output_files
                       ):
        DynamicModel.__init__(self)
        
        # set the clone map
        self.cloneMapFileName = cloneMapFileName
        pcr.setclone(self.cloneMapFileName)
        
        # time variable/object
        self.modelTime = modelTime
        
        # a dictionary containing input files
        self.input_files = input_files
        
        # a dictionary containing output files
        self.output_files  = output_files 
        self.output_folder = self.output_files["folder"]
        
        # prepare temporary directory
        self.tmpDir = self.output_folder + "/tmp/"
        try:
            os.makedirs(self.tmpDir)
        except:
            os.system('rm -r '+tmpDir+"/*")
        
        # cell area (m2)
        self.cell_area_total = vos.readPCRmapClone(v = self.input_files["cell_area"], \
                                                   cloneMapFileName = self.cloneMapFileName, \
                                                   tmpDir = self.tmpDir
                                                   )
        
        # nonpaddy and paddy fractions - unit: m2.m-2 
        nonpaddy_fraction = vos.readPCRmapClone(v = self.input_files["nonpaddy_fraction"], \
                                                cloneMapFileName = self.cloneMapFileName, \
                                                tmpDir = self.tmpDir)
        paddy_fraction    = vos.readPCRmapClone(v = self.input_files["paddy_fraction"], \
                                                cloneMapFileName = self.cloneMapFileName, \
                                                tmpDir = self.tmpDir)
        # for cells with irrigated areas, their paddy and nonpaddy fractions/distributions are calculated as the following
        # paddy fraction over irrigated area only - unit: m2.m-2
        self.paddy_fraction_over_irrigated_area    = pcr.ifthenelse(nonpaddy_fraction + paddy_fraction > 0.0, paddy_fraction / (nonpaddy_fraction + paddy_fraction), 0.0)                                   
        self.paddy_fraction_over_irrigated_area    = pcr.min(1.0, self.paddy_fraction_over_irrigated_area)
        # nonpaddy fraction over irrigated area only - unit: m2.m-2
        self.nonpaddy_fraction_over_irrigated_area = pcr.max(0.0, 1.0 - self.paddy_fraction_over_irrigated_area)                                   
        
        # object for reporting
        self.netcdf_report = OutputNetcdf(mapattr_dict = None,\
                                          cloneMapFileName = cloneMapFileName,\
                                          netcdf_format = "NETCDF4",\
                                          netcdf_zlib = False,\
                                          netcdf_attribute_dict = None,)       

        
    def initial(self): 

        # general attributes for netcdf output files
        attributeDictionary = {}
        attributeDictionary['institution']   = "Department of Physical Geography, Utrecht University, the Netherlands"
        attributeDictionary['history'    ]   = "Files are created by Edwin H. Sutanudjaja on " + str(datetime.datetime.now())
        attributeDictionary['references' ]   = "See description."
        attributeDictionary['source'     ]   = "See description."
        attributeDictionary['comment'    ]   = "See description. Calculated on the folder " + str(self.output_files["folder"]) 
        attributeDictionary['disclaimer' ]   = "Great care was exerted to prepare these data. Notwithstanding, use of the model and/or its outcome is the sole responsibility of the user." 

        # make a netcdf output file for monthly estimate irrigation demand
        attributeDictionary['title'      ]   = "Monthly estimate irrigation demand (km3/month)."
        attributeDictionary['description']   = "The files are created based on the 5 arcmin PCR-GLOBWB runs for the project WRI (World Resources Institute) Aqueduct 2021. "
        self.netcdf_report.createNetCDF(self.output_files["estimate_irrigation_demand"],\
                                        "estimate_irrigation_demand",\
                                        "km3.month-1",\
                                        "estimate_irrigation_demand",\
                                        attributeDictionary)

    def dynamic(self):
        
        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())


        # read yearly irrigated area (input files are originally in hectar and here converted to m2)
        if self.modelTime.doy == 1:
            
            irrigated_area_in_hectar = pcr.cover(
                                       vos.netcdf2PCRobjClone(ncFile            = self.input_files["irrigated_area_in_hectar"],\
                                                              varName           = "automatic",\
                                                              dateInput         = self.modelTime.fulldate,\
                                                              useDoy            = None,\
                                                              cloneMapFileName  = self.cloneMapFileName), 
                                                0.0)
            # irrigated area in m2
            self.irrigated_area     = irrigated_area_in_hectar * 10000.
        
            # nonpaddy cell area (m2)
            self.cell_area_nonpaddy = self.irrigated_area * self.nonpaddy_fraction_over_irrigated_area

            # paddy cell area (m2)
            self.cell_area_paddy    = self.irrigated_area * self.paddy_fraction_over_irrigated_area
        

        # read efficiency - dimensionless
        if self.modelTime.doy == 1:

            self.efficiency = vos.readPCRmapClone(v = self.input_files["efficiency"], \
                                                    cloneMapFileName = self.cloneMapFileName, \
                                                    tmpDir = self.tmpDir)

            # extrapolate efficiency map as done in PCR-GLOBWB 
            window_size = 1.25 * pcr.clone().cellSize()
            window_size = min(window_size, min(pcr.clone().nrRows(), pcr.clone().nrCols())*pcr.clone().cellSize())
            try:
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, window_size))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, window_size))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, window_size))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, window_size))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, window_size))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, 0.75))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, 1.00))
                self.efficiency = pcr.cover(self.efficiency, pcr.windowaverage(self.efficiency, 1.50))
            except:
                pass
            self.efficiency = pcr.cover(self.efficiency, 1.0)
            self.efficiency = pcr.max(0.1, self.efficiency)


        # get crop coefficient values (daily) for nonpaddy and paddy - dimensionless
        self.kc_nonpaddy_daily     = pcr.cover(
                                               vos.netcdf2PCRobjClone(ncFile            = self.input_files["kc_nonpaddy_daily"],\
                                                                      varName           = "automatic",\
                                                                      dateInput         = self.modelTime.fulldate,\
                                                                      useDoy            = "daily_seasonal",\
                                                                      cloneMapFileName  = self.cloneMapFileName), 
                                               0.0)
        self.kc_paddy_daily        = pcr.cover(
                                               vos.netcdf2PCRobjClone(ncFile            = self.input_files["kc_paddy_daily"],\
                                                                      varName           = "automatic",\
                                                                      dateInput         = self.modelTime.fulldate,\
                                                                      useDoy            = "daily_seasonal",\
                                                                      cloneMapFileName  = self.cloneMapFileName), 
                                               0.0)
        # set minimum kc - as used in PCR-GLOBWB runs
        minimum_kc = 0.2
        self.kc_nonpaddy_daily = pcr.max(minimum_kc, self.kc_nonpaddy_daily)
        self.kc_paddy_daily    = pcr.max(minimum_kc, self.kc_paddy_daily)


        # get reference potential evaporation (daily) - unit: m/day
        if self.modelTime.day == 1:
            try:
                self.et0_file = self.input_files["et0"] % (str(self.modelTime.year), str(self.modelTime.year))
            except:
                self.et0_file = self.input_files["et0"]
        self.et0 = vos.netcdf2PCRobjClone(ncFile            = self.et0_file,\
                                          varName           = "automatic",\
                                          dateInput         = self.modelTime.fulldate,\
                                          useDoy            = None,\
                                          cloneMapFileName  = self.cloneMapFileName)


        # calculate crop requirement (still not including efficiency) for irrigated crops - calculated from potential evaporation
        # - daily value - m3.day-1
        self.crop_requirement_daily = self.kc_nonpaddy_daily * self.et0 * self.cell_area_nonpaddy +\
                                      self.kc_paddy_daily    * self.et0 * self.cell_area_paddy
        # - monthly aggregation - m3.month-1
        if self.modelTime.day == 1: self.crop_requirement_monthly = pcr.scalar(0.0)
        self.crop_requirement_monthly = self.crop_requirement_monthly + self.crop_requirement_daily
        
        # monthly irrigation requirement (including efficiency) - unit: km3/month - note this can be supplied by precipitation and irrigation withdrawal 
        if self.modelTime.isLastDayOfMonth():
            # m3.month-1
            self.irrigation_requirement = self.crop_requirement_monthly / self.efficiency
            # km3.month-1
            self.irrigation_requirement = self.irrigation_requirement / 1e9

        
        # get irrigation supply (km3/month): amount of water that has been withdrawn to meet irrigation demand (from PCR-GLOBWB output)
        if self.modelTime.isLastDayOfMonth():

            # read irrigation supply (the one that evaporated; note this is still not including efficiency) - unit: m/month
            
            self.evaporation_from_irrigation_file = self.input_files["evaporation_from_irrigation"] % (str(self.modelTime.year), str(self.modelTime.year)) 
            
            # - irrigation supply, but still not including efficiency - unit: m/month - note this consists the ones from precipitation and irrigation withdrawal
            self.irrigation_supply = vos.netcdf2PCRobjClone(ncFile            = self.evaporation_from_irrigation_file,\
                                                            varName           = "automatic",\
                                                            dateInput         = self.modelTime.fulldate,\
                                                            useDoy            = None,\
                                                            cloneMapFileName  = self.cloneMapFileName)

            # - irrigation supply corrected with efficiency - unit: km3/month
            self.irrigation_supply = self.irrigation_supply / self.efficiency * self.cell_area_total / 1e9

        
        # get irrigation withdrawal (km3/month): amount of water that has been withdrawn to meet irrigation demand (from PCR-GLOBWB output)
        if self.modelTime.isLastDayOfMonth():

            # unit: m.month-1
            self.irrigation_withdrawal_file = self.input_files["total_irrigation_withdrawal"] % (str(self.modelTime.year), str(self.modelTime.year))
            irrigation_withdrawal = vos.netcdf2PCRobjClone(ncFile            = self.irrigation_withdrawal_file,\
                                                           varName           = "automatic",\
                                                           dateInput         = self.modelTime.fulldate,\
                                                           useDoy            = None,\
                                                           cloneMapFileName  = self.cloneMapFileName)
            
            # total irrigation withdrawal (amount of water that has been supplied to meet irrigation demand) - unit: km3/month
            self.irrigation_withdrawal = irrigation_withdrawal * self.cell_area_total / 1e9


            # ~ # the following is for the case using irrNonPaddyWithdrawal and irrPaddyWithdrawal (yet, results will be the same as above)
            # ~ # irrNonPaddyWithdrawal (output from PCR-GLOBWB runs) - unit: m/month
            # ~ self.nonpaddy_irrigation_withdrawal_file = self.input_files["nonpaddy_irrigation_withdrawal"] % (str(self.modelTime.year), str(self.modelTime.year))
            # ~ self.irrNonPaddyWithdrawal = vos.netcdf2PCRobjClone(ncFile            = self.nonpaddy_irrigation_withdrawal_file,\
                                                                # ~ varName           = "automatic",\
                                                                # ~ dateInput         = self.modelTime.fulldate,\
                                                                # ~ useDoy            = None,\
                                                                # ~ cloneMapFileName  = self.cloneMapFileName)
            # ~ # irrPaddyWithdrawal (output from PCR-GLOBWB runs) - unit: m/month
            # ~ self.paddy_irrigation_withdrawal_file = self.input_files["paddy_irrigation_withdrawal"] % (str(self.modelTime.year), str(self.modelTime.year))
            # ~ self.irrPaddyWithdrawal    = vos.netcdf2PCRobjClone(ncFile            = self.paddy_irrigation_withdrawal_file,\
                                                                # ~ varName           = "automatic",\
                                                                # ~ dateInput         = self.modelTime.fulldate,\
                                                                # ~ useDoy            = None,\
                                                                # ~ cloneMapFileName  = self.cloneMapFileName)
            # ~ # total irrigation withdrawal (amount of water that has been supplied to meet irrigation demand) - unit: km3/month
            # ~ self.irrigation_withdrawal = (self.irrPaddyWithdrawal + self.irrNonPaddyWithdrawal) * self.cell_area_total / 1e9
            			

        # estimate monthly irrigation demand (km3/month)
        if self.modelTime.isLastDayOfMonth():
            
            # irrigation water gap - unit: km3.month-1
            self.irrigation_water_gap       = pcr.max(0.0, self.irrigation_requirement - self.irrigation_supply)
            
            # estimate monthly irrigation demand - unit: km3.month-1
            self.estimate_irrigation_demand = self.irrigation_withdrawal + self.irrigation_water_gap


        # save monthly irrigation demand and monthly irrigation requirement to files (km3/month)
        if self.modelTime.isLastDayOfMonth():


            # reporting
            timeStamp = datetime.datetime(self.modelTime.year,\
                                          self.modelTime.month,\
                                          self.modelTime.day,0)
            varFields = {}
            varFields["estimate_irrigation_demand"] = pcr.pcr2numpy(self.estimate_irrigation_demand, vos.MV)
            self.netcdf_report.dataList2NetCDF(self.output_files["estimate_irrigation_demand"],\
                                               ["estimate_irrigation_demand"],\
                                               varFields,\
                                               timeStamp)



def main():
    
    # ~ # use the following system arguments
    # ~ start_year                          = sys.argv[1]
    # ~ end_year                            = sys.argv[2]
    # ~ pcrglobwb_input_folder              = sys.argv[3]
    # ~ irrigated_area_in_hectar_input_file = sys.argv[4]
    # ~ pcrglobwb_monthly_output_folder     = sys.argv[5]
    # ~ pcrglobwb_daily_output_folder       = sys.argv[6]
    # ~ output_folder_for_irrigation_demand = sys.argv[7]
    # ~ output_file_for_irrigation_demand   = sys.argv[8]
    
    # ~ # starting and end date
    # ~ startDate = "%s-01-01" % (str(start_year))
    # ~ endDate   = "%s-12-31" % (str(end_year))

    startDate = "1960-01-01"
    endDate   = "2019-12-31"


    # a dictionary containing input files
    input_files = {}
    
    # input from PCR-GLOBWB INPUT files
    # - main folder of pcrglobwb input files 
    # ~ input_files["pgb_inp_dir"]     = str(pcrglobwb_input_folder) + "/"
    input_files["pgb_inp_dir"]         = "/projects/0/dfguu/users/edwin/data/pcrglobwb_input_aqueduct/version_2021-09-16/"
    
    # - clone map (-), cell area (m2)
    input_files["clone_map"]                    = input_files["pgb_inp_dir"] + "/general/cloneMaps/clone_global_05min.map"    
    input_files["cell_area"]                    = input_files["pgb_inp_dir"] + "/general/cdo_gridarea_clone_global_05min_correct_lats.nc"
    # - nonpaddy_fraction and paddy_fraction (notes that this the estimate over the entire cell area (m2.m-2)   
    input_files["nonpaddy_fraction"]            = input_files["pgb_inp_dir"] + "/general/fractionNonPaddy_extrapolated.map"    
    input_files["paddy_fraction"]               = input_files["pgb_inp_dir"] + "/general/fractionPaddy_extrapolated.map"
    # - nonpaddy and paddy kc (dimensionless)  
    input_files["kc_nonpaddy_daily"]            = input_files["pgb_inp_dir"] + "/general/nonpaddy_cropfactor_filled.nc"    
    input_files["kc_paddy_daily"]               = input_files["pgb_inp_dir"] + "/general/paddy_cropfactor_filled.nc"
    # - irrigation efficiency                   
    input_files["efficiency"]                   = input_files["pgb_inp_dir"] + "/general/efficiency.nc"
    # - irrigated_area_in_hectar 
    # ~ input_files["irrigated_area_in_hectar"] = input_files["pgb_inp_dir"] + "/%s" % (irrigated_area_in_hectar_input_file)
    input_files["irrigated_area_in_hectar"]     = input_files["pgb_inp_dir"] + "/historical_and_ssp_files/irrigated_areas_historical_1960-2019.nc"


    # input from PCR-GLOBWB run OUTPUT files
    # - main folder of pcrglobwb monthly input files 
    # ~ input_files["pgb_monthly_out_dir"]      = str(pcrglobwb_monthly_output_folder) + "/"
    input_files["pgb_monthly_out_dir"]          = "/projects/0/dfguu2/users/edwin/pcrglobwb_aqueduct_2021_monthly_annual_files/version_2021-09-16/gswp3-w5e5_rerun/historical-reference/begin_from_1960/global/netcdf/"
    
    # - monthly evaporation_from_irrigation (m.month-1) 
    input_files["evaporation_from_irrigation"]    = input_files["pgb_monthly_out_dir"] + "/evaporation_from_irrigation_monthTot_output_%4s-01-31_to_%4s-12-31.nc"

    # - monthly nonpaddy and paddy irrigation withdrawal (m.month-1) 
    # ~ input_files["nonpaddy_irrigation_withdrawal"] = input_files["pgb_monthly_out_dir"] + "/irrNonPaddyWaterWithdrawal_monthTot_output_%4s-01-31_to_%4s-12-31.nc"
    # ~ input_files["paddy_irrigation_withdrawal"]    = input_files["pgb_monthly_out_dir"] + "/irrPaddyWaterWithdrawal_monthTot_output_%4s-01-31_to_%4s-12-31.nc"
    # - if not available - we can also use its total withdrawal (m.month-1) - note the following does not include livestock
    input_files["total_irrigation_withdrawal"]    = input_files["pgb_monthly_out_dir"] + "/irrGrossDemand_monthTot_output_%4s-01-31_to_%4s-12-31.nc"

    # - daily reference potential evaporation (m.month-1) - note this may be given in a different folder than the monthly output folder
    # ~ input_files["pgb_daily_out_dir"] = str(pcrglobwb_daily_output_folder) + "/"
    # ~ input_files["et0"] = input_files["pgb_daily_out_dir"] + "referencePotET_dailyTot_output_%4s-01-01_to_%4s-12-31.nc"
    input_files["et0"]     = "/projects/0/dfguu2/users/edwin/pcrglobwb_aqueduct_2021_daily_files/version_2021-09-16/gswp3-w5e5_rerun/historical-reference/begin_from_1960/global/netcdf_merged_daily_1960-2019/referencePotET_dailyTot_output_1960-01-01_to_2019-12-31.nc"


    # a dictionary containing output files
    output_files = {}

    output_files["folder"]                        = "/scratch-shared/edwin/irrigation_demand_aqueduct/gswp3-w5e5_rerun/"
    output_files["estimate_irrigation_demand"]    = output_files["folder"] + "/estimateIrrigationDemandVolume_monthTot_output_1960-2019_km3_per_month_gswp3-w5e5_historical-reference.nc" 

    # ~ output_files["folder"]                            = str(output_folder_for_irrigation_demand) + "/"
    # ~ output_files["estimate_irrigation_demand"]        = output_files["folder"] + "/" + str(output_file_for_irrigation_demand)


    # make output folder
    output_folder = output_files["folder"]
    try:
        os.makedirs(output_folder)
    except:
        os.system('rm -r ' + output_folder + "/*") ### THIS IS DANGEROUS
        pass

    # prepare logger and its directory
    log_file_location = output_folder + "/log/"
    try:
        os.makedirs(log_file_location)
    except:
        cmd = 'rm -r ' + log_file_location + "/*"
        os.system(cmd)
        pass
    vos.initialize_logging(log_file_location)
    
    # time object
    modelTime = ModelTime() # timeStep info: year, month, day, doy, hour, etc
    modelTime.getStartEndTimeSteps(startDate, endDate)
    
    calculationModel = CalcFramework(input_files["clone_map"],\
                                     modelTime, \
                                     input_files, \
                                     output_files)

    dynamic_framework = DynamicFramework(calculationModel, modelTime.nrOfTimeSteps)
    dynamic_framework.setQuiet(True)
    dynamic_framework.run()

if __name__ == '__main__':
    sys.exit(main())
