#!/bin/bash
#SBATCH -N 1
#SBATCH -n 96
#~ #SBATCH -t 240:00:00

#~ #SBATCH -p defq

#SBATCH -J irrd-ukesm1-0-ll

#SBATCH --exclusive

# mail alert at start, end and abortion of execution
#SBATCH --mail-type=ALL

# send mail to this address
#SBATCH --mail-user=edwinkost@gmail.com



# load all modules (software) needed
. /quanta1/home/sutan101/load_my_miniconda_and_my_default_env.sh

# use 24 cores (there are 4 processes in total, hence 96 cores will be used)
export PCRASTER_NR_WORKER_THREADS=24


# go to the script folder
cd /quanta1/home/sutan101/github/edwinkost/estimate_irrigation_demand/scripts/


PGB_INP_FOLDER="/scratch/depfg/sutan101/data/pcrglobwb_input_aqueduct/version_2021-09-16/"
PGB_MONTHLY_OUT_FOLDER="/scratch/depfg/sutan101/pcrglobwb_wri_aqueduct_2021/pcrglobwb_aqueduct_2021_monthly_annual_files/"
PGB_DAILY_OUT_FOLDER="/scratch/depfg/sutan101/pcrglobwb_wri_aqueduct_2021/pcrglobwb_aqueduct_2021_daily_files/"

IRR_DEMAND_OUTPUT_FOLDER="/scratch/depfg/sutan101/irrigation_demand_aqueduct_2021/"


# run the following scripts

# historical
python dynamic_calc_framework_for_estimating_irrigation_demand.py 1960 2014 ${PGB_INP_FOLDER} historical_and_ssp_files/irrigated_areas_historical_1960-2019.nc ${PGB_MONTHLY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/historical/begin_from_1960/global/netcdf/ ${PGB_DAILY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/historical/begin_from_1960/global/netcdf_daily/ ${IRR_DEMAND_OUTPUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/historical estimateIrrigationDemandVolume_monthTot_output_1960-2014_km3_per_month_ukesm1-0-ll_historical.nc &

# ssp126
python dynamic_calc_framework_for_estimating_irrigation_demand.py 2015 2100 ${PGB_INP_FOLDER} historical_and_ssp_files/irrigated_areas_ssp1_2000-2050.nc ${PGB_MONTHLY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp126/begin_from_2015/global/netcdf/ ${PGB_DAILY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp126/begin_from_2015/global/netcdf_daily/ ${IRR_DEMAND_OUTPUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp126 estimateIrrigationDemandVolume_monthTot_output_2015-2100_km3_per_month_ukesm1-0-ll_ssp126.nc &

# ssp370
python dynamic_calc_framework_for_estimating_irrigation_demand.py 2015 2100 ${PGB_INP_FOLDER} historical_and_ssp_files/irrigated_areas_ssp3_2000-2050.nc ${PGB_MONTHLY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp370/begin_from_2015/global/netcdf/ ${PGB_DAILY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp370/begin_from_2015/global/netcdf_daily/ ${IRR_DEMAND_OUTPUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp370 estimateIrrigationDemandVolume_monthTot_output_2015-2100_km3_per_month_ukesm1-0-ll_ssp370.nc &

# ssp585
python dynamic_calc_framework_for_estimating_irrigation_demand.py 2015 2100 ${PGB_INP_FOLDER} historical_and_ssp_files/irrigated_areas_ssp5_2000-2050.nc ${PGB_MONTHLY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp585/begin_from_2015/global/netcdf/ ${PGB_DAILY_OUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp585/begin_from_2015/global/netcdf_daily/ ${IRR_DEMAND_OUTPUT_FOLDER}/version_2021-09-16/ukesm1-0-ll/ssp585 estimateIrrigationDemandVolume_monthTot_output_2015-2100_km3_per_month_ukesm1-0-ll_ssp585.nc &

wait

