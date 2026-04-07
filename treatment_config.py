# Water quality requirements for each Fit-for-Purpose scenario
# Combined requirement specifications with detailed parameters, units, and limits
WATER_QUALITY_REQUIREMENTS = {
    "Surface water discharge": {
        "TSS": {"unit": "mg/L", "limit": 30.0},
        "NH4-N": {"unit": "mg/L", "limit": 1.0},
        "Oil": {"unit": "mg/L", "limit": 10.0},
        "TOC": {"unit": "mg/L", "limit": 10.0},
        "Gross Alpha": {"unit": "pCi/L", "limit": 15.0},
        "Gross Beta": {"unit": "pCi/L", "limit": 50.0},
        "Notes": "Surface water discharge requirements are governed by a hierarchical regulatory framework consisting \
                  of the U.S. Clean Water Act, EPA water quality standards, and state-specific regulations. \
                  \\n Discharge limits are ultimately defined through permit systems (e.g., NPDES/TPDES), which incorporate \
                both technology-based and water-quality-based criteria depending on receiving water conditions.",
        "url": {"EPA NPDES Program": "https://www.epa.gov/npdes",
                "EPA Water Quality Standards": "https://www.epa.gov/wqs-tech/water-quality-standards",
                "State-specific regulations": "https://www.epa.gov/wqs-tech/state-water-quality-standards",
                }
    },
    "Agricultural use": {
        "pH": {"unit": "-", "range": "6.5-8.4"},
        "TDS": {"unit": "mg/L", "limit": 450.0},
        "Conductivity": {"unit": "µS/cm", "limit": 700.0},
        "SAR": {"unit": "-", "limit": 3.0},
        "Boron": {"unit": "mg/L", "limit": 0.7},
        "Sodium": {"unit": "mg/L", "limit": 70.0},
        "Chloride": {"unit": "mg/L", "limit": 140.0},
        "Manganese": {"unit": "mg/L", "limit": 0.02},
        "Iron": {"unit": "mg/L", "limit": 5.0},
        "Lithium": {"unit": "mg/L", "limit": 2.5},
        "Arsenic": {"unit": "mg/L", "limit": 0.1},
        "Selenium": {"unit": "mg/L", "limit": 0.02},
        "Bicarbonate": {"unit": "mg/L", "limit": 1.5},

        "Notes": "These values are provided as general guidelines based on FAO Irrigation and Drainage and should not be interpreted as strict regulatory limits. \
            \\n Site-specific factors such as crop type, soil conditions, \
            and management practices (e.g., blending, soil amendments) should be considered when determining appropriate thresholds.\
            \\n This guideline evaluates the agricultural water suitability based on four categories defined in the FAO framework: \
            * Salinity (affecting crop water availability, typically represented by EC or TDS), \
            * Infiltration (affecting soil infiltration rate, evaluated using EC and SAR together), \
            * Specific ion toxicity (affecting sensitive crops, including Na+, Cl-, Boron and trace elements), \
            * Miscellaneous effects (including parameters such as nitrogen (NO3-N), bicarbonate (HCO3-), and pH). ",
        "url": {"FAO Irrigation Water Quality Guidelines":  "https://www.fao.org/4/t0234e/T0234E00.htm#TOC"},

    },
    "Powerplant cooling water": {
        "TSS": {"unit": "mg/L", "limit": 10.0},
        "Oil": {"unit": "mg/L", "limit": 5.0},
        "Conductivity": {"unit": "µS/cm", "limit": 5000.0},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 500.0},
        "Alkalinity": {"unit": "mg/L as CaCO3", "limit": 300.0},
        "Silica": {"unit": "mg/L", "limit": 40.0},
        "TOC": {"unit": "mg/L", "limit": 5.0},
        "Notes": "Powerplant cooling water quality requirements are aimed at preventing scaling, corrosion, and fouling in cooling systems. \
                 Parameters like TSS, oil, conductivity, hardness, alkalinity, silica, and TOC must be controlled to maintain efficient heat \
                 transfer and minimize maintenance issues in cooling towers and condensers."
    },
    "Data center cooling water": {
        "TSS": {"unit": "mg/L", "limit": 5.0},
        "Conductivity": {"unit": "µS/cm", "limit": 2000.0},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 100.0},
        "Silica": {"unit": "mg/L", "limit": 20.0},
        "TOC": {"unit": "mg/L", "limit": 3.0},
        "Microbes": {"unit": "CFU/mL", "limit": 10000.0},
        "Notes": "Data center cooling water quality requirements focus on preventing scaling, corrosion, and microbial growth in cooling systems. \
                 Parameters like TSS, conductivity, hardness, silica, TOC, and microbial counts must be controlled to maintain efficient heat \
                 transfer and minimize maintenance issues."
    },
    "Feedwater to UPW production": {
        "TDS": {"unit": "mg/L", "limit": 190.0},
        "Conductivity": {"unit": "µS/cm", "limit": 330.0},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 130.0},
        "TOC": {"unit": "mg/L", "limit": 2.8},
        "Silica": {"unit": "mg/L", "limit": 19.0},
        "Iron": {"unit": "mg/L", "limit": 0.2},
        "Manganese": {"unit": "mg/L", "limit": 0.04},
        "Turbidity": {"unit": "NTU", "limit": 0.1},
        "NH4-N": {"unit": "mg/L", "limit": 0.0},
        "Notes": "Feedwater quality requirements for UPW production are extremely stringent to ensure the \
                  highest purity water for semiconductor manufacturing. Parameters like TDS, hardness, TOC,\
                  silica, iron, manganese, turbidity, and ammonia must be tightly controlled to prevent scaling, \
                  fouling, and contamination of the UPW system and final product."
    },
    "Hydraulic fracturing reuse": {
        "TSS": {"unit": "mg/L", "limit": 50.0},
        "Oil": {"unit": "mg/L", "limit": 10.0},
        "Iron": {"unit": "mg/L", "limit": 50.0},
        "Bacteria": {"unit": "CFU/mL", "limit": 1000.0},
        "Ba2+": {"unit": "mg/L", "limit": 20.0},
        "SO4": {"unit": "mg/L", "limit": 50.0},
        "Notes": "Hydraulic fracturing reuse water quality requirements focus on parameters that can cause operational issues in fracturing operations. \
                High TSS, oil, iron, bacteria, barium, and sulfate can lead to equipment fouling, scaling, and microbial growth in fracturing fluids and \
                wellbore environments. Controlling these parameters is essential for successful reuse of produced water in hydraulic fracturing."
    },
    "ZLD feed conditioning": {
        "TSS": {"unit": "mg/L", "limit": 10.0},
        "Oil": {"unit": "mg/L", "limit": 5.0},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 100.0},
        "Silica": {"unit": "mg/L", "limit": 20.0},
        "Ba2+": {"unit": "mg/L", "limit": 5.0},
        "Sr2+": {"unit": "mg/L", "limit": 10.0},
        "SO4": {"unit": "mg/L", "limit": 50.0},
        "Notes": "ZLD feed conditioning water quality requirements focus on parameters that can cause scaling and fouling in ZLD systems. \
                  High TSS, oil, hardness, silica, barium, strontium, and sulfate can lead to operational issues in evaporators, crystallizers,\
                  and other ZLD components. Controlling these parameters is essential for efficient ZLD operation and minimizing maintenance."
    }
}


