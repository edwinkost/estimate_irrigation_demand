
python dynamic_calc_framework_for_estimating_irrigation_demand.py 1960 2014 /projects/0/dfguu/users/edwin/data/pcrglobwb_input_aqueduct/version_2021-09-16/ historical_and_ssp_files/irrigated_areas_historical_1960-2019.nc /projects/0/dfguu2/users/edwin/pcrglobwb_aqueduct_2021_monthly_annual_files/version_2021-09-16/gfdl-esm4/begin_from_1960/global/netcdf/ /scratch-shared/edwin/irrigation_demand_aqueduct_2021/version_2021-09-16/gfdl-esm4/historical estimateIrrigationDemandVolume_monthTot_output_1960-2014_km3_per_month_gfdl-esm4.nc

    # ~ start_year                          = sys.argv[1]
    # ~ end_year                            = sys.argv[2]
    # ~ pcrglobwb_input_folder              = sys.argv[3]
    # ~ irrigated_area_in_hectar_input_file = sys.argv[4]
    # ~ pcrglobwb_output_folder             = sys.argv[5]
    # ~ output_folder_for_irrigation_demand = sys.argv[6]
    # ~ output_file_for_irrigation_demand   = sys.argv[7]

# ~ edwin@tcn364:/home/edwin$ ls -lah /projects/0/dfguu2/users/edwin/pcrglobwb_aqueduct_2021_monthly_annual_files/version_2021-09-16/
# ~ total 4.5K
# ~ drwxr-sr-x 9 edwin qt23375 4.0K Jan 17 14:14 .
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Nov  2  2021 ..
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 00:28 gfdl-esm4
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Jan 12 14:09 gswp3-w5e5
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Jan 17 14:15 gswp3-w5e5_rerun
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 00:33 ipsl-cm6a-lr
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 00:38 mpi-esm1-2-hr
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 00:44 mri-esm2-0
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 01:02 ukesm1-0-ll

# ~ edwin@tcn364:/home/edwin$ ls -lah /projects/0/dfguu2/users/edwin/pcrglobwb_aqueduct_2021_monthly_annual_files/version_2021-09-16/gfdl-esm4/
# ~ total 3.0K
# ~ drwxr-sr-x 6 edwin qt23375 4.0K Dec 21 00:28 .
# ~ drwxr-sr-x 9 edwin qt23375 4.0K Jan 17 14:14 ..
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Nov  2  2021 historical
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Dec 20 22:55 ssp126
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Nov  2  2021 ssp370
# ~ drwxr-sr-x 3 edwin qt23375 4.0K Dec 21 00:28 ssp585
