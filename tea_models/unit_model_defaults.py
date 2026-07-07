"""Unit-specific defaults used by generic technical and cost models."""

TECHNICAL_MODEL_DEFAULTS = {
    "Equalization tank": {
        "unit_kind": "tank",
        "recovery": 0.999,
        "energy_intensity": 0.01,
        "hydraulic_retention_time": 8.0,
        "design_factor": 1.1,
    },
    "Floc n Drop": {
        "unit_kind": "chemical_clarification",
        "recovery": 0.97,
        "energy_intensity": 0.06,
        "chemical_dose": 0.08,
        "hydraulic_retention_time": 0.75,
        "design_factor": 1.2,
    },
    "Walnut shell filtration": {
        "unit_kind": "media_filter",
        "recovery": 0.99,
        "energy_intensity": 0.05,
        "filtration_rate": 10.0,
        "bed_depth": 1.0,
        "media_bulk_density": 650.0,
    },
    "Media filtration": {
        "unit_kind": "media_filter",
        "recovery": 0.99,
        "energy_intensity": 0.04,
        "filtration_rate": 8.0,
        "bed_depth": 1.0,
        "media_bulk_density": 1600.0,
    },
    "Cartridge filter": {
        "unit_kind": "cartridge_filter",
        "recovery": 0.995,
        "energy_intensity": 0.02,
        "element_capacity": 20.0,
    },
    "Bag filter": {
        "unit_kind": "cartridge_filter",
        "recovery": 0.995,
        "energy_intensity": 0.015,
        "element_capacity": 40.0,
    },
    "Ultra-fine filtration": {
        "unit_kind": "uf",
        "recovery": 0.97,
        "energy_intensity": 0.10,
        "membrane_flux": 60.0,
        "backwash_fraction": 0.03,
        "chemical_dose": 0.003,
    },
    "Well pumping": {
        "unit_kind": "pump",
        "recovery": 1.0,
        "energy_intensity": 0.0,
        "pump_head": 50.0,
        "pump_efficiency": 0.70,
    },
    "Raw water storage": {
        "unit_kind": "tank",
        "recovery": 0.999,
        "energy_intensity": 0.005,
        "hydraulic_retention_time": 24.0,
        "design_factor": 1.1,
    },
    "Product water storage": {
        "unit_kind": "tank",
        "recovery": 0.999,
        "energy_intensity": 0.005,
        "hydraulic_retention_time": 12.0,
        "design_factor": 1.1,
    },
    "Softening / pH adjustment": {
        "unit_kind": "chemical_clarification",
        "recovery": 0.97,
        "energy_intensity": 0.05,
        "chemical_dose": 0.15,
        "hydraulic_retention_time": 0.75,
        "target_pH": 8.5,
    },
    "Softening / silica control": {
        "unit_kind": "chemical_clarification",
        "recovery": 0.96,
        "energy_intensity": 0.07,
        "chemical_dose": 0.20,
        "hydraulic_retention_time": 1.0,
        "target_pH": 8.8,
    },
    "Antiscalant / pH adjustment": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.005,
        "chemical_dose": 0.005,
        "target_pH": 7.2,
    },
    "Antiscalant dosing": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.003,
    },
    "Air stripping": {
        "unit_kind": "air_stripping",
        "recovery": 0.995,
        "energy_intensity": 0.12,
        "air_water_ratio": 20.0,
        "tower_loading_rate": 25.0,
    },
    "Dechlorination / activated carbon": {
        "unit_kind": "media",
        "recovery": 0.995,
        "energy_intensity": 0.03,
        "empty_bed_contact_time": 6.0,
        "media_bulk_density": 480.0,
        "chemical_dose": 0.001,
    },
    "MD": {
        "unit_kind": "thermal_membrane",
        "recovery": 0.65,
        "energy_intensity": 1.0,
        "thermal_energy_intensity": 80.0,
        "membrane_flux": 5.0,
        "operating_pressure": 1.0,
    },
    "LSRRO": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.70,
        "energy_intensity": 3.9,
        "membrane_flux": 18.0,
        "operating_pressure": 45.0,
    },
    "OARO": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.72,
        "energy_intensity": 4.0,
        "membrane_flux": 12.0,
        "operating_pressure": 48.3,
    },
    "RO": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.75,
        "energy_intensity": 1.8,
        "membrane_flux": 20.0,
        "operating_pressure": 35.0,
    },
    "BWRO": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.80,
        "energy_intensity": 0.9,
        "membrane_flux": 24.0,
        "operating_pressure": 16.0,
    },
    "NF": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.85,
        "energy_intensity": 0.6,
        "membrane_flux": 30.0,
        "operating_pressure": 10.0,
    },
    "Ammonia stripping": {
        "unit_kind": "air_stripping",
        "recovery": 0.995,
        "energy_intensity": 0.12,
        "air_water_ratio": 30.0,
        "tower_loading_rate": 20.0,
    },
    "Ion exchange / EDI": {
        "unit_kind": "ion_exchange",
        "recovery": 0.98,
        "energy_intensity": 0.15,
        "empty_bed_contact_time": 3.0,
        "media_bulk_density": 720.0,
        "regenerant_dose": 0.02,
    },
    "Ion exchange": {
        "unit_kind": "ion_exchange",
        "recovery": 0.99,
        "energy_intensity": 0.04,
        "empty_bed_contact_time": 5.0,
        "media_bulk_density": 720.0,
        "regenerant_dose": 0.02,
    },
    "Boron-selective IX": {
        "unit_kind": "ion_exchange",
        "recovery": 0.99,
        "energy_intensity": 0.04,
        "empty_bed_contact_time": 8.0,
        "media_bulk_density": 700.0,
        "regenerant_dose": 0.03,
    },
    "Solar PV": {
        "unit_kind": "solar_pv",
        "recovery": 1.0,
        "energy_intensity": 0.0,
        "power_capacity": 0.0,
        "capacity_factor": 0.25,
    },
    "Chlorination": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.002,
        "chemical_dose": 0.002,
    },
    "Polishing filter": {
        "unit_kind": "media_filter",
        "recovery": 0.995,
        "energy_intensity": 0.025,
        "filtration_rate": 10.0,
        "bed_depth": 0.8,
        "media_bulk_density": 1600.0,
    },
    "Fine filter": {
        "unit_kind": "cartridge_filter",
        "recovery": 0.995,
        "energy_intensity": 0.02,
        "element_capacity": 20.0,
    },
    "Final filter": {
        "unit_kind": "cartridge_filter",
        "recovery": 0.995,
        "energy_intensity": 0.02,
        "element_capacity": 20.0,
    },
    "pH adjustment": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.004,
        "target_pH": 7.5,
    },
    "Scale inhibitor dosing": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.003,
    },
    "Biocide dosing": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.002,
    },
    "Blending / remineralization": {
        "unit_kind": "blending",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.01,
        "blend_fraction": 0.05,
    },
    "Blending / salinity adjustment": {
        "unit_kind": "blending",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "blend_fraction": 0.10,
    },
    "Adjust TDS": {
        "unit_kind": "blending",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "blend_fraction": 0.05,
    },
    "Additives blending": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.02,
    },
    "Add additives": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.02,
    },
    "Hardness adjustment": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.01,
    },
    "Scale control": {
        "unit_kind": "chemical_dosing",
        "recovery": 1.0,
        "energy_intensity": 0.003,
        "chemical_dose": 0.003,
    },
}


