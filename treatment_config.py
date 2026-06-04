# Water quality requirements for each Fit-for-Purpose scenario
# Combined requirement specifications with detailed parameters, units, and limits
WATER_QUALITY_REQUIREMENTS = {
    "Surface water discharge": {
        "pH": {"unit": "-", "range": "6.5-8.5"},
        "Conductivity": {"unit": "µS/cm", "limit": 900.0},
        "DO": {"unit": "mg/L", "limit": 4.0},
        "TDS": {"unit": "mg/L", "limit": 500.0},
        "TOC": {"unit": "mg/L", "limit": 5.0},
        "NH4-N": {"unit": "mg/L", "limit": 0.5},
        "Oil": {"unit": "mg/L", "limit": 10.0},
        "Boron": {"unit": "mg/L", "limit": 4.0},
        "Chloride": {"unit": "mg/L", "limit": 250.0},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 150.0},
        "BTEX": {"unit": "mg/L", "limit": 2.0},
        "PAHs": {"unit": "mg/L", "limit": 0.2},
        "Gross Alpha": {"unit": "pCi/L", "limit": 15.0},
        "Gross Beta": {"unit": "pCi/L", "limit": 15.0},
        "Notes": "Surface water discharge requirements are governed by a hierarchical regulatory framework consisting \
                  of the U.S. Clean Water Act, EPA water quality standards, and state-specific regulations. \
                  \\n Discharge limits are ultimately defined through permit systems (e.g., NPDES/TPDES), which incorporate \
                 both technology-based and water-quality-based criteria depending on receiving water conditions. \
                 \\n For produced water discharges, while currently not allowed by regulations, this tool provides \
                  technology-based effluent limits that are typically established \
                  based on the best available technology (BAT) for the specific industry and discharge type. ",
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
    "Municipal drinking water": {
        "pH": {"unit": "-", "range": "6.5-8.5"},
        "TDS": {"unit": "mg/L", "limit": 500.0},
        "Turbidity": {"unit": "NTU", "limit": 0.3},
        "Hardness": {"unit": "mg/L as CaCO3", "limit": 150.0},
        "Iron": {"unit": "mg/L", "limit": 0.3},
        "Manganese": {"unit": "mg/L", "limit": 0.05},
        "Arsenic": {"unit": "mg/L", "limit": 0.01},
        "Notes": "Placeholder municipal drinking water targets. Values should be reviewed and updated against the applicable federal, state, tribal, and project-specific requirements."
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

BRINE_MANAGEMENT_OPTIONS = {
    "Brine disposal": [
        "Evaporation pond",
        "Deep well injection",
        "Brine hauling",
        "Hydraulic fracturing reuse",
        "Reuse-compatible brine recycle / disposal",
        "Brine concentration for ZLD",
        "Crystallization",
    ],
    "Brine valorization": [
        "Bipolar membrane ED",
        "Selective ED",
        "Lithium adsorption",
        "Mineral precipitation / recovery",
        "Chemical precipitation",
        "Crystallization",
        "Acid/base recovery",
        "Evaporation pond",
    ],
}

BRINE_CATEGORY_DEFAULT_UNIT = {
    "Brine disposal": "Evaporation pond",
    "Brine valorization": "Mineral precipitation / recovery",
}


def get_brine_category(brine_unit):
    """Return the high-level brine management category for a brine unit."""
    for category, units in BRINE_MANAGEMENT_OPTIONS.items():
        if brine_unit in units:
            return category
    return "Brine disposal"


def normalize_treatment_train_config(config):
    """Normalize brine config to include a category and editable unit list."""
    brine = config.get("brine", [])
    if isinstance(brine, str):
        brine_units = [brine]
    else:
        brine_units = list(brine)

    brine_category = config.get("brine_category")
    if brine_category not in BRINE_MANAGEMENT_OPTIONS:
        if brine_units and brine_units[0] in BRINE_CATEGORY_DEFAULT_UNIT:
            brine_category = brine_units[0]
        else:
            brine_category = get_brine_category(brine_units[0]) if brine_units else "Brine disposal"

    brine_units = [
        BRINE_CATEGORY_DEFAULT_UNIT.get(unit, unit)
        for unit in brine_units
    ]

    normalized = config.copy()
    normalized["brine_category"] = brine_category
    normalized["brine"] = brine_units
    return normalized


def get_treatment_train_config(ffp_scenario, desal_type, water_type="Produced water"):
    """
    Returns the default treatment train configuration for a given Fit-for-Purpose scenario.
    
    Args:
        ffp_scenario: The selected Fit-for-Purpose scenario
        desal_type: Either "Thermal" (MVC) or "Membrane" (LSRRO)
        water_type: Source water type, e.g., "Produced water" or "Brackish groundwater"
    
    Returns:
        Dictionary with pretreatment, desalination, posttreatment, and brine management
    """

    if water_type == "Brackish groundwater":
        if desal_type == "Membrane desalination (MD)":
            primary_desal = ["NF", "MD"]
        elif desal_type == "Mechanical Vapor Compression (MVC)":
            primary_desal = ["NF", "MVC"]
        elif desal_type == "Reverse osmosis (RO)":
            primary_desal = ["RO"]
        else:
            primary_desal = ["NF", "RO"]

        configs = {
            "Municipal drinking water": {
                "pretreatment": ["Well pumping", "Raw water storage", "Cartridge filter"],
                "desalination": ["RO"],
                "posttreatment": ["ZIX-Zak IX"],
                "brine_category": "Brine valorization",
                "brine": ["Chemical precipitation", "Crystallization"]
            },
            "Agricultural use": {
                "pretreatment": ["Media filtration", "Cartridge filter", "Antiscalant dosing"],
                "desalination": ["RO"],
                "posttreatment": ["Selective ED", "Blending / salinity adjustment", "pH adjustment"],
                "brine": "Bipolar membrane ED"
            },
            "Surface water discharge": {
                "pretreatment": ["Well pumping", "Media filtration", "Cartridge filter"],
                "desalination": ["RO"],
                "posttreatment": ["GAC", "Chlorination"],
                "brine": "Deep well injection"
            },
            "Powerplant cooling water": {
                "pretreatment": ["Well pumping", "Media filtration", "Cartridge filter", "Antiscalant dosing"],
                "desalination": ["NF", "RO"],
                "posttreatment": ["Scale inhibitor dosing", "pH adjustment"],
                "brine": "Brine disposal"
            },
            "Data center cooling water": {
                "pretreatment": ["Well pumping", "Media filtration", "Cartridge filter", "Antiscalant dosing"],
                "desalination": ["NF", "RO"],
                "posttreatment": ["Biocide dosing", "Fine filter", "pH adjustment"],
                "brine": "Brine disposal"
            },
            "Feedwater to UPW production": {
                "pretreatment": ["Well pumping", "Media filtration", "Ultrafiltration", "Antiscalant dosing"],
                "desalination": ["RO", "RO"],
                "posttreatment": ["GAC", "Ion exchange / EDI"],
                "brine": "Brine valorization"
            },
            "Hydraulic fracturing reuse": {
                "pretreatment": ["Well pumping", "Media filtration", "Bag filter"],
                "desalination": ["RO"],
                "posttreatment": ["Adjust TDS", "Additives blending"],
                "brine": "Reuse-compatible brine recycle / disposal"
            },
            "ZLD feed conditioning": {
                "pretreatment": ["Well pumping", "Media filtration", "Softening / silica control", "Antiscalant dosing"],
                "desalination": ["RO"],
                "posttreatment": ["Selective ED", "Mineral precipitation / recovery"],
                "brine": "Crystallizer"
            }
        }

        return normalize_treatment_train_config(configs.get(ffp_scenario, configs["Municipal drinking water"]))

    if desal_type == "Mechanical Vapor Compression (MVC)":
        configs = {
            "Municipal drinking water": {
                "pretreatment": ["DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["MVC"],
                "posttreatment": ["Blending / remineralization", "pH adjustment", "Chlorination"],
                "brine": "Brine disposal"
            },
            "Surface water discharge": {
                "pretreatment": ["3-phase separator","DAF", "Ultrafiltration"],
                "desalination": ["MVC"],
                "posttreatment": ["GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
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
            "Municipal drinking water": {
                "pretreatment": ["DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["MD"],
                "posttreatment": ["Blending / remineralization", "pH adjustment", "Chlorination"],
                "brine": "Brine disposal"
            },
            "Surface water discharge": {
                "pretreatment": ["3-phase separator","DAF", "Ultrafiltration", "Antiscalant / pH adjustment"],
                "desalination": ["MD"],
                "posttreatment": ["GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
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

    elif desal_type in ["RO", "Reverse Osmosis (RO)", "Reverse osmosis (RO)"]:
        configs = {
            "Municipal drinking water": {
                "pretreatment": ["DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["RO"],
                "posttreatment": ["Blending / remineralization", "pH adjustment", "Chlorination"],
                "brine": "Brine disposal"
            },
            "Surface water discharge": {
                "pretreatment": ["3-phase separator","DAF", "Ultrafiltration", "Antiscalant / pH adjustment"],
                "desalination": ["RO"],
                "posttreatment": ["GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["RO"],
                "posttreatment": ["Boron-selective IX", "Blending / remineralization", "pH adjustment"],
                "brine": "Brine valorization"
            },
            "Powerplant cooling water": {
                "pretreatment": ["DAF", "Cartridge filter"],
                "desalination": ["RO"],
                "posttreatment": ["Scale inhibitor dosing", "Polishing filter"],
                "brine": "Brine disposal"
            },
            "Data center cooling water": {
                "pretreatment": ["DAF", "Ultra-fine filtration"],
                "desalination": ["RO"],
                "posttreatment": ["Biocide dosing", "Fine filter", "Polishing"],
                "brine": "Brine disposal"
            },
            "Feedwater to UPW production": {
                "pretreatment": ["DAF", "Air stripping", "Ultrafiltration"],
                "desalination": ["RO"],
                "posttreatment": ["GAC", "Ion exchange"],
                "brine": "Brine valorization"
            },
            "Hydraulic fracturing reuse": {
                "pretreatment": ["DAF", "Bag filter"],
                "desalination": ["RO"],
                "posttreatment": ["Adjust TDS", "Add additives"],
                "brine": "Hydraulic fracturing reuse"
            },
            "ZLD feed conditioning": {
                "pretreatment": ["DAF", "Media filtration"],
                "desalination": ["RO"],
                "posttreatment": ["Hardness adjustment", "Scale control"],
                "brine": "Brine concentration for ZLD"
            }
        }

    else: # LSRRO
        configs = {
            "Municipal drinking water": {
                "pretreatment": ["DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
                "desalination": ["LSRRO"],
                "posttreatment": ["Blending / remineralization", "pH adjustment", "Chlorination"],
                "brine": "Brine disposal"
            },
            "Surface water discharge": {
                "pretreatment": ["3-phase separator","DAF", "Ultrafiltration", "Antiscalant / pH adjustment"],
                "desalination": ["LSRRO"],
                "posttreatment": ["GAC", "Zeolite"],
                "brine": "Brine disposal"
            },
            "Agricultural use": {
                "pretreatment": ["3-phase separator", "DAF", "Ultrafiltration", "Softening / silica control", "Antiscalant / pH adjustment"],
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

    return normalize_treatment_train_config(configs.get(ffp_scenario, configs["Surface water discharge"]))


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
    "Magnesium": {"unit": "mg/L", "limit": 100.0},
    "Manganese": {"unit": "mg/L", "limit": 0.01},
    "Calcium": {"unit": "mg/L", "limit": 100.0},
    "Barium": {"unit": "mg/L", "limit": 20.0},
    "Lithium": {"unit": "mg/L", "limit": 2.5},
    "Strontium": {"unit": "mg/L", "limit": 10.0},
    "Arsenic": {"unit": "mg/L", "limit": 0.1},
    "Selenium": {"unit": "mg/L", "limit": 0.05},
    "Fluoride": {"unit": "mg/L", "limit": 4.0},
    "Uranium": {"unit": "mg/L", "limit": 0.03},
    "SAR": {"unit": "-", "limit": 3.0},
    "Sulfate": {"unit": "mg/L", "limit": 50.0},
    "Bicarbonate": {"unit": "mg/L", "limit": 300.0},
    "BTEX": {"unit": "mg/L", "limit": 0.1},
    "PAHs": {"unit": "mg/L", "limit": 0.01},
    "Gross Alpha": {"unit": "pCi/L", "limit": 15.0},
    "Gross Beta": {"unit": "pCi/L", "limit": 50.0},
    "Radium-226": {"unit": "pCi/L", "limit": 50.0},
    "Radium-228": {"unit": "pCi/L", "limit": 50.0},
}


# Unit removal rates for different constituents (%)
UNIT_REMOVAL_RATES = {
    # =========================================================
    # Pretreatment
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

    "Ultra-fine filtration": {
        "TSS": "95-99%",
        "Turbidity": "95-99%"
    },

    "Well pumping": {},

    "Raw water storage": {},

    "Product water storage": {},

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
        "Boron": "99%+",
        "Sodium": "99.9%+",
        "Chloride": "99.9%+",
        "Silica": "95-99%",
        "Iron": "99.9%+",
        "Manganese": "99.9%+",
        "Calcium": "99.9%+",
        "Barium": "99.9%+",
        "Lithium": "90-99%",
        "Strontium": "99.9%+",
        "Arsenic": "95-99%",
        "Selenium": "95-99%",
        "Sulfate": "99.9%+",
        "Bicarbonate": "90-99%",
        "BTEX": "50-90%",
        "PAHs": "50-90%",
        "Gross Alpha": "95-99%",
        "Gross Beta": "95-99%",
        "Radium-226": "90-99%",
        "Radium-228": "90-99%"
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
        "Gross Beta": "95-99%",
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

    "BWRO": {
        "Conductivity": "90-99%",
        "TDS": "90-99%",
        "Hardness": "90-99%",
        "Alkalinity": "60-90%",
        "Boron": "20-70%",
        "Sodium": "90-99%",
        "Chloride": "90-99%",
        "Silica": "70-95%",
        "Arsenic": "80-99%",
        "Fluoride": "80-95%",
        "Uranium": "90-99%",
        "Gross Alpha": "90-99%",
        "Gross Beta": "90-99%",
        "Radium-226": "90-99%",
        "Radium-228": "90-99%"
    },

    "NF": {
        "Conductivity": "30-80%",
        "TDS": "30-80%",
        "Hardness": "70-95%",
        "Calcium": "70-95%",
        "Magnesium": "70-95%",
        "Sulfate": "80-98%",
        "Arsenic": "50-90%",
        "Uranium": "70-95%",
        "Gross Alpha": "70-95%",
        "Gross Beta": "70-95%",
        "Boron": "10-40%"
    },

    # =========================================================
    # Post-treatment / polishing
    # =========================================================
    "Ammonia stripping": {
        "NH4-N": "90-99%"
    },
    "GAC": {
        "TOC": "90-99%",
        "Oil": "10-40%",
        "BTEX": "90-99%",
        "PAHs": "90-99%"
    },
    "Zeolite": {
        "NH4-N": "90-99%",
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
    "Ion exchange": {
        "Conductivity": "70-95%",
        "TDS": "70-95%",
        "Hardness": "80-99%",
        "Arsenic": "80-99%",
        "Uranium": "80-99%",
        "Gross Alpha": "80-99%",
        "Gross Beta": "80-99%"
    },
    "Boron-selective IX": {
        "Boron": "95-99%"
    },
    "ZIX-Zak IX": {
        "TDS": "70-95%",
        "Sodium": "70-95%",
        "Chloride": "70-95%",
        "Sulfate": "70-95%",
        "Arsenic": "80-99%",
        "Fluoride": "70-95%",
        "Uranium": "90-99%",
        "Gross Alpha": "90-99%",
        "Radium-226": "90-99%",
        "Radium-228": "90-99%"
    },
    "KNeW ion exchange": {
        "TDS": "70-95%",
        "Sodium": "70-95%",
        "Chloride": "70-95%",
        "Sulfate": "70-95%",
        "Hardness": "70-95%",
        "Arsenic": "80-99%",
        "Uranium": "90-99%"
    },
    "Selective ED": {
        "TDS": "40-90%",
        "Conductivity": "40-90%",
        "Sodium": "40-90%",
        "Chloride": "40-90%",
        "Sulfate": "40-90%",
        "SAR": "20-70%"
    },
    "Bipolar membrane ED": {
        "TDS": "30-80%",
        "Conductivity": "30-80%",
        "Sodium": "30-80%",
        "Chloride": "30-80%",
        "Sulfate": "30-80%"
    },
    "Lithium adsorption": {
        "Lithium": "50-95%"
    },
    "Mineral precipitation / recovery": {
        "Hardness": "50-95%",
        "Calcium": "50-95%",
        "Magnesium": "50-95%",
        "Sulfate": "20-80%",
        "Silica": "20-80%"
    },
    "Chemical precipitation": {
        "Hardness": "50-95%",
        "Calcium": "50-95%",
        "Magnesium": "50-95%",
        "Iron": "50-95%",
        "Manganese": "50-95%",
        "Arsenic": "50-95%"
    },
    "Acid/base recovery": {},
    "Fertilizer recovery": {
        "Sodium": "10-60%",
        "Chloride": "10-60%",
        "Sulfate": "10-60%"
    },
    "Solar PV": {},
    "Chlorination": {},
    "Polishing filter": {
        "TSS": "95-99%",
        "Turbidity": "90-99%"
    },
    "Fine filter": {
        "TSS": "95-99%",
        "Turbidity": "90-99%"
    },
    "Polishing": {
        "TSS": "80-99%",
        "Turbidity": "80-99%",
        "TOC": "10-50%"
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
    "Brine concentration for ZLD": {},
    "Evaporation pond": {},
    "Deep well injection": {},
    "Brine hauling": {},
    "Crystallizer": {},
    "Crystallization": {}
}

# Default values for sidebar inputs
SIDEBAR_DEFAULTS = {
    "High": {
    "pH": 6.4,
    "Oil": 346.0,
    "TDS": 180000.0,
    "TOC": 213.1,
    "TSS": 790.0,
    "Alkalinity": 870.0,
    "Hardness": 27800.0,
    "NH4-N": 750.0,
    "Barium": 12.0,
    "Boron": 76.5,
    "Calcium": 8200.0,
    "Mangesium": 1800.0,
    "Silica": 195.0,
    "Sodium": 49000.0,
    "Strontium": 1404.0,
    "Chloride": 102000.0,
    "Sulfate": 950.0,
    "Gross Alpha": 1630.0,
    "Gross Beta": 1230.0,
    "Radium-226": 970.0,
    "Radium-228": 346.0,
    "PAHs": 59.0,
    "BTEX": 10.2,
    },
    "Medium": {
    "pH": 6.4,
    "Oil": 189.0,
    "TDS": 130000.0,
    "TOC": 103.5,
    "TSS": 342.9,
    "Alkalinity": 279.0,
    "Hardness": 12500.0,
    "NH4-N": 500.0,
    "Barium": 5.6,
    "Boron": 42.3,
    "Calcium": 3800.0,
    "Mangesium": 745.0,
    "Silica": 107.0,
    "Sodium": 41000.0,
    "Strontium": 450.0,
    "Chloride": 78600.0,
    "Sulfate": 495.0,
    "Gross Alpha": 1105.0,
    "Gross Beta": 874.0,
    "Radium-226": 531.0,
    "Radium-228": 231.0,
    "PAHs": 21.0,
    "BTEX": 6.1,
    },
    "Low": {
    "pH": 6.4,
    "Oil": 67.0,
    "TDS": 100000.0,
    "TOC": 12.6,
    "TSS": 850.0,
    "Alkalinity": 132.0,
    "Hardness": 4200.0,
    "NH4-N": 350.0,
    "Barium": 2.2,
    "Boron": 17.2,
    "Calcium": 1200.0,
    "Mangesium": 295.0,
    "Silica": 47.5,
    "Sodium": 33600.0,
    "Strontium": 235.0,
    "Chloride": 58900.0,
    "Sulfate": 251.0,
    "Gross Alpha": 760.0,
    "Gross Beta": 556.0,
    "Radium-226": 237.0,
    "Radium-228": 89.0,
    "PAHs": 17.0,
    "BTEX": 4.5,
    },
    "Brackish groundwater": {
        "High": {
            "pH": 7.2,
            "TDS": 12000.0,
            "TSS": 25.0,
            "Turbidity": 10.0,
            "Alkalinity": 900.0,
            "Hardness": 1500.0,
            "Calcium": 450.0,
            "Magnesium": 100.0,
            "Sodium": 3600.0,
            "Chloride": 3100.0,
            "Sulfate": 4400.0,
            "Bicarbonate": 1800.0,
            "Boron": 8.0,
            "Silica": 35.0,
            "Iron": 3.0,
            "Manganese": 0.2,
            "Arsenic": 0.05,
            "Fluoride": 4.0,
            "Uranium": 0.02,
            "Gross Alpha": 100.0,
            "Gross Beta": 50.0,
            "Radium-226": 10.0,
            "Radium-228": 10.0,
            "SAR": 8.0,
        },
        "Medium": {
            "pH": 7.3,
            "TDS": 5000.0,
            "TSS": 10.0,
            "Turbidity": 5.0,
            "Alkalinity": 350.0,
            "Hardness": 600.0,
            "Calcium": 180.0,
            "Magnesium": 40.0,
            "Sodium": 1200.0,
            "Chloride": 900.0,
            "Sulfate": 900.0,
            "Bicarbonate": 500.0,
            "Boron": 2.0,
            "Silica": 25.0,
            "Iron": 0.8,
            "Manganese": 0.1,
            "Arsenic": 0.02,
            "Fluoride": 2.0,
            "Uranium": 0.01,
            "Gross Alpha": 30.0,
            "Gross Beta": 20.0,
            "Radium-226": 5.0,
            "Radium-228": 5.0,
            "SAR": 4.0,
        },
        "Low": {
            "pH": 7.4,
            "TDS": 1500.0,
            "TSS": 5.0,
            "Turbidity": 2.0,
            "Alkalinity": 180.0,
            "Hardness": 250.0,
            "Calcium": 70.0,
            "Magnesium": 20.0,
            "Sodium": 300.0,
            "Chloride": 250.0,
            "Sulfate": 250.0,
            "Bicarbonate": 250.0,
            "Boron": 0.8,
            "Silica": 15.0,
            "Iron": 0.3,
            "Manganese": 0.05,
            "Arsenic": 0.01,
            "Fluoride": 1.0,
            "Uranium": 0.005,
            "Gross Alpha": 10.0,
            "Gross Beta": 10.0,
            "Radium-226": 2.0,
            "Radium-228": 2.0,
            "SAR": 2.0,
        }
    }
}
