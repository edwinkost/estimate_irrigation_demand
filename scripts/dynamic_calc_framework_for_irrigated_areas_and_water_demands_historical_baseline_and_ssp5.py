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
        
        # maximum irrigated areas (based on cell area map at 5 arcmin resolution)
        cell_area = vos.readPCRmapClone(v = self.input_files["cell_area"], \
                                        cloneMapFileName = self.cloneMapFileName, \
                                        tmpDir = self.tmpDir
                                        )
        self.cell_area_in_hectar = cell_area / 10000.
        
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
        attributeDictionary['title'      ]   = "Yearly irrigation areas (hectar)"
        attributeDictionary['description']   = "For the years 1960-2010, the file was based on the irrigation area input file as used for the GMD paper run in Sutanudjaja et al. (2018). For the years 2011-2017, the file was extended with the HYDE 3.2 dataset (Klein Goldewijk et al., 2017). For the years 2018-2019, the file was extrapolated based on the SSP2 scenario (assumed to represent the current trend) of the GLO1 (Global Land Outlook, van der Esch et al., 2017). For the years after 2019, the SSP5 scenario file of GLO1 is used. The GLO1 files are obtained from Rens van Beek. A delta approach (additive) was used to synchronize various datasets during the merging. "
        self.output_files["irrigated_areas"] = self.output_folder + self.output_files["irrigated_areas"]
        self.netcdf_report.createNetCDF(self.output_files["irrigated_areas"],\
                                        "irrigationArea",\
                                        "hectar",\
                                        "irrigationArea",\
                                        attributeDictionary)

        # make a netcdf file for domestic water demand
        attributeDictionary['title'      ]   = "Monthly domestic water demand."
        attributeDictionary['description']   = "For the years 1960-2014, the file was based on the GLO1 (obtained from Rens van Beek). The original file was prepared by Edwin H. Sutanudjaja and Rens van Beek in February 2017. It was converted from water demand files provided by Yoshi Wada in February 2017. All original values have been converted to water slice. For the years 2015-2019, the file was extrapolated based on the SSP2 scenario (assumed to represent the current trend) of the (Global Land Outlook, van der Esch et al., 2017). For the years after 2019, the SSP5 scenario file of GLO1 was used (obtained from Rens van Beek). A delta approach (additive) was used to synchronize various datasets during the merging. "
        self.output_files["domestic_water_demand"] = self.output_folder + self.output_files["domestic_water_demand"]
        self.netcdf_report.createNetCDF(  self.output_files["domestic_water_demand"],\
                                          "domesticGrossDemand",\
                                          "m.day-1",\
                                          "domesticGrossDemand",\
                                          attributeDictionary)
        self.netcdf_report.addNewVariable(self.output_files["domestic_water_demand"],\
                                          "domesticNettoDemand", \
                                          "m.day-1",\
                                          "domesticNettoDemand")

        # make a netcdf file for industry water demand
        attributeDictionary['title'      ]   = "Monthly industrial water demand."
        attributeDictionary['description']   = "For the years 1960-2014, the file was based on the GLO1 (obtained from Rens van Beek). The original file was prepared by Edwin H. Sutanudjaja and Rens van Beek in February 2017. It was converted from water demand files provided by Yoshi Wada in February 2017. All original values have been converted to water slice. For the years 2015-2019, the file was extrapolated based on the SSP2 scenario (assumed to represent the current trend) of the (Global Land Outlook, van der Esch et al., 2017). For the years after 2019, the SSP5 scenario file of GLO1 was used (obtained from Rens van Beek). A delta approach (additive) was used to synchronize various datasets during the merging. "
        self.output_files["industry_water_demand"] = self.output_folder + self.output_files["industry_water_demand"]
        self.netcdf_report.createNetCDF(  self.output_files["industry_water_demand"],\
                                          "industryGrossDemand",\
                                          "m.day-1",\
                                          "industryGrossDemand",\
                                          attributeDictionary)
        self.netcdf_report.addNewVariable(self.output_files["industry_water_demand"],\
                                          "industryNettoDemand", \
                                          "m.day-1",\
                                          "industryNettoDemand")

    def dynamic(self):
        
        # re-calculate current model time using current pcraster timestep value
        self.modelTime.update(self.currentTimeStep())


        # irrigated_areas
        if self.modelTime.doy == 1:
            
            # using the gmd paper values for the years before 2011
            if self.modelTime.year <= 2010: 
                irrigated_areas_gmd = pcr.cover(
                                      vos.netcdf2PCRobjClone(ncFile            = self.input_files['gmd_paper_irrigation_areas'],\
                                                             varName           = "automatic",\
                                                             dateInput         = self.modelTime.fulldate,\
                                                             useDoy            = None,\
                                                             cloneMapFileName  = self.cloneMapFileName), 
                                                0.0)
                irrigated_areas     = irrigated_areas_gmd
                irrigated_areas     = pcr.min(pcr.max(0.0, irrigated_areas), self.cell_area_in_hectar)
        
            # expand irrigated areas with HYDE until 2017 (delta approach)
            if self.modelTime.year == 2010: 
                irrigated_areas_gmd_2010  = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['gmd_paper_irrigation_areas'],\
                                                                   varName           = "automatic",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = None,\
                                                                   cloneMapFileName  = self.cloneMapFileName), 
                                                      0.0)
                self.irrigated_areas_gmd_2010  = pcr.min(pcr.max(0.0, irrigated_areas_gmd_2010),  self.cell_area_in_hectar)
                irrigated_areas_hyde_2010 = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['hyde_irrigation_areas'],\
                                                                   varName           = "automatic",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = None,\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)
                self.irrigated_areas_hyde_2010 = pcr.min(pcr.max(0.0, irrigated_areas_hyde_2010), self.cell_area_in_hectar)
            
            if self.modelTime.year > 2010 and self.modelTime.year <= 2017:
                irrigated_areas_hyde = pcr.cover(
                                       vos.netcdf2PCRobjClone(ncFile            = self.input_files['hyde_irrigation_areas'],\
                                                              varName           = "automatic",\
                                                              dateInput         = self.modelTime.fulldate,\
                                                              useDoy            = None,\
                                                              cloneMapFileName  = self.cloneMapFileName),
                                                 0.0)
                irrigated_areas      = self.irrigated_areas_gmd_2010 + (irrigated_areas_hyde - self.irrigated_areas_hyde_2010)
                irrigated_areas      = pcr.min(pcr.max(0.0, irrigated_areas), self.cell_area_in_hectar)
                
            # expand irrigated areas with SSP TWO IMAGE to 2019
            if self.modelTime.year == 2017:
                self.irrigated_areas_2017     = irrigated_areas
                self.irrigated_areas_ssp_2017 = pcr.cover(
                                                vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_irrigation_areas'],\
                                                                       varName           = "automatic",\
                                                                       dateInput         = self.modelTime.fulldate,\
                                                                       useDoy            = None,\
                                                                       cloneMapFileName  = self.cloneMapFileName),
                                                          0.0)
            if self.modelTime.year > 2017 and self.modelTime.year <= 2019:
                irrigated_areas_ssp = pcr.cover(
                                      vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_irrigation_areas'],\
                                                             varName           = "automatic",\
                                                             dateInput         = self.modelTime.fulldate,\
                                                             useDoy            = None,\
                                                             cloneMapFileName  = self.cloneMapFileName),
                                                0.0)             
                irrigated_areas     = self.irrigated_areas_2017 + (irrigated_areas_ssp - self.irrigated_areas_ssp_2017)
                irrigated_areas     = pcr.min(pcr.max(0.0, irrigated_areas), self.cell_area_in_hectar)

            # expand irrigated areas with SSP5 after 2019
            if self.modelTime.year == 2019:
                self.irrigated_areas_2019     = irrigated_areas
                self.irrigated_areas_ssp_2019 = pcr.cover(
                                                vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_irrigation_areas'],\
                                                                       varName           = "automatic",\
                                                                       dateInput         = self.modelTime.fulldate,\
                                                                       useDoy            = None,\
                                                                       cloneMapFileName  = self.cloneMapFileName),
                                                          0.0)
            if self.modelTime.year > 2019:
                irrigated_areas_ssp = pcr.cover(
                                      vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_irrigation_areas'],\
                                                             varName           = "automatic",\
                                                             dateInput         = self.modelTime.fulldate,\
                                                             useDoy            = None,\
                                                             cloneMapFileName  = self.cloneMapFileName),
                                                0.0)             
                irrigated_areas     = self.irrigated_areas_2019 + (irrigated_areas_ssp - self.irrigated_areas_ssp_2019)
                irrigated_areas     = pcr.min(pcr.max(0.0, irrigated_areas), self.cell_area_in_hectar)

            # reporting
            timeStamp = datetime.datetime(self.modelTime.year,\
                                          self.modelTime.month,\
                                          self.modelTime.day,0)
            self.netcdf_report.data2NetCDF(self.output_files["irrigated_areas"],\
                                           "irrigationArea",\
                                           pcr.pcr2numpy(irrigated_areas, vos.MV),\
                                           timeStamp)
        
        # domestic water demand
        if self.modelTime.day == 1:
            
            # using the glo1 values for the years before 2015
            if self.modelTime.year < 2015: 
                
                domestic_netto_demand_glo1 = pcr.cover(
                                             vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_domestic_demand'],\
                                                                    varName           = "domesticNettoDemand",\
                                                                    dateInput         = self.modelTime.fulldate,\
                                                                    useDoy            = "monthly",\
                                                                    cloneMapFileName  = self.cloneMapFileName),
                                                       0.0)
                
                domestic_gross_demand_glo1 = pcr.cover(
                                             vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_domestic_demand'],\
                                                                    varName           = "domesticGrossDemand",\
                                                                    dateInput         = self.modelTime.fulldate,\
                                                                    useDoy            = "monthly",\
                                                                    cloneMapFileName  = self.cloneMapFileName),
                                                       0.0)
                
                domestic_netto_demand = pcr.max(0.0, domestic_netto_demand_glo1)
                domestic_gross_demand = pcr.max(domestic_netto_demand, domestic_gross_demand_glo1)

            # expand with the ssp two values of glo1 after 2015 (delta approach)
            if self.modelTime.year > 2014 and self.modelTime.year <= 2019: 

                # get the reference
                reference_date = "2014-%02i-01" %(self.modelTime.month) 
                
                domestic_netto_demand_glo1_2014 = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_domestic_demand'],\
                                                                         varName           = "domesticNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)
                
                domestic_gross_demand_glo1_2014 = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_domestic_demand'],\
                                                                         varName           = "domesticGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)            

                domestic_netto_demand_glo1_2014 = pcr.max(0.0, domestic_netto_demand_glo1_2014)
                domestic_gross_demand_glo1_2014 = pcr.max(domestic_netto_demand_glo1_2014, domestic_gross_demand_glo1_2014)
                
                domestic_netto_demand_ssp_2014  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_domestic_demand'],\
                                                                         varName           = "domesticNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             
                
                domestic_gross_demand_ssp_2014  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_domestic_demand'],\
                                                                         varName           = "domesticGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             

                domestic_netto_demand_ssp_2014 = pcr.max(0.0, domestic_netto_demand_ssp_2014)
                domestic_gross_demand_ssp_2014 = pcr.max(domestic_netto_demand_ssp_2014, domestic_gross_demand_ssp_2014)


                # expand with SSP TWO IMAGE
                domestic_netto_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_domestic_demand'],\
                                                                   varName           = "domesticNettoDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)

                domestic_gross_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_domestic_demand'],\
                                                                   varName           = "domesticGrossDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)             

                domestic_netto_demand_ssp = pcr.max(0.0, domestic_netto_demand_ssp)
                domestic_gross_demand_ssp = pcr.max(domestic_netto_demand_ssp, domestic_gross_demand_ssp)
                
                domestic_netto_demand = domestic_netto_demand_glo1_2014 + (domestic_netto_demand_ssp - domestic_netto_demand_ssp_2014)
                domestic_gross_demand = domestic_gross_demand_glo1_2014 + (domestic_gross_demand_ssp - domestic_gross_demand_ssp_2014)
                
                domestic_netto_demand = pcr.max(0.0, domestic_netto_demand)
                domestic_gross_demand = pcr.max(domestic_netto_demand, domestic_gross_demand)

            
            # save the reference values for the year 2019 for every month
            if self.modelTime.year == 2019:
                if self.modelTime.month == 1:
                    self.monthly_domestic_netto_demand = {}
                    self.monthly_domestic_gross_demand = {}
                self.monthly_domestic_netto_demand[self.modelTime.month] = domestic_netto_demand
                self.monthly_domestic_gross_demand[self.modelTime.month] = domestic_gross_demand
            

            # expand with the ssp values of glo1 after 2019 (delta approach)
            if self.modelTime.year > 2019: 

                # get the reference
                reference_date = "2019-%02i-01" %(self.modelTime.month) 
                
                domestic_netto_demand_2019 = self.monthly_domestic_netto_demand[self.modelTime.month]
                domestic_gross_demand_2019 = self.monthly_domestic_gross_demand[self.modelTime.month]            

                domestic_netto_demand_ssp_2019  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_domestic_demand'],\
                                                                         varName           = "domesticNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             
                
                domestic_gross_demand_ssp_2019  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_domestic_demand'],\
                                                                         varName           = "domesticGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             

                domestic_netto_demand_ssp_2019 = pcr.max(0.0, domestic_netto_demand_ssp_2019)
                domestic_gross_demand_ssp_2019 = pcr.max(domestic_netto_demand_ssp_2019, domestic_gross_demand_ssp_2019)


                # expand with SSP IMAGE
                domestic_netto_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_domestic_demand'],\
                                                                   varName           = "domesticNettoDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)

                domestic_gross_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_domestic_demand'],\
                                                                   varName           = "domesticGrossDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)             

                domestic_netto_demand_ssp = pcr.max(0.0, domestic_netto_demand_ssp)
                domestic_gross_demand_ssp = pcr.max(domestic_netto_demand_ssp, domestic_gross_demand_ssp)
                
                domestic_netto_demand = domestic_netto_demand_2019 + (domestic_netto_demand_ssp - domestic_netto_demand_ssp_2019)
                domestic_gross_demand = domestic_gross_demand_2019 + (domestic_gross_demand_ssp - domestic_gross_demand_ssp_2019)
                
                domestic_netto_demand = pcr.max(0.0, domestic_netto_demand)
                domestic_gross_demand = pcr.max(domestic_netto_demand, domestic_gross_demand)


            # make sure that gross demand is higher than netto
            domestic_netto_demand = pcr.max(0.0, domestic_netto_demand)
            domestic_gross_demand = pcr.max(domestic_netto_demand, domestic_gross_demand)
            
            # reporting
            timeStamp = datetime.datetime(self.modelTime.year,\
                                          self.modelTime.month,\
                                          self.modelTime.day,0)
            varFields = {}
            varFields["domesticGrossDemand"] = pcr.pcr2numpy(domestic_gross_demand, vos.MV)
            varFields["domesticNettoDemand"] = pcr.pcr2numpy(domestic_netto_demand, vos.MV)
            self.netcdf_report.dataList2NetCDF(self.output_files["domestic_water_demand"],\
                                               ["domesticGrossDemand", "domesticNettoDemand"],\
                                               varFields,\
                                               timeStamp)



        # industry water demand
        if self.modelTime.day == 1:
            
            # using the glo1 values for the years before 2015
            if self.modelTime.year < 2015: 
                
                industry_netto_demand_glo1 = pcr.cover(
                                             vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_industry_demand'],\
                                                                    varName           = "industryNettoDemand",\
                                                                    dateInput         = self.modelTime.fulldate,\
                                                                    useDoy            = "monthly",\
                                                                    cloneMapFileName  = self.cloneMapFileName),
                                                       0.0)
                
                industry_gross_demand_glo1 = pcr.cover(
                                             vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_industry_demand'],\
                                                                    varName           = "industryGrossDemand",\
                                                                    dateInput         = self.modelTime.fulldate,\
                                                                    useDoy            = "monthly",\
                                                                    cloneMapFileName  = self.cloneMapFileName),
                                                       0.0)
                
                industry_netto_demand = pcr.max(0.0, industry_netto_demand_glo1)
                industry_gross_demand = pcr.max(industry_netto_demand, industry_gross_demand_glo1)

            # expand with the ssp two values of glo1 after 2015 (delta approach)
            if self.modelTime.year > 2014 and self.modelTime.year <= 2019: 

                # get the reference
                reference_date = "2014-%02i-01" %(self.modelTime.month) 
                
                industry_netto_demand_glo1_2014 = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_industry_demand'],\
                                                                         varName           = "industryNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)
                
                industry_gross_demand_glo1_2014 = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['glo1_industry_demand'],\
                                                                         varName           = "industryGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)            

                industry_netto_demand_glo1_2014 = pcr.max(0.0, industry_netto_demand_glo1_2014)
                industry_gross_demand_glo1_2014 = pcr.max(industry_netto_demand_glo1_2014, industry_gross_demand_glo1_2014)
                
                industry_netto_demand_ssp_2014  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_industry_demand'],\
                                                                         varName           = "industryNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             
                
                industry_gross_demand_ssp_2014  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_industry_demand'],\
                                                                         varName           = "industryGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             

                industry_netto_demand_ssp_2014 = pcr.max(0.0, industry_netto_demand_ssp_2014)
                industry_gross_demand_ssp_2014 = pcr.max(industry_netto_demand_ssp_2014, industry_gross_demand_ssp_2014)


                # expand with SSP TWO IMAGE
                industry_netto_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_industry_demand'],\
                                                                   varName           = "industryNettoDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)

                industry_gross_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_two_industry_demand'],\
                                                                   varName           = "industryGrossDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)             

                industry_netto_demand_ssp = pcr.max(0.0, industry_netto_demand_ssp)
                industry_gross_demand_ssp = pcr.max(industry_netto_demand_ssp, industry_gross_demand_ssp)
                
                industry_netto_demand = industry_netto_demand_glo1_2014 + (industry_netto_demand_ssp - industry_netto_demand_ssp_2014)
                industry_gross_demand = industry_gross_demand_glo1_2014 + (industry_gross_demand_ssp - industry_gross_demand_ssp_2014)
                
                industry_netto_demand = pcr.max(0.0, industry_netto_demand)
                industry_gross_demand = pcr.max(industry_netto_demand, industry_gross_demand)

            
            # save the reference values for the year 2019 for every month
            if self.modelTime.year == 2019:
                if self.modelTime.month == 1:
                    self.monthly_industry_netto_demand = {}
                    self.monthly_industry_gross_demand = {}
                self.monthly_industry_netto_demand[self.modelTime.month] = industry_netto_demand
                self.monthly_industry_gross_demand[self.modelTime.month] = industry_gross_demand
            

            # expand with the ssp values of glo1 after 2019 (delta approach)
            if self.modelTime.year > 2019: 

                # get the reference
                reference_date = "2019-%02i-01" %(self.modelTime.month) 
                
                industry_netto_demand_2019 = self.monthly_industry_netto_demand[self.modelTime.month]
                industry_gross_demand_2019 = self.monthly_industry_gross_demand[self.modelTime.month]            

                industry_netto_demand_ssp_2019  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_industry_demand'],\
                                                                         varName           = "industryNettoDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             
                
                industry_gross_demand_ssp_2019  = pcr.cover(
                                                  vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_industry_demand'],\
                                                                         varName           = "industryGrossDemand",\
                                                                         dateInput         = reference_date,\
                                                                         useDoy            = "monthly",\
                                                                         cloneMapFileName  = self.cloneMapFileName),
                                                            0.0)             

                industry_netto_demand_ssp_2019 = pcr.max(0.0, industry_netto_demand_ssp_2019)
                industry_gross_demand_ssp_2019 = pcr.max(industry_netto_demand_ssp_2019, industry_gross_demand_ssp_2019)


                # expand with SSP IMAGE
                industry_netto_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_industry_demand'],\
                                                                   varName           = "industryNettoDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)

                industry_gross_demand_ssp = pcr.cover(
                                            vos.netcdf2PCRobjClone(ncFile            = self.input_files['ssp_industry_demand'],\
                                                                   varName           = "industryGrossDemand",\
                                                                   dateInput         = self.modelTime.fulldate,\
                                                                   useDoy            = "monthly",\
                                                                   cloneMapFileName  = self.cloneMapFileName),
                                                      0.0)             

                industry_netto_demand_ssp = pcr.max(0.0, industry_netto_demand_ssp)
                industry_gross_demand_ssp = pcr.max(industry_netto_demand_ssp, industry_gross_demand_ssp)
                
                industry_netto_demand = industry_netto_demand_2019 + (industry_netto_demand_ssp - industry_netto_demand_ssp_2019)
                industry_gross_demand = industry_gross_demand_2019 + (industry_gross_demand_ssp - industry_gross_demand_ssp_2019)
                
                industry_netto_demand = pcr.max(0.0, industry_netto_demand)
                industry_gross_demand = pcr.max(industry_netto_demand, industry_gross_demand)


            # make sure that gross demand is higher than netto
            industry_netto_demand = pcr.max(0.0, industry_netto_demand)
            industry_gross_demand = pcr.max(industry_netto_demand, industry_gross_demand)
            
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