def get_treatment_train_config(ffp_scenario, desal_type):
    """
    Returns the default treatment train configuration for a given Fit-for-Purpose scenario.
    
    Args:
        ffp_scenario: The selected Fit-for-Purpose scenario
        desal_type: Either "Thermal" (MVC) or "Membrane" (LSRRO)
    
    Returns:
        Dictionary with pretreatment, desalination, posttreatment, and brine management
    """

    if desal_type == "Mechanical Vapor Compression (MVC)":
        configs = {
            "Surface water discharge": {
                "pretreatment": ["DAF", "Walnut shell filtration"],
                "desalination": ["MVC"],
                "posttreatment": ["Ammonia stripping", "GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "Floc n Drop", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["MVC"],
                "posttreatment": ["Blending / remineralization", "pH adjustment"],
                "brine": "Brine disposal"
            },
            "Powerplant cooling water": {
                "pretreatment": ["DAF", "Cartridge filter"],
                "desalination": ["MVC"],
                "posttreatment": ["Scale inhibitor dosing", "Polishing filter"],
                "brine": "Brine disposal"
            },
            "Data center cooling water": {
                "pretreatment": ["DAF", "Ultra-fine filtration"],
                "desalination": ["MVC"],
                "posttreatment": ["Biocide dosing", "Fine filter", "Polishing"],
                "brine": "Brine disposal"
            },
            "Feedwater to UPW production": {
                "pretreatment": ["DAF", "Ultrafiltration"],
                "desalination": ["MVC", "pH adjustment","RO"],
                "posttreatment": ["GAC", "Ion exchange"],
                "brine": "Brine valorization"
            },
            "Hydraulic fracturing reuse": {
                "pretreatment": ["DAF", "Bag filter"],
                "desalination": ["MVC"],
                "posttreatment": ["Adjust TDS", "Add additives"],
                "brine": "Hydraulic fracturing reuse"
            },
            "ZLD feed conditioning": {
                "pretreatment": ["DAF", "Media filtration"],
                "desalination": ["MVC"],
                "posttreatment": ["Hardness adjustment", "Scale control"],
                "brine": "Brine concentration for ZLD"
            }
        }

    elif desal_type == "Membrane desalination (MD)":  # Membrane desalination
        configs = {
            "Surface water discharge": {
                "pretreatment": ["DAF", "Walnut shell filtration"],
                "desalination": ["MD"],
                "posttreatment": ["Ammonia stripping", "GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "Floc n Drop", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["MD"],
                "posttreatment": ["Blending / remineralization", "pH adjustment"],
                "brine": "Brine valorization"
            },
            "Powerplant cooling water": {
                "pretreatment": ["DAF", "Cartridge filter"],
                "desalination": ["MD"],
                "posttreatment": ["Scale inhibitor dosing", "Polishing filter"],
                "brine": "Brine disposal"
            },
            "Data center cooling water": {
                "pretreatment": ["DAF", "Ultra-fine filtration"],
                "desalination": ["MD"],
                "posttreatment": ["Biocide dosing", "Fine filter", "Polishing"],
                "brine": "Brine disposal"
            },
            "Feedwater to UPW production": {
                "pretreatment": ["DAF", "Ultrafiltration"],
                "desalination": ["MD"],
                "posttreatment": ["GAC", "Ion exchange"],
                "brine": "Brine valorization"
            },
            "Hydraulic fracturing reuse": {
                "pretreatment": ["DAF", "Bag filter"],
                "desalination": ["MD"],
                "posttreatment": ["Adjust TDS", "Add additives"],
                "brine": "Hydraulic fracturing reuse"
            },
            "ZLD feed conditioning": {
                "pretreatment": ["DAF", "Media filtration"],
                "desalination": ["MD"],
                "posttreatment": ["Hardness adjustment", "Scale control"],
                "brine": "Brine concentration for ZLD"
            }
        }

    else: # LSRRO
        configs = {
            "Surface water discharge": {
                "pretreatment": ["DAF", "Walnut shell filtration"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Ammonia stripping", "GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "Floc n Drop", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Boron-selective IX", "Blending / remineralization", "pH adjustment"],
                "brine": "Brine valorization"
            },
            "Powerplant cooling water": {
                "pretreatment": ["DAF", "Cartridge filter"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Scale inhibitor dosing", "Polishing filter"],
                "brine": "Brine disposal"
            },
            "Data center cooling water": {
                "pretreatment": ["DAF", "Ultra-fine filtration"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Biocide dosing", "Fine filter", "Polishing"],
                "brine": "Brine disposal"
            },
            "Feedwater to UPW production": {
                "pretreatment": ["DAF", "Air stripping", "Ultrafiltration"],
                "desalination": ["LSRRO"],
                "posttreatment": ["GAC", "Ion exchange"],
                "brine": "Brine valorization"
            },
            "Hydraulic fracturing reuse": {
                "pretreatment": ["DAF", "Bag filter"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Adjust TDS", "Add additives"],
                "brine": "Hydraulic fracturing reuse"
            },
            "ZLD feed conditioning": {
                "pretreatment": ["DAF", "Media filtration"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Hardness adjustment", "Scale control"],
                "brine": "Brine concentration for ZLD"
            }
        }

    return configs.get(ffp_scenario, configs["Surface water discharge"])


# All available water quality parameters for user selection
ALL_WATER_QUALITY_PARAMS = {
    "pH": {"unit": "-", "limit": 9.0},
    "Oil": {"unit": "mg/L", "limit": 10.0},
    "Conductivity": {"unit": "µS/cm", "limit": 5000.0},
    "TDS": {"unit": "mg/L", "limit": 2000.0},
    "TSS": {"unit": "mg/L", "limit": 30.0},
    "Turbidity": {"unit": "NTU", "limit": 5.0},
    "Hardness": {"unit": "mg/L as CaCO3", "limit": 500.0},
    "Alkalinity": {"unit": "mg/L as CaCO3", "limit": 300.0},
    "TOC": {"unit": "mg/L", "limit": 10.0},
    "NH4-N": {"unit": "mg/L", "limit": 1.0},
    "Boron": {"unit": "mg/L", "limit": 2.0},
    "Sodium": {"unit": "mg/L", "limit": 70.0},
    "Chloride": {"unit": "mg/L", "limit": 140.0},
    "Silica": {"unit": "mg/L", "limit": 40.0},
    "Iron": {"unit": "mg/L", "limit": 50.0},
    "Manganese": {"unit": "mg/L", "limit": 0.01},
    "Calcium": {"unit": "mg/L", "limit": 100.0},
    "Barium": {"unit": "mg/L", "limit": 20.0},
    "Lithium": {"unit": "mg/L", "limit": 2.5},
    "Strontium": {"unit": "mg/L", "limit": 10.0},
    "Arsenic": {"unit": "mg/L", "limit": 0.1},
    "Selenium": {"unit": "mg/L", "limit": 0.05},
    "Sulfate": {"unit": "mg/L", "limit": 50.0},
    "Bicarbonate": {"unit": "mg/L", "limit": 300.0},
    "BTEX": {"unit": "mg/L", "limit": 0.1},
    "PAHs": {"unit": "mg/L", "limit": 0.01},
    "Gross Alpha": {"unit": "pCi/L", "limit": 15.0},
    "Gross Beta": {"unit": "pCi/L", "limit": 50.0},
}


# Unit removal rates for different constituents (%)
UNIT_REMOVAL_RATES = {
    # =========================================================
    # Primary separation / pretreatment
    # =========================================================
    "3-phase separator": {
        "Oil": "90-95%",
        "TSS": "20-50%",
        "Turbidity": "10-40%"
    },

    "Equalization tank": {},

    "DAF": {
        "Oil": "90-99%",
        "TSS": "80-95%",
        "Turbidity": "80-95%",
        "TOC": "10-30%",
        "Iron": "10-30%"
    },

    "Floc n Drop": {
        "TSS": "70-95%",
        "Turbidity": "70-95%",
        "Iron": "60-95%",
        "Manganese": "40-90%",
        "TOC": "10-40%",
        "Oil": "20-60%"
    },

    "Walnut shell filtration": {
        "Oil": "60-90%",
        "TSS": "85-95%",
        "Turbidity": "90-98%"
    },

    "Media filtration": {
        "TSS": "70-90%",
        "Turbidity": "80-95%",
        "Iron": "10-30%"
    },

    "Cartridge filter": {
        "TSS": "90-99%",
        "Turbidity": "90-99%"
    },

    "Bag filter": {
        "TSS": "80-95%",
        "Turbidity": "70-90%"
    },

    "Ultrafiltration": {
        "TSS": "99%+",
        "Turbidity": "99%+",
        "Oil": "50-90%",
        "TOC": "20-50%"
    },

    # =========================================================
    # Chemical conditioning / pretreatment
    # =========================================================
    "Softening / pH adjustment": {
        "Hardness": "60-95%",
        "Calcium": "50-95%",
        "Barium": "20-70%",
        "Strontium": "10-50%",
        "Iron": "20-60%",
        "Manganese": "10-50%"
    },

    "Softening / silica control": {
        "Hardness": "60-95%",
        "Calcium": "50-95%",
        "Silica": "20-60%",
        "Barium": "20-70%",
        "Strontium": "10-50%"
    },

    "Antiscalant / pH adjustment": {},

    "Antiscalant dosing": {},

    "Air stripping": {
        "NH4-N": "50-95%",
        "TOC": "0-20%"
    },

    "Dechlorination / activated carbon": {
        "TOC": "20-60%"
    },

    # =========================================================
    # Thermal desalination
    # =========================================================
    "MVC": {
        "pH": "variable",
        "Oil": "95-99%",
        "Conductivity": "99%+",
        "TDS": "99.9%+",
        "TSS": "99%+",
        "Turbidity": "99%+",
        "Hardness": "99%+",
        "Alkalinity": "90-99%",
        "TOC": "20-80%",
        "NH4-N": "30-90%",
        "Boron": "99%+%",
        "Sodium": "99%+",
        "Chloride": "99%+",
        "Silica": "95-99%",
        "Iron": "99%+",
        "Manganese": "99%+",
        "Calcium": "99%+",
        "Barium": "99%+",
        "Lithium": "90-99%",
        "Strontium": "99%+",
        "Arsenic": "95-99%",
        "Selenium": "95-99%",
        "Sulfate": "99%+",
        "Bicarbonate": "90-99%",
        "BTEX": "50-90%",
        "PAHs": "50-90%",
        "Gross Alpha": "95-99%",
        "Gross Beta": "95-99%"
    },

    "MD": {
        "pH": "variable",
        "Oil": "90-99%",
        "Conductivity": "95-99%",
        "TDS": "95-99.5%",
        "TSS": "95-99%",
        "Turbidity": "95-99%",
        "Hardness": "95-99%",
        "Alkalinity": "80-98%",
        "TOC": "30-80%",
        "NH4-N": "0-50%",
        "Boron": "80-95%",
        "Sodium": "95-99%",
        "Chloride": "95-99%",
        "Silica": "90-99%",
        "Iron": "95-99%",
        "Manganese": "95-99%",
        "Calcium": "95-99%",
        "Barium": "95-99%",
        "Lithium": "80-95%",
        "Strontium": "95-99%",
        "Arsenic": "90-99%",
        "Selenium": "90-99%",
        "Sulfate": "95-99%",
        "Bicarbonate": "80-95%",
        "Gross Alpha": "95-99%",
        "Gross Beta": "95-99%"
    },

    # =========================================================
    # Membrane desalination
    # =========================================================
    "LSRRO": {
        "Conductivity": "95-99%",
        "TDS": "95-99%",
        "TSS": "90-99%",
        "Turbidity": "90-99%",
        "Hardness": "95-99%",
        "Alkalinity": "70-95%",
        "TOC": "20-60%",
        "NH4-N": "10-40%",
        "Boron": "30-70%",
        "Sodium": "90-99%",
        "Chloride": "90-99%",
        "Silica": "80-95%",
        "Iron": "80-95%",
        "Manganese": "80-95%",
        "Calcium": "95-99%",
        "Barium": "90-99%",
        "Lithium": "50-90%",
        "Strontium": "90-99%",
        "Arsenic": "80-95%",
        "Selenium": "80-95%",
        "Sulfate": "95-99%",
        "Bicarbonate": "70-95%",
        "Gross Alpha": "90-99%",
        "Gross Beta": "90-99%"
    },

    "OARO": {
        "Conductivity": "95-99%",
        "TDS": "95-99%",
        "TSS": "90-99%",
        "Turbidity": "90-99%",
        "Hardness": "95-99%",
        "Alkalinity": "70-95%",
        "TOC": "20-60%",
        "NH4-N": "10-40%",
        "Boron": "30-70%",
        "Sodium": "90-99%",
        "Chloride": "90-99%",
        "Silica": "80-95%",
        "Iron": "80-95%",
        "Manganese": "80-95%",
        "Calcium": "95-99%",
        "Barium": "90-99%",
        "Lithium": "50-90%",
        "Strontium": "90-99%",
        "Arsenic": "80-95%",
        "Selenium": "80-95%",
        "Sulfate": "95-99%",
        "Bicarbonate": "70-95%",
        "Gross Alpha": "90-99%",
        "Gross Beta": "90-99%"
    },

    "RO": {
        "Conductivity": "95-99%",
        "TDS": "95-99%",
        "TSS": "90-99%",
        "Turbidity": "90-99%",
        "Hardness": "95-99%",
        "Alkalinity": "70-95%",
        "TOC": "20-60%",
        "NH4-N": "10-40%",
        "Boron": "30-80%",
        "Sodium": "90-99%",
        "Chloride": "90-99%",
        "Silica": "80-95%",
        "Iron": "80-95%",
        "Manganese": "80-95%",
        "Calcium": "95-99%",
        "Barium": "90-99%",
        "Lithium": "50-90%",
        "Strontium": "90-99%",
        "Arsenic": "80-95%",
        "Selenium": "80-95%",
        "Sulfate": "95-99%",
        "Bicarbonate": "70-95%",
        "Gross Alpha": "90-99%",
        "Gross Beta": "90-99%"
    },

    # =========================================================
    # Post-treatment / polishing
    # =========================================================
    "Ammonia stripping": {
        "NH4-N": "90-99%"
    },
    "GAC": {
        "TOC": "50-90%",
        "Oil": "10-40%"
    },
    "Zeolite": {
        "NH4-N": "60-90%",
        "Iron": "10-40%",
        "Manganese": "10-40%"
    },
    "Ion exchange / EDI": {
        "Conductivity": "80-99%",
        "TDS": "80-95%",
        "Hardness": "99%+",
        "NH4-N": "80-95%",
        "Boron": "80-95%",
        "Sodium": "80-95%",
        "Chloride": "70-95%",
        "Calcium": "99%+",
        "Barium": "95-99%",
        "Strontium": "95-99%",
        "Arsenic": "90-99%",
        "Selenium": "90-99%",
        "Gross Alpha": "90-99%",
        "Gross Beta": "90-99%"
    },
    "Boron-selective IX": {
        "Boron": "95-99%"
    },
    "Polishing filter": {
        "TSS": "95-99%",
        "Turbidity": "90-99%"
    },
    "Fine filter": {
        "TSS": "95-99%",
        "Turbidity": "90-99%"
    },
    "Final filter": {
        "TSS": "99%+",
        "Turbidity": "99%+"
    },
    "pH adjustment": {},
    "Scale inhibitor dosing": {},
    "Biocide dosing": {},
    "Blending / remineralization": {},
    "Blending / salinity adjustment": {},
    "Adjust TDS": {},
    "Additives blending": {},
    "Add additives": {},
    "Hardness adjustment": {},
    "Scale control": {},

    # =========================================================
    # Brine / system handling
    # =========================================================
    "Brine disposal": {},
    "Brine disposal / further concentration": {},
    "Brine valorization": {},
    "Brine valorization / disposal": {},
    "Hydraulic fracturing reuse": {},
    "Reuse-compatible brine recycle / disposal": {},
    "Brine concentration for ZLD": {}
}

# Default values for sidebar inputs
SIDEBAR_DEFAULTS = {
    "pH": 6.4,
    "Oil": 100.0,
    "TDS": 180000.0,
    "Conductivity": 250000.0,
    "TSS": 165.0,
    "Turbidity": 40.0,
    "TOC": 80.0,
    "NH4-N": 500.0,
    "Boron": 14.2,
    "Sodium": 40000.0,
    "Chloride": 70000.0,
    "Silica": 40.0,
    "Hardness": 25000.0,
    "Alkalinity": 200.0,
    "Iron": 40.0,
    "Manganese": 2.5,
    "Calcium": 8000.0,
    "Barium": 30.0,
    "Lithium": 25.9,
    "Strontium": 3000.0,
    "Arsenic": 0.84,
    "Selenium": 0.745,
    "Sulfate": 500.0,
    "Bicarbonate": 140.0,
    "BTEX": 0.9,
    "PAHs": 0.3,
    "Gross Alpha": 1430.0,
    "Gross Beta": 3080.0,
}
