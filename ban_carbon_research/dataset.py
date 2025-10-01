from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.pandas as pa
import geopandas

from ban_carbon_research.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

def process_rggi_emissions_annual_facility():
    fname = "rggi-emissions-annual-facility.csv"
    df = pd.read_csv(RAW_DATA_DIR / fname)

    numeric_columns = [
        "Op Time", "Op Hours", "CO2 Mass (Tons)", "Heat Input (mmBtu)",
        "Eligible Biomass (Tons) (State Value)",
        "Eligible CHP Thermal Output (Tons) (State Value)"
    ]
    for c in numeric_columns:
        df[c] = df[c].replace("No Data", np.nan)
        df[c] = df[c].str.replace(",", "").astype(np.float64)

    schema = pa.DataFrameSchema(
        {
            "Year": pa.Column(
                int,
                checks = pa.Check.between(2009, 2025),
                nullable = False
                ),
            "Source Name": pa.Column(
                str,
                checks = pa.Check.ne(""),
                nullable = False
                ),
            "ORIS Code": pa.Column(
                int,
                checks = pa.Check.gt(0),
                nullable = False
                ),
            "State": pa.Column(
                str,
                checks = pa.Check.isin(
                    [
                        'CT', 'DE', 'MA', 'MD', 'ME', 'NH', 'NJ', 'NY', 'PA', 'RI',
                        'VA', 'VT'
                        ]
                    ),
                nullable = False
                ),
            **{
                c: pa.Column(np.float64, checks = pa.Check.ge(0), nullable = True)
                for c in numeric_columns
                },
            "Reporting Status": pa.Column(
                str,
                checks = pa.Check.isin(["Complete", "Incomplete"])
            )
        },
        checks = pa.Check(
            lambda df: df.duplicated(["Year", "ORIS Code"]).sum() == 0,
            name = "ORIS-year_is_unique_identifier"
        )
    )
    df = schema.validate(df)

    df.to_csv(PROCESSED_DATA_DIR / fname, index=False)

def process_geolocated_power_plants():
    fname = "Power_Plants"
    gdf = geopandas.read_file(RAW_DATA_DIR / fname)
    
    gdf["County"] = gdf["County"].replace("SUFFOLK", "Suffolk")

    mw_columns = [
            "Install_MW", "Total_MW", "Bat_MW", "Bio_MW", "Coal_MW",
            "Geo_MW", "Hydro_MW", "HydroPS_MW", "NG_MW", "Nuclear_MW",
            "Crude_MW", "Solar_MW", "Wind_MW", "Other_MW"
            ]
    # Check that there are no frequencies at suspicious/missing values like 999.
    #[print(df[c].value_counts()) for c in mw_columns]

    schema = pa.DataFrameSchema(
        {
            **{
                c: pa.Column(np.int32, unique = True, nullable = False)
                for c in ["OBJECTID", "Plant_Code"]
            },
            **{
                c: pa.Column(np.float64, checks = pa.Check.ge(0), nullable = False)
                for c in mw_columns
            },
            "geometry": pa.Column(nullable = False)
        },
    )
    gdf = schema.validate(gdf)

    gdf = gdf.to_crs("EPSG:4326")

    gdf.to_file(PROCESSED_DATA_DIR / fname, index = False)

def process_world_countries():
    fname = "geoBoundariesCGAZ_ADM0"
    gdf = geopandas.read_file(RAW_DATA_DIR / fname)
    gdf = gdf.to_crs("EPSG:4326")
    gdf.to_file(PROCESSED_DATA_DIR / fname, index = False)
    
def main():
    process_rggi_emissions_annual_facility()
    process_geolocated_power_plants()
    process_world_countries()

if __name__ == "__main__":
    main()