COST_MODEL_DEFAULTS = {
    "Equalization tank": {"capex_per_flow": 48.0, "fixed_opex_fraction": 0.03, "variable_opex_per_m3": 0.005},
    "Floc n Drop": {"capex_per_flow": 104.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.06, "chemical_price": 0.8},
    "Walnut shell filtration": {"capex_per_flow": 168.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.08, "media_replacement_price": 0.6, "media_replacement_fraction": 0.25},
    "Media filtration": {"capex_per_flow": 96.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 0.15, "media_replacement_fraction": 0.10},
    "Cartridge filter": {"capex_per_flow": 36.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 80.0, "media_replacement_fraction": 6.0},
    "Bag filter": {"capex_per_flow": 28.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.03, "media_replacement_price": 35.0, "media_replacement_fraction": 6.0},
    "Ultra-fine filtration": {"capex_per_flow": 180.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.20, "chemical_price": 1.0, "media_replacement_price": 25.0, "media_replacement_fraction": 0.12},
    "Well pumping": {"capex_per_flow": 32.0, "fixed_opex_fraction": 0.03, "variable_opex_per_m3": 0.005},
    "Raw water storage": {"capex_per_flow": 24.0, "fixed_opex_fraction": 0.02, "variable_opex_per_m3": 0.002},
    "Product water storage": {"capex_per_flow": 24.0, "fixed_opex_fraction": 0.02, "variable_opex_per_m3": 0.002},
    "Softening / pH adjustment": {"capex_per_flow": 152.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.08, "chemical_price": 0.25},
    "Softening / silica control": {"capex_per_flow": 168.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.10, "chemical_price": 0.30},
    "Antiscalant / pH adjustment": {"capex_per_flow": 14.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.01, "chemical_price": 2.5},
    "Antiscalant dosing": {"capex_per_flow": 10.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 3.0},
    "Air stripping": {"capex_per_flow": 120.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.04},
    "Dechlorination / activated carbon": {"capex_per_flow": 280.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.20, "chemical_price": 1.0, "media_replacement_price": 2.5, "media_replacement_fraction": 0.5},
    "MD": {"capex_per_flow": 720.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.15, "media_replacement_price": 60.0, "media_replacement_fraction": 0.10},
    "LSRRO": {"capex_per_flow": 480.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.10, "media_replacement_price": 45.0, "media_replacement_fraction": 0.12},
    "OARO": {"capex_per_flow": 600.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.12, "media_replacement_price": 50.0, "media_replacement_fraction": 0.12},
    "RO": {"capex_per_flow": 360.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.08, "media_replacement_price": 40.0, "media_replacement_fraction": 0.12},
    "BWRO": {"capex_per_flow": 260.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.06, "media_replacement_price": 35.0, "media_replacement_fraction": 0.12},
    "NF": {"capex_per_flow": 220.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.05, "media_replacement_price": 35.0, "media_replacement_fraction": 0.12},
    "Ammonia stripping": {"capex_per_flow": 128.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.05},
    "Ion exchange / EDI": {"capex_per_flow": 440.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.35, "chemical_price": 0.5, "media_replacement_price": 5.0, "media_replacement_fraction": 0.25},
    "Ion exchange": {"capex_per_flow": 340.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.25, "chemical_price": 0.5, "media_replacement_price": 4.0, "media_replacement_fraction": 0.20},
    "Boron-selective IX": {"capex_per_flow": 380.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.30, "chemical_price": 0.6, "media_replacement_price": 8.0, "media_replacement_fraction": 0.20},
    "Solar PV": {"capex_per_flow": 0.0, "capex_per_kw": 480.0, "fixed_opex_fraction": 0.02, "variable_opex_per_m3": 0.0},
    "Chlorination": {"capex_per_flow": 12.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 1.0},
    "Polishing filter": {"capex_per_flow": 72.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.03, "media_replacement_price": 0.15, "media_replacement_fraction": 0.10},
    "Fine filter": {"capex_per_flow": 36.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 80.0, "media_replacement_fraction": 6.0},
    "Final filter": {"capex_per_flow": 36.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 80.0, "media_replacement_fraction": 6.0},
    "pH adjustment": {"capex_per_flow": 12.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 0.5},
    "Scale inhibitor dosing": {"capex_per_flow": 10.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 3.0},
    "Biocide dosing": {"capex_per_flow": 10.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 2.5},
    "Blending / remineralization": {"capex_per_flow": 16.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.01, "chemical_price": 0.3},
    "Blending / salinity adjustment": {"capex_per_flow": 14.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005},
    "Adjust TDS": {"capex_per_flow": 14.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005},
    "Additives blending": {"capex_per_flow": 12.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 1.0},
    "Add additives": {"capex_per_flow": 12.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 1.0},
    "Hardness adjustment": {"capex_per_flow": 14.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 0.3},
    "Scale control": {"capex_per_flow": 10.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 3.0},
}


