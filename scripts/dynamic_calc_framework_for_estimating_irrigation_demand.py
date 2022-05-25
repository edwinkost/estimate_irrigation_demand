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
        
        # object for reporting
        self.netcdf_report = OutputNetcdf(mapattr_dict = None,\
                                          cloneMapFileName = cloneMapFileName,\
                                          netcdf_format = "NETCDF4",\
                                          netcdf_zlib = False,\
                                          netcdf_attribute_dict = None,)       

        
    def initial(self): 

        # general attributes for netcdf files
        attributeDictionary = {}
        attributeDictionary['institution']   = "Department of Physical Geography, Utrecht University, the Netherlands"
        attributeDictionary['history'    ]   = "Files are created by Edwin H. Sutanudjaja on " + str(datetime.datetime.now())
        attributeDictionary['references' ]   = "See description."
        attributeDictionary['source'     ]   = "See description."
        attributeDictionary['comment'    ]   = "See description."
        attributeDictionary['disclaimer' ]   = "Great care was exerted to prepare these data. Notwithstanding, use of the model and/or its outcome is the sole responsibility of the user." 

        # make a netcdf file for yearly irrigation areas
        attributeDictionary['title'      ]   = "Monthly estimate irrigation demand (km3/month)."
        attributeDictionary['description']   = "The files are created based on the 5 arcmin PCR-GLOBWB runs for the Aqueduct project 2021. "
        self.output_files["estimate_irrigation_demand"] = self.output_folder + self.output_files["irrigated_areas"]
        self.netcdf_report.createNetCDF(self.output_files["estimate_irrigation_demand"],\
                                        "estimate_irrigation_demand",\
                                        "km3",\
                                        "estimate_irrigation_demand",\
                                        attributeDictionary)

    def dynamic(self):
        
        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())
        

        # nonpaddy cell area (m2)
        self.cell_area_nonpaddy = 

        # paddy cell area (m2)
        self.cell_area_paddy    = 
        

        
        # get crop coefficient values (daily) for nonpaddy and calculate its monthly average values - dimensionless
        self.kc_nonpaddy_daily     = 
        # - monthly aggregation 
        if self.modelTime.day == 1: self.kc_nonpaddy_monthly_agg = pcr.scalar(0.0)
        self.kc_nonpaddy_monthly_agg += self.kc_nonpaddy_daily
        # - monthly average values
        if self.modelTime.isLastDayOfMonth():
            self.kc_nonpaddy_monthly_average = self.kc_nonpaddy_monthly_agg / self.modelTime.day
        
        # get crop coefficient values (daily) for paddy and calculate its monthly average values - dimensionless
        self.kc_paddy_daily = 
        
        
        # get monthly reference potential evaporation - unit: m/month
        if self.modelTime.isLastDayOfMonth():
            self.et0 = 

        # read efficiency - dimensionless
        self.efficiency = 

        # calculate monthly irrigation water requirement (still not corrected by precipitation) - unit: km3/month
        if self.modelTime.isLastDayOfMonth():

            # crop requirement (still not including efficiency) - unit: m3/month
            self.crop_requirement = self.kc_nonpaddy_monthly_average * self.et0 * self.cell_area_nonpaddy +\
                                          self.kc_paddy_monthly_average * self.et0 * self.cell_area_paddy
            # - km3/month
            self.crop_requirement = self.crop_requirement / 1e9

            # irrigation requirement (including efficiency) - unit: km3/month
            self.irrigation_requirement = self.crop_requirement / self.efficiency

        
        # get irrigation supply (km3/month): amount of water that has been withdrawn to meet irrigation demand (from PCR-GLOBWB output)
        if self.modelTime.isLastDayOfMonth():

            # ready irrigation supply, but still not including efficiency - unit: m/month
            self.irrigation_supply = 
            
            # irrigation supply corrected with efficiency - unit: km3/month
            self.irrigation_supply = self.irrigation_supply / self.efficiency * self.cell_area_total / 1e9

        
        # get irrigation withdrawal (km3/month): amount of water that has been withdrawn to meet irrigation demand (from PCR-GLOBWB output)
        if self.modelTime.isLastDayOfMonth():
            # irrPaddyWithdrawal + irrNonPaddyWithdrawal (output from PCR-GLOBWB runs) - unit: m/month
            self.irrPaddyWithdrawal    = 
            
            self.irrNonPaddyWithdrawal =
            
            # irrigation supply (amount of water that has been supplied to meet irrigation demand) - unit: km3/month
            self.irrigation_withdrawal = (self.irrPaddyWithdrawal + self.irrNonPaddyWithdrawal) * self.cell_area_total / 1e9
            			

        # estimate monthly irrigation demand (km3/month)
        if self.modelTime.isLastDayOfMonth():
            
            self.estimate_irrigation_demand = (self.irrigation_requirement - self.irrigation_supply) + self.irrigation_withdrawal


        # save monthly irrigation demand and monthly irrigation requirement to files (km3/month)
        if self.modelTime.isLastDayOfMonth():


            # reporting
            timeStamp = datetime.datetime(self.modelTime.year,\
                                          self.modelTime.month,\
                                          self.modelTime.day,0)
            varFields = {}
            varFields["industryGrossDemand"] = pcr.pcr2numpy(industry_gross_demand, vos.MV)
            varFields["industryNettoDemand"] = pcr.pcr2numpy(industry_netto_demand, vos.MV)
            self.netcdf_report.dataList2NetCDF(self.output_files["industry_water_demand"],\
                                               ["industryGrossDemand", "industryNettoDemand"],\
                                               varFields,\
                                               timeStamp)



def main():
    
    # starting and end date
    startDate = "1960-01-01"
    endDate   = "2100-12-31"
    
    # ~ # for testing
    # ~ startDate = "2005-01-01"
    # ~ endDate   = "2025-12-31"

    # a dictionary containing input files
    input_files = {}
    input_files["clone_map"]                  = "/scratch/depfg/sutan101/data/pcrglobwb_gmglob_input/develop/global_05min/cloneMaps/clone_global_05min.map"
    input_files["cell_area"]                  = "/scratch/depfg/sutan101/data/pcrglobwb_input_arise/develop/global_05min/routing/cell_area/cdo_gridarea_clone_global_05min_correct_lats.nc"
    
    # - irrigated areas
    input_files['gmd_paper_irrigation_areas'] = "/scratch/depfg/sutan101/data/pcrglobwb_input_arise/develop/global_05min_from_gmd_paper_input/waterUse/irrigation/irrigated_areas/irrigationArea05ArcMin.nc"
    input_files['hyde_irrigation_areas']      = "/scratch/depfg/sutan101/data/hyde3.2/downloaded_on_2021-08-11_baseline_only/baseline/zip_extracted_1800-2017/netcdf_irr/merged_annual/tot_irri_area_in_hectar_1800-2017_annual.nc"
    input_files['ssp_two_irrigation_areas']   = "/scratch/depfg/sutan101/data/landcover_glo1_parameters_from_rens_cartesius/irrigated_areas_calculated_by_edwin/ssp2/total_irrigation_areas_in_hectar_ssp2.nc"
    input_files['ssp_irrigation_areas']       = "/scratch/depfg/sutan101/data/landcover_glo1_parameters_from_rens_cartesius/irrigated_areas_calculated_by_edwin/ssp5/total_irrigation_areas_in_hectar_ssp5.nc"
    
    # - domestic demand
    input_files['glo1_domestic_demand']       = "/scratch/depfg/sutan101/data/water_demand_glo1/05min/historical/domestic_water_demand_1961_to_2014_in_m_per_day_05arcmin.nc"
    input_files['ssp_two_domestic_demand']    = "/scratch/depfg/sutan101/data/GLO1_rens/WaterDemand/water_demand_domestic_SSP2_2010-2099_5min.nc"
    input_files['ssp_domestic_demand']        = "/scratch/depfg/sutan101/data/GLO1_rens/WaterDemand/water_demand_domestic_SSP5_2010-2099_5min.nc"

    # - industry demand
    input_files['glo1_industry_demand']       = "/scratch/depfg/sutan101/data/water_demand_glo1/05min/historical/industrial_water_demand_1961_to_2014_in_m_per_day_05arcmin.nc"
    input_files['ssp_two_industry_demand']    = "/scratch/depfg/sutan101/data/GLO1_rens/WaterDemand/water_demand_industry_SSP2_2010-2099_5min.nc"
    input_files['ssp_industry_demand']        = "/scratch/depfg/sutan101/data/GLO1_rens/WaterDemand/water_demand_industry_SSP5_2010-2099_5min.nc"

    
    # a dictionary containing output files
    output_files = {}
    output_files["folder"]                = "/scratch/depfg/sutan101/aqueduct_irrigated_areas_and_water_demands/version_2021-09-13/ssp5/"
    output_files["irrigated_areas"]       = "irrigated_areas_historical_and_ssp5_1960-2100.nc"
    output_files["domestic_water_demand"] = "domestic_water_demand_historical_and_ssp5_1960-2100.nc"
    output_files["industry_water_demand"] = "industry_water_demand_historical_and_ssp5_1960-2100.nc"
    

    # make output folder
    output_folder = output_files["folder"]
    try:
        os.makedirs(output_folder)
    except:
        os.system('rm -r ' + output_folder + "/*")

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