TECHNICAL_INPUT_SPECS = {
    "recovery": ("Hydraulics", "fraction", "Fraction of inlet flow recovered as outlet flow"),
    "energy_intensity": ("Energy", "kWh/m3", "Electricity demand per cubic meter treated"),
    "thermal_energy_intensity": ("Energy", "kWh/m3", "Thermal energy demand per cubic meter treated"),
    "chemical_dose": ("Chemicals", "kg/m3", "Chemical dose per cubic meter treated"),
    "hydraulic_retention_time": ("Hydraulics", "hr", "Hydraulic retention time"),
    "design_factor": ("Hydraulics", "fraction", "Oversizing factor for basin or tank volume"),
    "filtration_rate": ("Filtration", "m/h", "Design filtration loading rate"),
    "bed_depth": ("Filtration", "m", "Media bed depth"),
    "media_bulk_density": ("Media", "kg/m3", "Bulk density of media or resin"),
    "element_capacity": ("Filtration", "m3/day/element", "Nominal cartridge or bag element capacity"),
    "membrane_flux": ("Membrane", "L/m2-h", "Average membrane operating flux"),
    "backwash_fraction": ("Membrane", "fraction", "Backwash or cleaning waste fraction"),
    "pump_head": ("Pumping", "m", "Total dynamic head for pump energy calculation"),
    "pump_efficiency": ("Pumping", "fraction", "Pump wire-to-water efficiency"),
    "target_pH": ("Conditioning", "-", "Target outlet pH when pH is tracked"),
    "air_water_ratio": ("Air stripping", "m3 air/m3 water", "Volumetric air-to-water ratio"),
    "tower_loading_rate": ("Air stripping", "m/h", "Hydraulic loading rate through stripping tower"),
    "operating_pressure": ("Membrane", "bar", "Representative operating pressure"),
    "empty_bed_contact_time": ("Media", "min", "Empty bed contact time"),
    "regenerant_dose": ("Chemicals", "kg/m3", "Regenerant dose normalized to treated flow"),
    "power_capacity": ("Energy", "kW", "Installed PV power capacity"),
    "capacity_factor": ("Energy", "fraction", "Annual average PV capacity factor"),
    "blend_fraction": ("Blending", "fraction", "Supplemental blend or additive stream fraction"),
}


COST_INPUT_SPECS = {
    "capex_per_flow": ("Capital", "$/(m3/day)", "Equipment capital cost per unit daily capacity"),
    "capex_per_kw": ("Capital", "$/kW", "Equipment capital cost per kW capacity"),
    "fixed_opex_fraction": ("Fixed O&M", "fraction/yr", "Annual fixed OPEX as fraction of installed CAPEX"),
    "variable_opex_per_m3": ("Variable O&M", "$/m3", "Variable operating cost per cubic meter treated"),
    "chemical_price": ("Chemicals", "$/kg", "Chemical or regenerant price"),
    "media_replacement_price": ("Replacement", "$/unit", "Replacement media, membrane, cartridge, or bag price"),
    "media_replacement_fraction": ("Replacement", "fraction/yr", "Annual replacement fraction"),
}


TECHNICAL_INPUT_METADATA = {
    "recovery": (
        "WaterTAP zero-order model guidance and site-specific engineering defaults",
        "open source documentation",
    ),
    "energy_intensity": (
        "WaterTAP zero-order model guidance and site-specific energy-use literature",
        "open source documentation",
    ),
    "thermal_energy_intensity": (
        "Membrane distillation and thermal desalination energy-use literature",
        "publication",
    ),
    "chemical_dose": (
        "Water Technologies Handbook and RO chemical dosing guidance",
        "industrial reference",
    ),
    "hydraulic_retention_time": (
        "WaterTAP tank and clarification zero-order defaults; verify by site-specific sizing",
        "open source documentation",
    ),
    "design_factor": (
        "Planning-level engineering sizing allowance; no exact external source",
        "engineering estimate",
    ),
    "filtration_rate": (
        "Hach Granular Media Filtration for Water Treatment Applications 2012",
        "industrial report",
    ),
    "bed_depth": (
        "Hach Granular Media Filtration for Water Treatment Applications 2012",
        "industrial report",
    ),
    "media_bulk_density": (
        "WaterTAP media and ion-exchange defaults plus supplier media datasheets",
        "vendor data",
    ),
    "element_capacity": (
        "WaterTAP Cartridge Filtration ZO defaults and vendor element sizing practice",
        "open source documentation",
    ),
    "membrane_flux": (
        "EPA RO/NF WBS cost model and WaterTAP membrane model defaults",
        "technical report",
    ),
    "backwash_fraction": (
        "WaterTAP Ultra Filtration ZO documentation and membrane treatment literature",
        "open source documentation",
    ),
    "pump_head": (
        "Hydraulic pump energy calculation; use site-specific total dynamic head",
        "engineering calculation",
    ),
    "pump_efficiency": (
        "Hydraulic pump energy calculation; use pump vendor curve when available",
        "engineering calculation",
    ),
    "target_pH": (
        "Water Technologies Handbook precipitation softening and pH adjustment practice",
        "industrial reference",
    ),
    "air_water_ratio": (
        "WaterTAP air stripping and decarbonator zero-order defaults",
        "open source documentation",
    ),
    "tower_loading_rate": (
        "WaterTAP air stripping and decarbonator zero-order defaults",
        "open source documentation",
    ),
    "operating_pressure": (
        "USBR brackish groundwater RO/NF comparison and membrane desalination literature",
        "technical report",
    ),
    "empty_bed_contact_time": (
        "US EPA WBS GAC cost model 2024 and WQA GAC Fact Sheet",
        "technical report",
    ),
    "regenerant_dose": (
        "Veolia ion exchange handbook and US EPA WBS IX cost model",
        "industrial reference",
    ),
    "power_capacity": (
        "LBNL Utility-Scale Solar 2024 Edition",
        "technical report",
    ),
    "capacity_factor": (
        "LBNL Utility-Scale Solar 2024 Edition",
        "technical report",
    ),
    "blend_fraction": (
        "Site-specific blending design assumption; no exact external source",
        "engineering estimate",
    ),
}


TECHNICAL_INPUT_METADATA_BY_UNIT = {
    "MD": {
        "recovery": (
            "Membrane distillation energy and cost literature; waste-heat integration case studies",
            "publication",
        ),
        "energy_intensity": (
            "Waste heat driven integrated membrane distillation study and MD energy review",
            "publication",
        ),
        "thermal_energy_intensity": (
            "Waste heat driven integrated membrane distillation study and MD energy review",
            "publication",
        ),
        "membrane_flux": (
            "Membrane distillation review and waste-heat MD case-study flux ranges",
            "publication",
        ),
        "operating_pressure": (
            "Membrane distillation low-pressure operation assumption",
            "engineering estimate",
        ),
    },
    "LSRRO": {
        "recovery": (
            "Atia et al. 2023 Cost optimization of low-salt-rejection reverse osmosis",
            "publication",
        ),
        "energy_intensity": (
            "Atia et al. 2023 Cost optimization of low-salt-rejection reverse osmosis",
            "publication",
        ),
        "membrane_flux": (
            "WaterTAP LSRRO flowsheet documentation and LSRRO TEA literature",
            "open source documentation",
        ),
        "operating_pressure": (
            "WaterTAP LSRRO flowsheet documentation and LSRRO TEA literature",
            "open source documentation",
        ),
    },
    "OARO": {
        "recovery": (
            "OARO five-approach brine dewatering study reporting 72 percent recovery at 35 g/L feed",
            "publication",
        ),
        "energy_intensity": (
            "OARO five-approach brine dewatering study reporting approximately 4 kWh/m3",
            "publication",
        ),
        "membrane_flux": (
            "WaterTAP OARO flowsheet documentation and OARO brine dewatering literature",
            "open source documentation",
        ),
        "operating_pressure": (
            "OARO five-approach brine dewatering study using 48.3 bar membrane pressure limit",
            "publication",
        ),
    },
    "RO": {
        "recovery": (
            "EPA RO/NF WBS cost model and USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "energy_intensity": (
            "USBR brackish groundwater RO/NF comparison and RO energy literature",
            "technical report",
        ),
        "operating_pressure": (
            "USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
    },
    "BWRO": {
        "recovery": (
            "USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "energy_intensity": (
            "USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "operating_pressure": (
            "USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
    },
    "NF": {
        "recovery": (
            "EPA RO/NF WBS cost model and USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "energy_intensity": (
            "USBR brackish groundwater RO/NF comparison showing lower NF pressure and energy",
            "technical report",
        ),
        "operating_pressure": (
            "USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
    },
    "Ion exchange / EDI": {
        "empty_bed_contact_time": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "media_bulk_density": (
            "Ion exchange resin supplier data and US EPA WBS IX model",
            "vendor data",
        ),
        "regenerant_dose": (
            "Veolia ion exchange handbook and US EPA WBS IX model",
            "industrial reference",
        ),
    },
    "Ion exchange": {
        "empty_bed_contact_time": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "media_bulk_density": (
            "Ion exchange resin supplier data and US EPA WBS IX model",
            "vendor data",
        ),
        "regenerant_dose": (
            "Veolia ion exchange handbook and US EPA WBS IX model",
            "industrial reference",
        ),
    },
    "Boron-selective IX": {
        "empty_bed_contact_time": (
            "US EPA WBS Ion Exchange PFAS cost model 2024 and boron-selective resin guidance",
            "technical report",
        ),
        "media_bulk_density": (
            "Boron-selective ion exchange resin supplier data",
            "vendor data",
        ),
        "regenerant_dose": (
            "Veolia ion exchange handbook and boron-selective IX regeneration guidance",
            "industrial reference",
        ),
    },
    "Dechlorination / activated carbon": {
        "empty_bed_contact_time": (
            "WQA GAC Fact Sheet and US EPA WBS GAC cost model 2024",
            "technical report",
        ),
        "media_bulk_density": (
            "GAC supplier datasheets and WQA GAC Fact Sheet",
            "vendor data",
        ),
    },
}


COST_INPUT_METADATA = {
    "capex_per_flow": (
        "US EPA Drinking Water Treatment Technology Unit Cost Models WBS method",
        "technical report",
    ),
    "capex_per_kw": (
        "LBNL Utility-Scale Solar 2024 Edition and NREL ATB-style PV cost assumptions",
        "technical report",
    ),
    "fixed_opex_fraction": (
        "US EPA WBS cost-model O&M categories and planning-level allowance",
        "technical report",
    ),
    "variable_opex_per_m3": (
        "US EPA WBS cost-model O&M categories and WaterTAP zero-order cost defaults",
        "technical report",
    ),
    "chemical_price": (
        "Chemical vendor pricing assumption; verify with project quote",
        "vendor data",
    ),
    "media_replacement_price": (
        "EPA WBS replacement cost framework and supplier media pricing",
        "technical report",
    ),
    "media_replacement_fraction": (
        "EPA WBS O&M replacement framework; site-specific lifetime should override",
        "technical report",
    ),
}


COST_INPUT_METADATA_BY_UNIT = {
    "MD": {
        "capex_per_flow": (
            "Membrane distillation energy and cost literature with waste-heat integration cases",
            "publication",
        ),
        "variable_opex_per_m3": (
            "Membrane distillation energy and cost literature with waste-heat integration cases",
            "publication",
        ),
        "media_replacement_price": (
            "Membrane distillation module replacement planning estimate",
            "engineering estimate",
        ),
    },
    "LSRRO": {
        "capex_per_flow": (
            "Atia et al. 2023 LSRRO cost optimization and WaterTAP costing framework",
            "publication",
        ),
        "variable_opex_per_m3": (
            "Atia et al. 2023 LSRRO cost optimization and WaterTAP costing framework",
            "publication",
        ),
    },
    "OARO": {
        "capex_per_flow": (
            "OARO brine dewatering TEA literature and WaterTAP OARO flowsheet context",
            "publication",
        ),
        "variable_opex_per_m3": (
            "OARO brine dewatering TEA literature and WaterTAP OARO flowsheet context",
            "publication",
        ),
    },
    "RO": {
        "capex_per_flow": (
            "US EPA WBS RO/NF cost model",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS RO/NF cost model membrane O&M assumptions",
            "technical report",
        ),
    },
    "BWRO": {
        "capex_per_flow": (
            "US EPA WBS RO/NF cost model and USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS RO/NF cost model membrane O&M assumptions",
            "technical report",
        ),
    },
    "NF": {
        "capex_per_flow": (
            "US EPA WBS RO/NF cost model and USBR brackish groundwater RO/NF comparison",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS RO/NF cost model membrane O&M assumptions",
            "technical report",
        ),
    },
    "Ion exchange / EDI": {
        "capex_per_flow": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "media_replacement_price": (
            "Ion exchange resin supplier pricing and US EPA WBS IX model",
            "vendor data",
        ),
    },
    "Ion exchange": {
        "capex_per_flow": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS Ion Exchange PFAS cost model 2024",
            "technical report",
        ),
        "media_replacement_price": (
            "Ion exchange resin supplier pricing and US EPA WBS IX model",
            "vendor data",
        ),
    },
    "Boron-selective IX": {
        "capex_per_flow": (
            "US EPA WBS Ion Exchange PFAS cost model 2024 and boron-selective IX vendor guidance",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS Ion Exchange PFAS cost model 2024 and boron-selective IX vendor guidance",
            "technical report",
        ),
        "media_replacement_price": (
            "Boron-selective resin supplier pricing assumption",
            "vendor data",
        ),
    },
    "Solar PV": {
        "capex_per_kw": (
            "LBNL Utility-Scale Solar 2024 Edition and NREL ATB-style PV cost assumptions",
            "technical report",
        ),
        "fixed_opex_fraction": (
            "NREL ATB-style fixed O&M planning assumption",
            "technical report",
        ),
    },
    "Dechlorination / activated carbon": {
        "capex_per_flow": (
            "US EPA WBS GAC cost model 2024",
            "technical report",
        ),
        "variable_opex_per_m3": (
            "US EPA WBS GAC cost model 2024",
            "technical report",
        ),
        "media_replacement_price": (
            "US EPA WBS GAC cost model 2024 and GAC supplier pricing",
            "vendor data",
        ),
    },
}


TECHNICAL_INPUT_ORDER = [
    "recovery",
    "energy_intensity",
    "thermal_energy_intensity",
    "chemical_dose",
    "hydraulic_retention_time",
    "design_factor",
    "filtration_rate",
    "bed_depth",
    "media_bulk_density",
    "element_capacity",
    "membrane_flux",
    "backwash_fraction",
    "pump_head",
    "pump_efficiency",
    "target_pH",
    "air_water_ratio",
    "tower_loading_rate",
    "operating_pressure",
    "empty_bed_contact_time",
    "regenerant_dose",
    "power_capacity",
    "capacity_factor",
    "blend_fraction",
]

COST_INPUT_ORDER = [
    "capex_per_flow",
    "capex_per_kw",
    "fixed_opex_fraction",
    "variable_opex_per_m3",
    "chemical_price",
    "media_replacement_price",
    "media_replacement_fraction",
]


def supports_technical(unit_process):
    return unit_process in TECHNICAL_MODEL_DEFAULTS


def supports_cost(unit_process):
    return unit_process in COST_MODEL_DEFAULTS


def technical_defaults(unit_process):
    return TECHNICAL_MODEL_DEFAULTS[unit_process]


def cost_defaults(unit_process):
    return COST_MODEL_DEFAULTS[unit_process]


def _metadata_for(metadata_by_unit, metadata_by_parameter, unit_process, parameter):
    return metadata_by_unit.get(unit_process, {}).get(
        parameter,
        metadata_by_parameter.get(parameter, ("", "")),
    )


def technical_input_rows(unit_process):
    defaults = TECHNICAL_MODEL_DEFAULTS.get(unit_process)
    if not defaults:
        return []
    rows = []
    for parameter in TECHNICAL_INPUT_ORDER:
        if parameter not in defaults:
            continue
        sub_section, unit, description = TECHNICAL_INPUT_SPECS[parameter]
        source, data_type = _metadata_for(
            TECHNICAL_INPUT_METADATA_BY_UNIT,
            TECHNICAL_INPUT_METADATA,
            unit_process,
            parameter,
        )
        rows.append((
            sub_section,
            parameter,
            defaults[parameter],
            unit,
            description,
            source,
            data_type,
        ))
    return rows


def cost_input_rows(unit_process):
    defaults = COST_MODEL_DEFAULTS.get(unit_process)
    if not defaults:
        return []
    rows = []
    for parameter in COST_INPUT_ORDER:
        if parameter not in defaults:
            continue
        sub_section, unit, description = COST_INPUT_SPECS[parameter]
        source, data_type = _metadata_for(
            COST_INPUT_METADATA_BY_UNIT,
            COST_INPUT_METADATA,
            unit_process,
            parameter,
        )
        rows.append((
            sub_section,
            parameter,
            defaults[parameter],
            unit,
            description,
            source,
            data_type,
        ))
    return rows
