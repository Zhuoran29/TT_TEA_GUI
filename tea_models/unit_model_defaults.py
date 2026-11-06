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
    "Chemical softening": {
        "unit_kind": "chemical_softening",
        "lime_dose_mg_l": 10.0,
        "soda_ash_dose_mg_l": 4301.0,
        "target_neutral_pH": 8.0,
        "acid_dose_override_mg_l": 0.0,
        "energy_intensity": 0.223,
        "sludge_solids_content": 0.10,
    },
    "Electrocoagulation": {
        "unit_kind": "electrocoagulation",
        "current_density_mA_cm2": 20.0,
        "electrode_gap_m": 0.02,
        "hydraulic_retention_time": 30.0,
        "energy_intensity": 0.0,
        "sludge_solids_content": 0.025,
    },
    "Walnut shell filtration": {
        "unit_kind": "wsf",
        "recovery": 0.99,
        "energy_intensity": 0.17,
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
    "Ultrafiltration": {
        "unit_kind": "membrane_filtration",
        "recovery": 0.99,
        "sodium_bisulfite_dose_mg_l": 5.0,
        "pump_tdh_ft": 50.0,
        "pump_efficiency": 0.75,
        "motor_efficiency": 0.95,
        "vfd_factor": 0.98,
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
    "Vacuum membrane distillation (VMD)": {
        "unit_kind": "thermal_membrane",
        "recovery": 0.50,
        "feed_temperature": 25.0,
    },
    "LSRRO": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.0,
        "clip_negative_permeate": 1.0,
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
        "feed_tds_g_l": 0.8,
        "feed_temperature": 25.0,
        "array_stages": 0,
        "elements_per_vessel": 6,
        "design_flux_lmh": 18.0,
        "concentration_polarization": 1.05,
        "fouling_factor": 0.85,
        "high_pressure_pump_efficiency": 0.85,
        "feed_pump_efficiency": 0.80,
        "feed_pump_pressure_bar": 1.0,
        "piping_loss_bar": 0.5,
        "has_erd": 0,
        "erd_efficiency": 0.95,
        "pretreatment_energy_intensity": 0.0,
    },
    "NF": {
        "unit_kind": "pressure_membrane",
        "recovery": 0.85,
        "energy_intensity": 0.6,
        "membrane_flux": 30.0,
        "operating_pressure": 10.0,
    },
    "Ammonia stripping": {
        "unit_kind": "ammonia_stripping",
        "recovery": 0.995,
        "energy_intensity": 0.12,
        "feed_temperature": 68.0,
        "target_ammonia_mg_l": 1.0,
        "henry_cp_25c": 0.59,
        "henry_conversion_factor": 2479.0,
        "stripping_design_factor": 20.0,
        "kla_s": 6.3611111111111114e-5,
        "tower_diameter_in": 10.0,
    },
    "GAC": {
        "unit_kind": "gac",
        "recovery": 0.995,
        "empty_bed_contact_time": 10.0,
        "max_bed_volume_per_vessel": 40.0,
        "redundant_vessels": 1.0,
        "media_bulk_density": 400.0,
        "bv_coefficient_a": 1.5e5,
        "bv_exponent_b": -1.85,
        "pump_head": 10.0,
        "pump_efficiency": 0.70,
    },
    "Zeolite": {
        "unit_kind": "zeolite",
        "recovery": 0.995,
        "empty_bed_contact_time": 20.0,
        "regenerant_bed_volumes": 90.0,
        "brine_reuse_cycles": 5.0,
        "nacl_mass_fraction": 0.10,
        "naoh_to_nitrogen_molar_ratio": 1.0,
        "aec_mg_n_g": 4.0,
        "pump_head": 10.0,
        "pump_efficiency": 0.70,
    },
    "DAF": {
        "unit_kind": "daf",
        "recycle_ratio": 0.12,
        "pump_head": 51.0,
        "pump_efficiency": 0.70,
        "auxiliary_energy_intensity": 0.02,
        "h2o2_to_iron_ratio": 1.75,
        "ach_aluminum_content": 0.124,
        "cod_to_toc_ratio": 4.0,
        "float_solids_content": 0.03,
    },
    "Ion exchange / EDI": {
        "unit_kind": "ion_exchange",
        "recovery": 0.98,
        "energy_intensity": 0.0,
        "pressure_drop_psi": 95.0,
        "pump_efficiency": 0.70,
        "auxiliary_energy_intensity": 0.29,
        "empty_bed_contact_time": 3.0,
        "media_bulk_density": 720.0,
        "regenerant_dose": 0.02,
    },
    "Ion exchange": {
        "unit_kind": "ion_exchange",
        "bed_removal": 0.99,
        "cation_empty_bed_contact_time": 2.5,
        "cation_capacity": 1.24,
        "cation_regenerant_dose": 240.0,
        "cation_regenerant_concentration": 107.8,
        "cation_rinse_bed_volumes": 12.0,
        "cation_backwash_bed_volumes": 3.0,
        "cation_max_bed_volumes": 1000.0,
        "anion_empty_bed_contact_time": 2.0,
        "anion_capacity": 0.8,
        "anion_regenerant_dose": 128.0,
        "anion_regenerant_concentration": 59.9,
        "anion_rinse_bed_volumes": 7.0,
        "anion_backwash_bed_volumes": 1.2,
        "anion_max_bed_volumes": 3000.0,
        "pump_head": 10.0,
        "pump_efficiency": 0.70,
    },
    "Ion exchange (demineralization)": {
        "unit_kind": "ion_exchange_demineralization",
        "bed_removal": 0.99,
        "cation_empty_bed_contact_time": 2.5,
        "cation_capacity": 1.0,
        "cation_regenerant_dose": 100.0,
        "cation_regenerant_concentration": 51.0,
        "cation_rinse_bed_volumes": 7.0,
        "cation_backwash_bed_volumes": 1.2,
        "cation_max_bed_volumes": 1000.0,
        "anion_empty_bed_contact_time": 2.0,
        "anion_capacity": 0.5,
        "anion_regenerant_dose": 100.0,
        "anion_regenerant_concentration": 42.0,
        "anion_rinse_bed_volumes": 7.0,
        "anion_backwash_bed_volumes": 1.2,
        "anion_max_bed_volumes": 1000.0,
        "pump_head": 10.0,
        "pump_efficiency": 0.70,
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
    "Chemical softening": {
        "reference_direct_cs_capex": 25829456.94,
        "reference_capacity": 3785.41,
        "capex_scaling_exponent": 0.87,
        "lime_price": 0.05,
        "soda_ash_price": 0.45,
        "h2so4_price": 0.043,
        "installation_factor": 1.43,
        "maintenance_fraction": 0.02,
        "om_contingency_factor": 0.20,
    },
    "Electrocoagulation": {
        "reference_ec_capex": 1595666.0,
        "reference_capacity": 11356.0,
        "capex_scaling_exponent": 0.87,
        "installation_factor": 1.0,
        "aluminum_price": 2.23,
        "maintenance_fraction": 0.03,
        "om_contingency_factor": 0.20,
    },
    "Walnut shell filtration": {
        "reference_capex_cost_per_bbl": 0.008993,
        "capex_scaling_exponent": 0.87,
        "installation_factor": 1.0,
        "media_cleaning_cost_per_m3": 0.0546,
        "maintenance_fraction": 0.03,
        "om_contingency_factor": 0.20,
    },
    "Media filtration": {"capex_per_flow": 96.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 0.15, "media_replacement_fraction": 0.10},
    "Cartridge filter": {"capex_per_flow": 36.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.04, "media_replacement_price": 80.0, "media_replacement_fraction": 6.0},
    "Bag filter": {"capex_per_flow": 28.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.03, "media_replacement_price": 35.0, "media_replacement_fraction": 6.0},
    "Ultra-fine filtration": {"capex_per_flow": 180.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.20, "chemical_price": 1.0, "media_replacement_price": 25.0, "media_replacement_fraction": 0.12},
    "Ultrafiltration": {
        "reference_uf_flow_gpd": 970000.0,
        "uf_equipment_unit_cost": 2.0,
        "uf_building_unit_cost": 300.0,
        "reference_building_area_ft2": 2000.0,
        "capex_scaling_exponent": 0.87,
        "installation_factor": 1.43,
        "sodium_bisulfite_price": 0.25,
        "maintenance_fraction": 0.02,
        "om_contingency_factor": 0.20,
    },
    "Well pumping": {"capex_per_flow": 32.0, "fixed_opex_fraction": 0.03, "variable_opex_per_m3": 0.005},
    "Raw water storage": {"capex_per_flow": 24.0, "fixed_opex_fraction": 0.02, "variable_opex_per_m3": 0.002},
    "Product water storage": {"capex_per_flow": 24.0, "fixed_opex_fraction": 0.02, "variable_opex_per_m3": 0.002},
    "Antiscalant / pH adjustment": {"capex_per_flow": 14.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.01, "chemical_price": 2.5},
    "Antiscalant dosing": {"capex_per_flow": 10.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.005, "chemical_price": 3.0},
    "Air stripping": {"capex_per_flow": 120.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.04},
    "Dechlorination / activated carbon": {"capex_per_flow": 280.0, "fixed_opex_fraction": 0.04, "variable_opex_per_m3": 0.20, "chemical_price": 1.0, "media_replacement_price": 2.5, "media_replacement_fraction": 0.5},
    "Vacuum membrane distillation (VMD)": {
        "low_pressure_pump_cost": 889.0,
        "heat_exchanger_material_factor": 1.0,
        "heat_exchanger_unit_cost": 300.0,
        "mixer_unit_cost": 361.0,
        "heater_unit_cost": 0.066,
        "chiller_unit_cost": 0.20,
        "chiller_cop": 7.0,
        "membrane_cost": 56.0,
        "membrane_replacement_fraction": 0.20,
        "fixed_opex_fraction": 0.03,
    },
    "MVC": {"capex_per_flow": 2100.0, "column_capex_multiplier": 1.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.0},
    "LSRRO": {
        "reference_flow_m3_day": 7949.36,
        "capex_scaling_exponent": 0.81,
        "installation_factor": 2.0,
        "maintenance_fraction": 0.02,
        "antiscalant_dose_mg_l": 3.0,
        "antiscalant_unit_price": 61.40,
        "antiscalant_density_kg_l": 1.10,
        "cip_cost_per_m3_product": 0.07,
        "om_contingency_factor": 0.20,
    },
    "OARO": {"capex_per_flow": 600.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.12, "media_replacement_price": 50.0, "media_replacement_fraction": 0.12},
    "RO": {"capex_per_flow": 360.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.08, "media_replacement_price": 40.0, "media_replacement_fraction": 0.12},
    "BWRO": {
        "total_installed_cost": 0.0,
        "unit_capex": 0.0,
        "reference_unit_capex": 1500.0,
        "reference_capacity": 1000.0,
        "capex_scaling_exponent": -0.15,
        "cost_index_factor": 1.0,
        "fixed_om_fraction": 0.035,
        "insurance_fraction": 0.005,
        "membrane_cost": 30.0,
        "membrane_replacement_fraction": 0.20,
        "chemical_cost_per_m3_product": 0.03,
        "labor_cost_per_m3_product": 0.05,
        "pretreatment_cost_per_m3_product": 0.0,
        "posttreatment_cost_per_m3_product": 0.0,
        "other_variable_cost_per_m3_product": 0.0,
        "intake_water_cost_per_m3_feed": 0.0,
        "brine_disposal_cost_per_m3_concentrate": 0.0,
    },
    "NF": {"capex_per_flow": 220.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.05, "media_replacement_price": 35.0, "media_replacement_fraction": 0.12},
    "Ammonia stripping": {"capital_cost_multiplier": 1.0, "opex_cost_multiplier": 1.0, "variable_opex_per_m3": 0.0},
    "GAC": {
        "installation_factor": 1.15,
        "gac_replacement_cost": 4.58223,
        "gac_regeneration_cost": 4.28352,
        "regeneration_fraction": 0.80,
        "maintenance_fraction": 0.03,
        "om_contingency_factor": 0.20,
    },
    "Zeolite": {
        "capex_coefficient": 3305.1,
        "capex_exponent": 0.6961,
        "installation_factor": 1.15,
        "maintenance_fraction": 0.02,
        "om_contingency_factor": 0.20,
        "zeolite_price": 4.41,
        "media_replacement_fraction_per_cycle": 0.0,
    },
    "DAF": {
        "capex_scaling_exponent": 0.87,
        "installation_factor": 1.0,
        "maintenance_fraction": 0.03,
        "om_contingency_factor": 0.20,
        "ach_price": 0.4506,
        "polymer_price": 1.6344,
        "h2o2_price": 1.3986,
    },
    "Ion exchange / EDI": {"capex_per_flow": 440.0, "column_capex_multiplier": 1.0, "fixed_opex_fraction": 0.05, "variable_opex_per_m3": 0.35, "chemical_price": 0.5, "media_replacement_price": 5.0, "media_replacement_fraction": 0.25},
    "Ion exchange": {
        "cation_capex_coefficient": 698.35,
        "cation_capex_exponent": 0.7478,
        "anion_capex_coefficient": 673.45,
        "anion_capex_exponent": 0.7282,
        "installation_factor": 1.15,
        "cation_resin_price": 8175.0,
        "anion_resin_price": 8198.0,
        "resin_life": 7.0,
        "annual_resin_loss": 0.045,
        "salt_price": 230.3,
        "maintenance_fraction": 0.02,
        "om_contingency_factor": 0.20,
    },
    "Ion exchange (demineralization)": {
        "cation_capex_coefficient": 698.35,
        "cation_capex_exponent": 0.7478,
        "anion_capex_coefficient": 673.45,
        "anion_capex_exponent": 0.7282,
        "installation_factor": 1.15,
        "cation_resin_price": 8175.0,
        "anion_resin_price": 8198.0,
        "resin_life": 7.0,
        "annual_resin_loss": 0.045,
        "hcl_price": 1085.9,
        "caustic_price": 940.3,
        "maintenance_fraction": 0.02,
        "om_contingency_factor": 0.20,
    },
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
    "reference_flow_bbl_day": ("Design basis", "bbl/day", "Reference LSRRO flow basis for scaling model inputs"),
    "gross_pump_power_kw": ("Energy", "kW", "Gross pump power at the reference flow"),
    "energy_recovery_fraction": ("Energy recovery", "fraction", "Fraction of gross pump power recovered by the ERD"),
    "pressure_override_psi": ("Membrane", "psi", "Optional operating-pressure override; 0 uses TDS lookup"),
    "stage_override": ("Membrane", "count", "Optional stage-count override; 0 uses TDS lookup"),
    "clip_negative_permeate": ("Water quality", "0/1", "Clip negative regression-predicted permeate concentrations to zero"),
    "lime_dose_mg_l": ("Chemicals", "mg/L", "Lime dose as Ca(OH)2 product"),
    "soda_ash_dose_mg_l": ("Chemicals", "mg/L", "Soda ash dose as Na2CO3 product"),
    "target_neutral_pH": ("Conditioning", "-", "Target pH after acid neutralization"),
    "acid_dose_override_mg_l": ("Chemicals", "mg/L", "Optional H2SO4 dose override; 0 auto-calculates to target pH"),
    "current_density_mA_cm2": ("Electrodes", "mA/cm2", "EC aluminum-electrode current density"),
    "electrode_gap_m": ("Electrodes", "m", "Electrode gap used in solution-resistance estimate"),
    "energy_intensity": ("Energy", "kWh/m3", "Electricity demand per cubic meter treated"),
    "auxiliary_energy_intensity": ("Energy", "kWh/m3", "Regeneration, controls, EDI, or other auxiliary electricity demand"),
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
    "sodium_bisulfite_dose_mg_l": ("Chemicals", "mg/L", "Sodium bisulfite dose at UF"),
    "pump_tdh_ft": ("Pumping", "ft", "UF pump total dynamic head"),
    "motor_efficiency": ("Pumping", "fraction", "Motor efficiency"),
    "vfd_factor": ("Pumping", "factor", "VFD or constant motor factor"),
    "pump_head": ("Pumping", "m", "Total dynamic head for pump energy calculation"),
    "recycle_ratio": ("Hydraulics", "fraction", "Pressurised recycle flow as a fraction of inlet flow"),
    "h2o2_to_iron_ratio": ("Chemicals", "mg H2O2/mg Fe", "H2O2 dose per mg of feed iron"),
    "ach_aluminum_content": ("Chemicals", "fraction", "Aluminum mass fraction of the ACH product"),
    "cod_to_toc_ratio": ("Water quality", "mg COD/mg TOC", "COD to TOC ratio used to report COD"),
    "float_solids_content": ("Residuals", "fraction", "Dry solids mass fraction of the skimmed float"),
    "sludge_solids_content": ("Residuals", "fraction", "Dry solids mass fraction of the sludge; sets sludge volume and water recovery"),
    "pressure_drop_psi": ("Pumping", "psi", "WaterTAP-style resin bed and column pressure drop"),
    "pump_efficiency": ("Pumping", "fraction", "Pump wire-to-water efficiency"),
    "target_pH": ("Conditioning", "-", "Target outlet pH when pH is tracked"),
    "air_water_ratio": ("Air stripping", "m3 air/m3 water", "Volumetric air-to-water ratio"),
    "tower_loading_rate": ("Air stripping", "m/h", "Hydraulic loading rate through stripping tower"),
    "operating_pressure": ("Membrane", "bar", "Representative operating pressure"),
    "empty_bed_contact_time": ("Media", "min", "Empty bed contact time"),
    "max_bed_volume_per_vessel": ("Design", "m3", "Maximum bed volume per pressure vessel; larger beds are split into parallel vessels"),
    "redundant_vessels": ("Design", "count", "Off-line redundant vessels (costed as contactors, not filled with carbon)"),
    "regenerant_bed_volumes": ("Regeneration", "bed volumes", "Brine volume applied per regeneration, in bed volumes"),
    "brine_reuse_cycles": ("Regeneration", "count", "Number of regenerations each brine batch is reused before disposal"),
    "aec_mg_n_g": ("Media", "mg N/g zeolite", "Ammonium exchange capacity used to size the zeolite mass loaded per cycle"),
    "nacl_mass_fraction": ("Regeneration", "fraction", "NaCl mass fraction of the regeneration brine"),
    "naoh_to_nitrogen_molar_ratio": ("Regeneration", "mol/mol", "NaOH added per mole of NH4-N eluted, to hold the brine at pH 11"),
    "bv_coefficient_a": ("Bed-life model", "bed volumes", "Coefficient A in the NMSU bed-life law BV = A x TOC^b (TOC in mg/L)"),
    "bv_exponent_b": ("Bed-life model", "-", "Exponent b in the NMSU bed-life law BV = A x TOC^b"),
    "ammonia_removal": ("Performance", "fraction", "Target NH3-N removal used for zeolite breakthrough sizing"),
    "regenerant_dose": ("Chemicals", "kg/m3", "Regenerant dose normalized to treated flow"),
    "power_capacity": ("Energy", "kW", "Installed PV power capacity"),
    "capacity_factor": ("Energy", "fraction", "Annual average PV capacity factor"),
    "blend_fraction": ("Blending", "fraction", "Supplemental blend or additive stream fraction"),
    "feed_tds_g_l": ("Feed", "g/L", "Fallback feed TDS when the stream has no TDS value"),
    "feed_temperature": ("Feed", "deg C", "Feed temperature"),
    "target_ammonia_mg_l": ("Performance", "mg/L", "Target ammonia-nitrogen concentration after ammonia stripping"),
    "henry_cp_25c": ("Air stripping", "mol/m3/Pa", "Henry's law constant for ammonia at 25 deg C"),
    "henry_conversion_factor": ("Air stripping", "factor", "Conversion from H_cp to the worksheet dimensionless gas/liquid basis"),
    "stripping_design_factor": ("Air stripping", "factor", "Safety factor applied to the minimum air-to-water ratio"),
    "kla_s": ("Air stripping", "1/s", "Overall liquid-side mass-transfer coefficient"),
    "tower_diameter_in": ("Air stripping", "in", "Tower diameter used in packed-height sizing"),
    "array_stages": ("Membrane array", "count", "Concentrate stages; 0 selects automatically"),
    "elements_per_vessel": ("Membrane array", "count", "Membrane elements per pressure vessel"),
    "design_flux_lmh": ("Membrane array", "L/m2-h", "Selected design permeate flux"),
    "concentration_polarization": ("Membrane", "factor", "Concentration-polarization factor"),
    "fouling_factor": ("Membrane", "fraction", "Membrane permeability fouling allowance"),
    "high_pressure_pump_efficiency": ("Pumps", "fraction", "High-pressure pump efficiency"),
    "feed_pump_efficiency": ("Pumps", "fraction", "Intake/feed pump efficiency"),
    "feed_pump_pressure_bar": ("Pumps", "bar", "Feed-pump discharge pressure"),
    "piping_loss_bar": ("Pumps", "bar", "High-pressure piping loss allowance"),
    "has_erd": ("Energy recovery", "0/1", "Enable concentrate energy recovery device"),
    "erd_efficiency": ("Energy recovery", "fraction", "Energy recovery device efficiency"),
    "pretreatment_energy_intensity": ("Energy", "kWh/m3 product", "BWRO-island pretreatment energy not modeled in upstream units"),
    "bed_removal": ("Performance", "fraction", "Removal of the target ions in the water passing through the beds; the rest of the flow bypasses"),
    "cation_empty_bed_contact_time": ("Cation bed", "min", "Empty bed contact time of the cation bed"),
    "cation_capacity": ("Cation bed", "eq/L resin", "Usable exchange capacity of the cation resin at the regenerant dose"),
    "cation_regenerant_dose": ("Cation bed", "g/L resin", "Regenerant applied per regeneration (NaCl, or HCl for demineralization)"),
    "cation_regenerant_concentration": ("Cation bed", "g/L", "Regenerant solution concentration; sets the regenerant volume"),
    "cation_rinse_bed_volumes": ("Cation bed", "bed volumes", "Slow and fast rinse volume per regeneration"),
    "cation_backwash_bed_volumes": ("Cation bed", "bed volumes", "Backwash volume per regeneration"),
    "cation_max_bed_volumes": ("Cation bed", "bed volumes", "Maximum run length between regenerations"),
    "anion_empty_bed_contact_time": ("Anion bed", "min", "Empty bed contact time of the anion bed"),
    "anion_capacity": ("Anion bed", "eq/L resin", "Usable exchange capacity of the anion resin at the regenerant dose"),
    "anion_regenerant_dose": ("Anion bed", "g/L resin", "Regenerant applied per regeneration (NaCl, or NaOH for demineralization)"),
    "anion_regenerant_concentration": ("Anion bed", "g/L", "Regenerant solution concentration; sets the regenerant volume"),
    "anion_rinse_bed_volumes": ("Anion bed", "bed volumes", "Slow and fast rinse volume per regeneration"),
    "anion_backwash_bed_volumes": ("Anion bed", "bed volumes", "Backwash volume per regeneration"),
    "anion_max_bed_volumes": ("Anion bed", "bed volumes", "Maximum run length between regenerations"),
}


COST_INPUT_SPECS = {
    "reference_direct_membrane_capex": ("Capital", "$(2024)", "Reference direct membrane CAPEX at the LSRRO reference flow"),
    "reference_direct_cs_capex": ("Capital", "$(2024)", "Reference direct chemical-softening CAPEX"),
    "reference_ec_capex": ("Capital", "$(2024)", "Reference EC CAPEX at the reference capacity"),
    "installation_factor": ("Capital", "-", "Unit-level installation factor (TIC) applied to all direct capital items"),
    "reference_flow_bbl_day": ("Capital", "bbl/day", "Reference flow basis for bbl/day CAPEX scaling"),
    "reference_flow_m3_day": ("Capital", "m3/day", "Reference flow for CAPEX scaling"),
    "reference_capex_cost_per_bbl": ("Capital", "$(2020)/bbl", "Annualized WSF CAPEX at the reference flow"),
    "reference_opex_cost_per_bbl": ("Variable O&M", "$(2022)/bbl", "Reference WSF operating cost"),
    "reference_uf_flow_gpd": ("Capital", "gpd", "Reference UF flow basis"),
    "uf_equipment_unit_cost": ("Capital", "$(2024)/gpd", "UF equipment unit CAPEX"),
    "uf_building_unit_cost": ("Capital", "$(2024)/ft2", "UF building unit CAPEX"),
    "reference_building_area_ft2": ("Capital", "ft2", "Reference UF building area"),
    "equipment_capex_per_gpm": ("Capital", "$(2024)/gpm", "Zeolite system equipment cost per gpm of inlet flow"),
    "capex_coefficient": ("Capital", "$(2021)", "Coefficient a in equipment cost = a x Q^b (Q = inlet flow, m3/day)"),
    "capex_exponent": ("Capital", "exponent", "Exponent b in equipment cost = a x Q^b"),
    "capex_per_flow": ("Capital", "$(2024)/(m3/day)", "Equipment capital cost per unit daily capacity"),
    "column_capex_multiplier": ("Capital", "factor", "Lead/lag, parallel, and standby column CAPEX multiplier"),
    "capex_per_kw": ("Capital", "$(2024)/kW", "Equipment capital cost per kW capacity"),
    "fixed_opex_fraction": ("Fixed O&M", "fraction/yr", "Annual fixed OPEX as fraction of installed CAPEX"),
    "variable_opex_per_m3": ("Variable O&M", "$(2024)/m3", "Variable operating cost per cubic meter treated"),
    "capital_cost_multiplier": ("Capital", "factor", "Multiplier applied to the workbook ammonia-stripper capital-cost curve"),
    "opex_cost_multiplier": ("Variable O&M", "factor", "Multiplier applied to the workbook ammonia-stripper O&M-cost curve"),
    "chemical_price": ("Chemicals", "$(2024)/kg", "Chemical or regenerant price"),
    "lime_price": ("Chemicals", "$(2024)/lb", "Lime purchase price"),
    "soda_ash_price": ("Chemicals", "$(2024)/lb", "Soda ash purchase price"),
    "h2so4_price": ("Chemicals", "$(2024)/lb", "Sulfuric acid purchase price"),
    "aluminum_price": ("Chemicals", "$(2022)/kg", "Aluminum electrode purchase price"),
    "solid_disposal_cost": ("Disposal", "$(2024)/kg", "Solid waste disposal cost"),
    "sodium_bisulfite_price": ("Chemicals", "$(2024)/lb", "Sodium bisulfite purchase price"),
    "gac_replacement_cost": ("Spent GAC management", "$(2020)/kg", "Makeup GAC unit cost"),
    "gac_regeneration_cost": ("Spent GAC management", "$(2020)/kg", "Off-site regeneration unit cost, including regeneration energy"),
    "regeneration_fraction": ("Spent GAC management", "fraction", "Fraction of spent GAC regenerated; the rest is disposed and replaced with makeup GAC"),
    "zeolite_price": ("Media", "$(2014)/kg", "Zeolite media price"),
    "media_replacement_fraction_per_cycle": ("Media", "fraction/cycle", "Fraction of the AEC-based zeolite mass replaced per regeneration cycle"),
    "nacl_price": ("Chemicals", "$(2014)/metric tonne", "NaCl (regeneration salt) price"),
    "naoh_price": ("Chemicals", "$(2014)/metric tonne", "NaOH price"),
    "maintenance_fraction": ("Fixed O&M", "fraction/yr", "Maintenance-labor-chemical cost as a fraction of direct (TIC) CAPEX"),
    "media_replacement_price": ("Replacement", "$(2024)/unit", "Replacement media, membrane, cartridge, or bag price"),
    "media_replacement_fraction": ("Replacement", "fraction/yr", "Annual replacement fraction"),
    "total_installed_cost": ("Capital", "$(2024)", "Optional installed BWRO CAPEX; 0 uses unit/correlation CAPEX"),
    "unit_capex": ("Capital", "$(2024)/(m3/day product)", "Optional installed unit CAPEX; 0 uses the correlation"),
    "reference_unit_capex": ("Capital", "$(2024)/(m3/day product)", "Screening installed unit CAPEX at reference capacity"),
    "reference_capacity": ("Capital", "m3/day", "Reference capacity for CAPEX scaling"),
    "capex_scaling_exponent": ("Capital", "exponent", "CAPEX capacity-scaling exponent"),
    "cost_index_factor": ("Capital", "factor", "User-supplied common currency-year escalation factor"),
    "fixed_om_fraction": ("Fixed O&M", "fraction/yr", "Annual fixed O&M as fraction of installed CAPEX"),
    "insurance_fraction": ("Fixed O&M", "fraction/yr", "Annual insurance as fraction of installed CAPEX"),
    "membrane_cost": ("Replacement", "$(2024)/m2", "Membrane purchase cost per active area"),
    "membrane_replacement_fraction": ("Replacement", "fraction/yr", "Annual fraction of membrane area replaced"),
    "chemical_cost_per_m3_product": ("Variable O&M", "$(2024)/m3 product", "Chemical cost normalized to product volume"),
    "labor_cost_per_m3_product": ("Variable O&M", "$(2024)/m3 product", "Labor cost normalized to product volume"),
    "pretreatment_cost_per_m3_product": ("Variable O&M", "$(2024)/m3 product", "BWRO-island non-energy pretreatment cost"),
    "posttreatment_cost_per_m3_product": ("Variable O&M", "$(2024)/m3 product", "BWRO-island non-energy post-treatment cost"),
    "other_variable_cost_per_m3_product": ("Variable O&M", "$(2024)/m3 product", "Other product-normalized variable cost"),
    "intake_water_cost_per_m3_feed": ("Variable O&M", "$(2024)/m3 feed", "Source-water purchase or extraction cost"),
    "brine_disposal_cost_per_m3_concentrate": ("Variable O&M", "$(2024)/m3 brine", "Brine disposal cost; leave zero when modeled as a separate unit"),
    "membrane_replacement_factor": ("Replacement", "fraction/yr", "Annual membrane replacement as a fraction of direct membrane CAPEX"),
    "antiscalant_dose_mg_l": ("Chemicals", "mg/L", "Antiscalant dose normalized to LSRRO feed volume"),
    "antiscalant_unit_price": ("Chemicals", "$(2026)/gal", "Antiscalant product price"),
    "antiscalant_density_kg_l": ("Chemicals", "kg/L", "Antiscalant product density for kg-to-gal conversion"),
    "cip_cost_per_m3_product": ("Cleaning", "$(2021)/m3 product", "Clean-in-place cost normalized to permeate volume"),
    "labor_fte": ("Labor", "FTE", "Labor requirement assigned to the LSRRO unit"),
    "labor_cost_per_fte_year": ("Labor", "$(2024)/FTE-year", "Annual labor cost per full-time equivalent"),
    "om_contingency_factor": ("Variable O&M", "fraction", "O&M contingency applied to LSRRO operating costs"),
    "ach_price": ("Chemicals", "$(2021)/kg", "ACH (aluminum chlorohydrate) product price"),
    "media_cleaning_cost_per_m3": ("Variable O&M", "$(2020)/m3", "Media cleaning chemicals and makeup per m3 treated"),
    "polymer_price": ("Chemicals", "$(2021)/kg", "Polymer price"),
    "h2o2_price": ("Chemicals", "$(2021)/kg", "H2O2 price on a 100% basis"),
    "cation_capex_coefficient": ("Capital", "$(2021)", "Coefficient a in cation-bed equipment cost = a x Q^b (Q = flow through the bed, m3/day)"),
    "cation_capex_exponent": ("Capital", "exponent", "Exponent b in cation-bed equipment cost = a x Q^b"),
    "anion_capex_coefficient": ("Capital", "$(2021)", "Coefficient a in anion-bed equipment cost = a x Q^b (Q = flow through the bed, m3/day)"),
    "anion_capex_exponent": ("Capital", "exponent", "Exponent b in anion-bed equipment cost = a x Q^b"),
    "cation_resin_price": ("Resin", "$(2021)/m3", "Cation resin price"),
    "anion_resin_price": ("Resin", "$(2021)/m3", "Anion resin price"),
    "resin_life": ("Resin", "years", "Resin useful life before complete replacement"),
    "annual_resin_loss": ("Resin", "fraction/yr", "Resin lost to attrition and made up each year"),
    "salt_price": ("Chemicals", "$(2021)/metric tonne", "NaCl regenerant price"),
    "hcl_price": ("Chemicals", "$(2021)/metric tonne", "HCl price (100% basis)"),
    "caustic_price": ("Chemicals", "$(2021)/metric tonne", "NaOH price (100% basis)"),
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
    "Vacuum membrane distillation (VMD)": {
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
            "0 uses the NMSU recovery correlation (SI Eq. B5-1, fit to WaterTAP PBSE design points with hardness and silica correction); a positive value overrides it",
            "model input",
        ),
        "clip_negative_permeate": (
            "NMSU assumptions: water-quality regression post-processing option",
            "empirical",
        ),
    },
    "Ammonia stripping": {
        "recovery": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet",
            "workbook model",
        ),
        "energy_intensity": (
            "Planning-level blower energy placeholder; workbook cost curve already includes O&M",
            "engineering estimate",
        ),
        "feed_temperature": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet cell C5",
            "workbook model",
        ),
        "target_ammonia_mg_l": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet cell C30",
            "workbook model",
        ),
        "henry_cp_25c": (
            "Sander 2015 Henry's law compilation as cited in the NH3 Stripping Design Model worksheet",
            "publication",
        ),
        "henry_conversion_factor": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet cell E16",
            "workbook model",
        ),
        "stripping_design_factor": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet minimum air:water ratio equation",
            "workbook model",
        ),
        "kla_s": (
            "NH3 Stripping Design Model worksheet average of KLa values from https://www.ijche.com/article_58591.html and https://iopscience.iop.org/article/10.1088/1755-1315/344/1/012051/pdf",
            "publication",
        ),
        "tower_diameter_in": (
            "NMPWRC Produced Water Valorization v1.xlsm, NH3 Stripping Design Model worksheet cell C31",
            "workbook model",
        ),
    },
    "Chemical softening": {
        "lime_dose_mg_l": (
            "NMSU assumptions: average-TDS case of the NMSU CS model (SI Table S4); dose depends on the feed",
            "model input",
        ),
        "soda_ash_dose_mg_l": (
            "NMSU assumptions: average-TDS case of the NMSU CS model (SI Table S4); dose depends on the feed",
            "model input",
        ),
        "target_neutral_pH": (
            "NMPWRC Reaktoro chemical-softening simulator target neutralization pH",
            "model input",
        ),
        "acid_dose_override_mg_l": (
            "NMPWRC Reaktoro chemical-softening simulator optional user override",
            "model input",
        ),
        "energy_intensity": (
            "NMSU assumptions; KBH TEA workbook (O&M_Summary): 307,042 kWh/yr at 1 MGD for softening, UF, IX and degasifier pumping",
            "model input",
        ),
        "sludge_solids_content": (
            "Engineering estimate: lime softening clarifier sludge typically a few to about 15% solids; 10% used; sets sludge volume and water recovery",
            "engineering estimate",
        ),
    },
    "Electrocoagulation": {
        "current_density_mA_cm2": (
            "NMSU assumptions: 20 mA/cm2 (2.0 A/dm2), Al-Ajmi et al. 2025, Water 17, 23",
            "publication",
        ),
        "electrode_gap_m": (
            "NMSU assumptions; Lugo et al. 2025 (WaterTAP EC model input)",
            "publication",
        ),
        "hydraulic_retention_time": (
            "NMSU assumptions: 30 min EC treatment time, Al-Ajmi et al. 2025, Water 17, 23",
            "publication",
        ),
        "sludge_solids_content": (
            "Al-Ajmi et al. 2025, Water 17, 23: EC sludge 2.41-2.62% dry solids",
            "publication",
        ),
        "energy_intensity": (
            "NMPWRC EC-Al energy calculation from conductivity, current density, and electrode area",
            "engineering calculation",
        ),
    },
    "Walnut shell filtration": {
        "recovery": (
            "NMSU assumptions",
            "model input",
        ),
        "energy_intensity": (
            "NMSU assumptions; US DOE final report DE-FE0031851 (Drover 2022), WSF vendor electricity",
            "technical report",
        ),
    },
    "Ultrafiltration": {
        "recovery": (
            "KBH TEA Appendix: UF filtrate 0.9603 MGD from 0.97 MGD feed",
            "technical report",
        ),
        "sodium_bisulfite_dose_mg_l": (
            "KBH TEA Appendix (Chemical Details): sodium bisulfite 5 mg/L at UF",
            "model input",
        ),
        "pump_tdh_ft": (
            "KBH TEA Appendix (Power Load Details): Pump for MU/UF, TDH 50 ft",
            "model input",
        ),
        "pump_efficiency": (
            "KBH TEA Appendix (Power Load Details): Pump for MU/UF, pump efficiency 0.75",
            "model input",
        ),
        "motor_efficiency": (
            "KBH TEA Appendix (Power Load Details): Pump for MU/UF, motor efficiency 0.95",
            "model input",
        ),
        "vfd_factor": (
            "KBH TEA Appendix (Power Load Details): Pump for MU/UF, VFD factor 0.98",
            "model input",
        ),
    },
    "GAC": {
        "empty_bed_contact_time": (
            "WaterTAP GAC reference design (EBCT 600 s); EPA WBS typical 5-25 min for organics",
            "open source documentation",
        ),
        "max_bed_volume_per_vessel": (
            "US EPA 2021 WBS GAC model: vertical vessels up to 14 ft diameter x 14 ft, 50% bed expansion",
            "technical report",
        ),
        "redundant_vessels": (
            "WaterTAP 1.4 GAC costing default (1 operating + 1 redundant)",
            "open source documentation",
        ),
        "media_bulk_density": (
            "WaterTAP GAC reference design and NMSU assumptions (400 kg/m3)",
            "model source",
        ),
        "bv_coefficient_a": (
            "NMSU assumptions: empirical bed-life model (pilot BV vs feed TOC)",
            "pilot data",
        ),
        "bv_exponent_b": (
            "NMSU assumptions: empirical bed-life model (pilot BV vs feed TOC)",
            "pilot data",
        ),
        "pump_head": (
            "Engineering estimate of pressure-vessel bed, underdrain and piping head loss; EPA WBS GAC model computes pump energy from flow, head and efficiency",
            "engineering estimate",
        ),
        "pump_efficiency": (
            "Planning-level pump wire-to-water efficiency (EPA WBS pump energy method)",
            "engineering estimate",
        ),
    },
    "DAF": {
        "recycle_ratio": (
            "NMSU assumptions: 12% recycle (Abada et al. 2022 optimized DAF conditions)",
            "publication",
        ),
        "pump_head": (
            "Engineering estimate: saturator pressure about 5 bar",
            "engineering estimate",
        ),
        "pump_efficiency": (
            "Planning-level pump wire-to-water efficiency (EPA WBS pump energy method)",
            "engineering estimate",
        ),
        "auxiliary_energy_intensity": (
            "Engineering estimate: air compressor, flocculators and float skimmer; total DAF energy close to WaterTAP zero-order DAF (0.05 kWh/m3)",
            "engineering estimate",
        ),
        "h2o2_to_iron_ratio": (
            "NMSU assumptions: pilot study, 1.75 mg H2O2 per mg Fe",
            "pilot data",
        ),
        "ach_aluminum_content": (
            "Typical ACH product, 23-24% Al2O3 (12.4% Al)",
            "vendor data",
        ),
        "cod_to_toc_ratio": (
            "NMSU assumptions (used only to report COD)",
            "model input",
        ),
        "float_solids_content": (
            "Engineering estimate: mechanically skimmed DAF float typically 2-5% dry solids; sets float volume and water recovery",
            "engineering estimate",
        ),
    },
    "Zeolite": {
        "empty_bed_contact_time": (
            "NMSU assumptions: bench zeolite column test (KMI zeolite 14x30); Turan and Turan 2021",
            "pilot data",
        ),
        "regenerant_bed_volumes": (
            "NMSU assumptions: bench regeneration, 0.9 L brine per 10 mL bed",
            "pilot data",
        ),
        "brine_reuse_cycles": (
            "NMSU assumptions: brine reused for 5 successful bench regenerations",
            "pilot data",
        ),
        "nacl_mass_fraction": (
            "NMSU assumptions: 10% NaCl regenerant (bench test)",
            "pilot data",
        ),
        "naoh_to_nitrogen_molar_ratio": (
            "Engineering estimate: stoichiometric OH- to convert eluted NH4+ to NH3 at pH 11; set 0 for pH 7 regeneration",
            "engineering estimate",
        ),
        "aec_mg_n_g": (
            "Deng et al. 2014 ammonium exchange capacity range 2.5-21.5 mg N/g; NMSU assumptions use 4.0",
            "publication",
        ),
        "pump_head": (
            "Engineering estimate of pressure-vessel bed, underdrain and piping head loss (same basis as GAC)",
            "engineering estimate",
        ),
        "pump_efficiency": (
            "Planning-level pump wire-to-water efficiency (EPA WBS pump energy method)",
            "engineering estimate",
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
        "bed_removal": (
            "NMSU assumptions: 99% removal through the beds; lower targets are met by bypass",
            "model input",
        ),
        "cation_empty_bed_contact_time": ("US EPA WBS cation exchange model (2023 release): standard designs, EBCT 2.5 min (range 1.5-7.5)", "technical report"),
        "cation_capacity": ("US EPA WBS cation exchange model (2023 release): usable capacity 27 kgr as CaCO3/ft3 (1.24 eq/L) at 15 lb NaCl/ft3", "technical report"),
        "cation_regenerant_dose": ("US EPA WBS cation exchange model (2023 release): salt dose 15 lb NaCl/ft3 (240 g/L)", "technical report"),
        "cation_regenerant_concentration": ("US EPA WBS cation exchange model (2023 release): brine 0.9 lb/gal (108 g/L)", "technical report"),
        "cation_rinse_bed_volumes": ("US EPA WBS cation exchange model (2023 release): slow rinse 2 BV and fast rinse 10 BV", "technical report"),
        "cation_backwash_bed_volumes": ("US EPA WBS cation exchange model (2023 release): backwash 6 gpm/ft2 for 15 min, about 3 BV for a 4 ft bed", "technical report"),
        "cation_max_bed_volumes": ("US EPA WBS cation exchange model (2023 release): 100-1,000 BV before regeneration", "technical report"),
        "anion_empty_bed_contact_time": ("US EPA WBS anion exchange model (2023 release): standard designs, EBCT 2.0 min (range 1.5-7)", "technical report"),
        "anion_capacity": ("US EPA WBS anion exchange model (2023 release): bed life BV = -606 ln(SO4) + 3150 (Chen et al. 1999) implies 0.75-0.81 eq/L at 50-100 mg/L sulfate", "technical report"),
        "anion_regenerant_dose": ("US EPA WBS anion exchange model (2023 release): salt dose 8 lb NaCl/ft3 (128 g/L)", "technical report"),
        "anion_regenerant_concentration": ("US EPA WBS anion exchange model (2023 release): brine 0.5 lb/gal (60 g/L)", "technical report"),
        "anion_rinse_bed_volumes": ("US EPA WBS anion exchange model (2023 release): slow rinse 2 BV and fast rinse 5 BV", "technical report"),
        "anion_backwash_bed_volumes": ("US EPA WBS anion exchange model (2023 release): backwash 3 gpm/ft2 for 12 min, about 1.2 BV for a 4 ft bed", "technical report"),
        "anion_max_bed_volumes": ("US EPA WBS anion exchange model (2023 release): 300-3,000 BV before regeneration", "technical report"),
        "pump_head": ("Engineering estimate of pressure-vessel bed, underdrain and piping head loss (same basis as GAC and zeolite)", "engineering estimate"),
        "pump_efficiency": ("Planning-level pump wire-to-water efficiency (EPA WBS pump energy method)", "engineering estimate"),
    },
    "Ion exchange (demineralization)": {
        "bed_removal": (
            "NMSU assumptions: 99% removal through the beds; lower targets are met by bypass",
            "model input",
        ),
        "cation_empty_bed_contact_time": ("US EPA WBS cation exchange model (2023 release): EBCT 2.5 min", "technical report"),
        "cation_capacity": ("Lenntech demineralization plant data: indicative cation operating capacity 1 eq/L at 500 mg/L TDS", "industrial reference"),
        "cation_regenerant_dose": ("Woolley 2012 (SCI ion exchange course): 60-160 g acid/L resin, 3-6% HCl; 100 g/L used", "industrial reference"),
        "cation_regenerant_concentration": ("Woolley 2012: 3-6% HCl; 5% used", "industrial reference"),
        "cation_rinse_bed_volumes": ("US EPA WBS anion exchange model (2023 release): slow rinse 2 BV and fast rinse 5 BV", "technical report"),
        "cation_backwash_bed_volumes": ("US EPA WBS anion exchange model (2023 release): backwash about 1.2 BV", "technical report"),
        "cation_max_bed_volumes": ("US EPA WBS cation exchange model (2023 release): 100-1,000 BV before regeneration", "technical report"),
        "anion_empty_bed_contact_time": ("US EPA WBS anion exchange model (2023 release): EBCT 2.0 min", "technical report"),
        "anion_capacity": ("Lenntech demineralization plant data: indicative anion operating capacity 0.5 eq/L at 500 mg/L TDS", "industrial reference"),
        "anion_regenerant_dose": ("Woolley 2012: 60-160 g NaOH/L resin, 3-6% NaOH; 100 g/L used", "industrial reference"),
        "anion_regenerant_concentration": ("Woolley 2012: 3-6% NaOH; 4% used", "industrial reference"),
        "anion_rinse_bed_volumes": ("US EPA WBS anion exchange model (2023 release): slow rinse 2 BV and fast rinse 5 BV", "technical report"),
        "anion_backwash_bed_volumes": ("US EPA WBS anion exchange model (2023 release): backwash about 1.2 BV", "technical report"),
        "anion_max_bed_volumes": ("NMSU assumptions: same limit as the cation bed", "model input"),
        "pump_head": ("Engineering estimate of pressure-vessel bed, underdrain and piping head loss (same basis as GAC and zeolite)", "engineering estimate"),
        "pump_efficiency": ("Planning-level pump wire-to-water efficiency (EPA WBS pump energy method)", "engineering estimate"),
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
    "column_capex_multiplier": (
        "EPA WBS column-process design convention and expert review: lead/lag or parallel duty with standby columns",
        "engineering estimate",
    ),
    "reference_capacity": (
        "Screening CAPEX scaling input; replace with source-specific reference capacity when available",
        "engineering estimate",
    ),
    "capex_scaling_exponent": (
        "Screening CAPEX scaling input",
        "engineering estimate",
    ),
}


COST_INPUT_METADATA_BY_UNIT = {
    "Chemical softening": {
        "reference_direct_cs_capex": (
            "KBH TEA Appendix (2024-10-24), Capital_Summary at 1 MGD (ENR May 2024, location factor 0.815): lime softening 6.8 $/gpd x 1 MGD = 6.8 M, lime dewatering 11.53 M (scaled by solids load), chemical area 7.5 M (whole-plant lump sum)",
            "technical report",
        ),
        "reference_capacity": (
            "KBH TEA Appendix: 1.0 MGD reference flow",
            "technical report",
        ),
        "capex_scaling_exponent": (
            "NMSU assumptions",
            "model input",
        ),
        "installation_factor": (
            "KBH TEA Appendix, Capital_Summary: site 10% and E&IC 30% on the direct items (1.1 x 1.3 = 1.43)",
            "technical report",
        ),
        "lime_price": (
            "NMSU assumptions; KBH TEA Appendix (O&M_Summary) lime 0.05 $/lb",
            "technical report",
        ),
        "soda_ash_price": (
            "NMSU assumptions; KBH TEA Appendix (O&M_Summary) soda ash 0.45 $/lb",
            "technical report",
        ),
        "h2so4_price": (
            "NMSU assumptions (SI Table S1, 93% sulfuric acid 0.04 $/lb)",
            "model input",
        ),
        "maintenance_fraction": (
            "KBH TEA Appendix (O&M_Summary): other maintenance (replacements) 2% of system direct cost; labor included",
            "technical report",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "Ultrafiltration": {
        "reference_uf_flow_gpd": (
            "KBH TEA Appendix (Capital_Summary): UF feed 0.97 MGD; 2024 dollars",
            "technical report",
        ),
        "uf_equipment_unit_cost": (
            "KBH TEA Appendix (Capital_Summary): UF 2 $/gpd; 2024 dollars",
            "technical report",
        ),
        "uf_building_unit_cost": (
            "KBH TEA Appendix (Capital_Summary): UF building 300 $/ft2; 2024 dollars",
            "technical report",
        ),
        "reference_building_area_ft2": (
            "KBH TEA Appendix (Capital_Summary): UF building 2,000 ft2",
            "technical report",
        ),
        "capex_scaling_exponent": (
            "NMSU assumptions",
            "model input",
        ),
        "installation_factor": (
            "KBH TEA Appendix (Capital_Summary): site 10% and E&IC 30% on the direct items (1.1 x 1.3 = 1.43)",
            "technical report",
        ),
        "sodium_bisulfite_price": (
            "NMSU assumptions; KBH TEA Appendix (O&M_Summary) sodium bisulfite 0.25 $/lb",
            "technical report",
        ),
        "maintenance_fraction": (
            "KBH TEA Appendix (O&M_Summary): other maintenance (replacements) 2% of system direct cost; labor and membrane replacement included",
            "technical report",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "Electrocoagulation": {
        "reference_ec_capex": (
            "NMSU EC model: Lugo et al. 2025 (J. Environ. Chem. Eng. 13, 117026) EC-Al cost at 11,356 m3/day, 2024 dollars",
            "publication",
        ),
        "reference_capacity": (
            "Lugo et al. 2025 design flow (3 MGD)",
            "publication",
        ),
        "capex_scaling_exponent": (
            "NMSU assumptions",
            "model input",
        ),
        "installation_factor": (
            "Reference cost is a plant-level cost; indirect costs are covered by the system-level investment factor",
            "engineering estimate",
        ),
        "aluminum_price": (
            "Anuf et al. 2022, J. Water Process Eng., doi:10.1016/j.jwpe.2022.103074 (aluminum electrode metal)",
            "publication",
        ),
        "maintenance_fraction": (
            "NMSU assumptions: maintenance including labor, same basis as GAC, DAF and WSF",
            "model input",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "Walnut shell filtration": {
        "reference_capex_cost_per_bbl": (
            "US DOE final report DE-FE0031851 (Drover 2022) vendor data: WSF only (no DGF), 64,752 $/yr amortization at 7,200,000 bbl/yr; converted with the report's CRF (5%, 10 yr)",
            "technical report",
        ),
        "capex_scaling_exponent": (
            "NMSU assumptions",
            "model input",
        ),
        "installation_factor": (
            "Reference cost includes installation; indirect costs are covered by the system-level investment factor",
            "engineering estimate",
        ),
        "media_cleaning_cost_per_m3": (
            "US DOE final report DE-FE0031851 (Drover 2022): WSF chemicals 62,500 $/yr at 20,000 bbl/day (weekly cleaning)",
            "technical report",
        ),
        "maintenance_fraction": (
            "NMSU assumptions: maintenance including labor, same basis as GAC and DAF",
            "model input",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "DAF": {
        "capex_scaling_exponent": (
            "NMSU assumptions: exponent from two DAF systems (Lugo et al. 2025; Liu et al. 2023); reference cost 313,992 USD_2018 at 3 MGD",
            "publication",
        ),
        "installation_factor": (
            "Reference cost is an installed (construction) cost; indirect costs are covered by the system-level investment factor",
            "engineering estimate",
        ),
        "maintenance_fraction": (
            "NMSU assumptions: maintenance including labor, same basis as GAC",
            "model input",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
        "ach_price": (
            "US EPA WBS cost database: polyaluminum chloride, large quantity (2021 $)",
            "technical report",
        ),
        "polymer_price": (
            "US EPA WBS cost database: polymers (2021 $)",
            "technical report",
        ),
        "h2o2_price": (
            "US EPA WBS cost database: hydrogen peroxide 50%, large quantity, converted to 100% basis (2021 $)",
            "technical report",
        ),
    },
    "Zeolite": {
        "capex_coefficient": (
            "US EPA WBS Cation Exchange model (2023 release, 2021 $) run at 0.124-22.6 MGD with EBCT 20 min; media charge excluded; fit within 16%",
            "technical report",
        ),
        "capex_exponent": (
            "US EPA WBS Cation Exchange model (2023 release, 2021 $) run at 0.124-22.6 MGD with EBCT 20 min; media charge excluded",
            "technical report",
        ),
        "installation_factor": (
            "EPA WBS unit costs already include transportation and installation; TIC covers remaining direct items (same basis as GAC)",
            "engineering estimate",
        ),
        "maintenance_fraction": (
            "NMSU assumptions: 2% of CAPEX per year",
            "model input",
        ),
        "zeolite_price": (
            "NMSU assumptions: bench test vendor price (10 $ per 5 lb); Deng et al. 2014",
            "model input",
        ),
        "media_replacement_fraction_per_cycle": (
            "NMSU assumptions: media regenerated in place, no replacement",
            "model input",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "GAC": {
        "gac_replacement_cost": (
            "WaterTAP 1.4 GAC model and costing method (watertap.costing.unit_models.gac)",
            "open source documentation",
        ),
        "gac_regeneration_cost": (
            "WaterTAP 1.4 GAC model and costing method (watertap.costing.unit_models.gac)",
            "open source documentation",
        ),
        "maintenance_fraction": (
            "WaterTAP 1.4 GAC model and costing method (watertap.costing.unit_models.gac)",
            "open source documentation",
        ),
        "installation_factor": (
            "EPA WBS unit costs already include transportation and installation; TIC covers remaining direct items",
            "engineering estimate",
        ),
        "regeneration_fraction": (
            "NMSU assumptions: spent-media split (WaterTAP default 0.70)",
            "model input",
        ),
        "om_contingency_factor": (
            "Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "Vacuum membrane distillation (VMD)": {
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
        "reference_flow_m3_day": (
            "NMSU assumptions: 50,000 bbl/day reference flow for capital scaling",
            "model input",
        ),
        "capex_scaling_exponent": (
            "NMSU assumptions (SI Eq. B5-2)",
            "empirical",
        ),
        "installation_factor": (
            "WaterTAP LSRRO flowsheet costing (TIC = 2); equipment costs from the WaterTAP design table",
            "open source documentation",
        ),
        "maintenance_fraction": (
            "NMSU assumptions: 2% of direct cost per year, including labor (as for UF and chemical softening)",
            "model input",
        ),
        "antiscalant_dose_mg_l": (
            "NMSU assumptions: LSRRO antiscalant dose",
            "model input",
        ),
        "antiscalant_unit_price": (
            "NMSU assumptions; Applied Membranes AMI antiscalant product information 2026",
            "vendor data",
        ),
        "antiscalant_density_kg_l": (
            "NMSU assumptions: antiscalant product density",
            "engineering estimate",
        ),
        "cip_cost_per_m3_product": (
            "NMSU assumptions; Jafari et al. 2021 reverse-osmosis and nanofiltration fouling cost",
            "publication",
        ),
        "om_contingency_factor": (
            "NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption",
            "technical report",
        ),
    },
    "Ammonia stripping": {
        "capital_cost_multiplier": (
            "NMPWRC Produced Water Valorization v1.xlsm, Air Strip Cost Model worksheet full unit-process CIP CAPEX curve",
            "workbook model",
        ),
        "opex_cost_multiplier": (
            "NMPWRC Produced Water Valorization v1.xlsm, Air Strip Cost Model worksheet full unit-process CIP O&M curve",
            "workbook model",
        ),
        "variable_opex_per_m3": (
            "Optional project-specific add-on; leave zero to use only the workbook O&M curve",
            "user input",
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
        "cation_capex_coefficient": ("US EPA WBS cation exchange model (2023 release) standard designs 2-7 (0.124-22.6 MGD, SAC, EBCT 2.5 min, autosized) rerun at NMSU; resin excluded; fit within 30%", "technical report"),
        "cation_capex_exponent": ("US EPA WBS cation exchange model (2023 release) standard designs 2-7 (0.124-22.6 MGD, SAC, EBCT 2.5 min, autosized) rerun at NMSU; resin excluded; fit within 30%", "technical report"),
        "anion_capex_coefficient": ("US EPA WBS anion exchange model (2023 release) nitrate standard designs 2-7 (0.124-22.6 MGD) with SBA Type I gel resin, EBCT 2.0 min, autosized, rerun at NMSU; resin excluded; fit within 34%", "technical report"),
        "anion_capex_exponent": ("US EPA WBS anion exchange model (2023 release) nitrate standard designs 2-7 (0.124-22.6 MGD) with SBA Type I gel resin, EBCT 2.0 min, autosized, rerun at NMSU; resin excluded; fit within 34%", "technical report"),
        "installation_factor": ("EPA WBS unit costs already include transportation and installation; TIC covers remaining direct items (same basis as GAC and zeolite)", "engineering estimate"),
        "cation_resin_price": ("US EPA WBS cost data: strong acid polystyrenic macroporous resin 231.49 $/ft3 (2021 $)", "technical report"),
        "anion_resin_price": ("US EPA WBS cost data: strong base polystyrenic gel Type I resin 232.14 $/ft3 (2021 $)", "technical report"),
        "resin_life": ("US EPA WBS cation and anion exchange models: resin life 7 years", "technical report"),
        "annual_resin_loss": ("US EPA WBS cation and anion exchange models: 4.5% annual resin loss", "technical report"),
        "maintenance_fraction": ("NMSU assumptions: 2% of direct CAPEX per year, including labor (same basis as zeolite)", "model input"),
        "om_contingency_factor": ("NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption", "technical report"),
        "salt_price": ("US EPA WBS cost data: sodium chloride, large quantity, 0.104 $/lb (2021 $)", "technical report"),
    },
    "Ion exchange (demineralization)": {
        "cation_capex_coefficient": ("US EPA WBS cation exchange model (2023 release) standard designs 2-7 (0.124-22.6 MGD, SAC, EBCT 2.5 min, autosized) rerun at NMSU; resin excluded; fit within 30%", "technical report"),
        "cation_capex_exponent": ("US EPA WBS cation exchange model (2023 release) standard designs 2-7 (0.124-22.6 MGD, SAC, EBCT 2.5 min, autosized) rerun at NMSU; resin excluded; fit within 30%", "technical report"),
        "anion_capex_coefficient": ("US EPA WBS anion exchange model (2023 release) nitrate standard designs 2-7 (0.124-22.6 MGD) with SBA Type I gel resin, EBCT 2.0 min, autosized, rerun at NMSU; resin excluded; fit within 34%", "technical report"),
        "anion_capex_exponent": ("US EPA WBS anion exchange model (2023 release) nitrate standard designs 2-7 (0.124-22.6 MGD) with SBA Type I gel resin, EBCT 2.0 min, autosized, rerun at NMSU; resin excluded; fit within 34%", "technical report"),
        "installation_factor": ("EPA WBS unit costs already include transportation and installation; TIC covers remaining direct items (same basis as GAC and zeolite)", "engineering estimate"),
        "cation_resin_price": ("US EPA WBS cost data: strong acid polystyrenic macroporous resin 231.49 $/ft3 (2021 $)", "technical report"),
        "anion_resin_price": ("US EPA WBS cost data: strong base polystyrenic gel Type I resin 232.14 $/ft3 (2021 $)", "technical report"),
        "resin_life": ("US EPA WBS cation and anion exchange models: resin life 7 years", "technical report"),
        "annual_resin_loss": ("US EPA WBS cation and anion exchange models: 4.5% annual resin loss", "technical report"),
        "maintenance_fraction": ("NMSU assumptions: 2% of direct CAPEX per year, including labor (same basis as zeolite)", "model input"),
        "om_contingency_factor": ("NMSU assumptions; Wang et al. 2024 DWPR report TEA O&M contingency assumption", "technical report"),
        "hcl_price": ("US EPA WBS cost data: hydrochloric acid, large quantity, 0.493 $/lb (2021 $)", "technical report"),
        "caustic_price": ("US EPA WBS cost data: sodium hydroxide 50%, large quantity, 0.213 $/lb solution, converted to 100% basis (2021 $)", "technical report"),
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
    "reference_flow_bbl_day",
    "gross_pump_power_kw",
    "energy_recovery_fraction",
    "membrane_flux",
    "pressure_override_psi",
    "stage_override",
    "clip_negative_permeate",
    "lime_dose_mg_l",
    "soda_ash_dose_mg_l",
    "target_neutral_pH",
    "acid_dose_override_mg_l",
    "current_density_mA_cm2",
    "electrode_gap_m",
    "feed_tds_g_l",
    "feed_temperature",
    "target_ammonia_mg_l",
    "henry_cp_25c",
    "henry_conversion_factor",
    "stripping_design_factor",
    "kla_s",
    "tower_diameter_in",
    "array_stages",
    "elements_per_vessel",
    "design_flux_lmh",
    "concentration_polarization",
    "fouling_factor",
    "high_pressure_pump_efficiency",
    "feed_pump_efficiency",
    "feed_pump_pressure_bar",
    "piping_loss_bar",
    "has_erd",
    "erd_efficiency",
    "pretreatment_energy_intensity",
    "energy_intensity",
    "auxiliary_energy_intensity",
    "thermal_energy_intensity",
    "recycle_ratio",
    "h2o2_to_iron_ratio",
    "ach_aluminum_content",
    "cod_to_toc_ratio",
    "float_solids_content",
    "sludge_solids_content",
    "chemical_dose",
    "hydraulic_retention_time",
    "design_factor",
    "filtration_rate",
    "bed_depth",
    "media_bulk_density",
    "element_capacity",
    "backwash_fraction",
    "sodium_bisulfite_dose_mg_l",
    "pump_tdh_ft",
    "pump_head",
    "pressure_drop_psi",
    "pump_efficiency",
    "motor_efficiency",
    "vfd_factor",
    "target_pH",
    "air_water_ratio",
    "tower_loading_rate",
    "operating_pressure",
    "empty_bed_contact_time",
    "max_bed_volume_per_vessel",
    "redundant_vessels",
    "regenerant_bed_volumes",
    "brine_reuse_cycles",
    "nacl_mass_fraction",
    "aec_mg_n_g",
    "naoh_to_nitrogen_molar_ratio",
    "bv_coefficient_a",
    "bv_exponent_b",
    "ammonia_removal",
    "regenerant_dose",
    "bed_removal",
    "cation_empty_bed_contact_time",
    "cation_capacity",
    "cation_regenerant_dose",
    "cation_regenerant_concentration",
    "cation_rinse_bed_volumes",
    "cation_backwash_bed_volumes",
    "cation_max_bed_volumes",
    "anion_empty_bed_contact_time",
    "anion_capacity",
    "anion_regenerant_dose",
    "anion_regenerant_concentration",
    "anion_rinse_bed_volumes",
    "anion_backwash_bed_volumes",
    "anion_max_bed_volumes",
    "power_capacity",
    "capacity_factor",
    "blend_fraction",
]

COST_INPUT_ORDER = [
    "total_installed_cost",
    "unit_capex",
    "reference_unit_capex",
    "reference_direct_membrane_capex",
    "reference_direct_cs_capex",
    "reference_ec_capex",
    "installation_factor",
    "reference_flow_bbl_day",
    "reference_flow_m3_day",
    "reference_capex_cost_per_bbl",
    "reference_opex_cost_per_bbl",
    "reference_uf_flow_gpd",
    "uf_equipment_unit_cost",
    "uf_building_unit_cost",
    "reference_building_area_ft2",
    "equipment_capex_per_gpm",
    "capex_coefficient",
    "capex_exponent",
    "cation_capex_coefficient",
    "cation_capex_exponent",
    "anion_capex_coefficient",
    "anion_capex_exponent",
    "capex_per_flow",
    "reference_capacity",
    "capex_scaling_exponent",
    "cost_index_factor",
    "column_capex_multiplier",
    "capex_per_kw",
    "fixed_om_fraction",
    "insurance_fraction",
    "membrane_cost",
    "membrane_replacement_fraction",
    "chemical_cost_per_m3_product",
    "labor_cost_per_m3_product",
    "pretreatment_cost_per_m3_product",
    "posttreatment_cost_per_m3_product",
    "other_variable_cost_per_m3_product",
    "intake_water_cost_per_m3_feed",
    "brine_disposal_cost_per_m3_concentrate",
    "membrane_replacement_factor",
    "antiscalant_dose_mg_l",
    "antiscalant_unit_price",
    "antiscalant_density_kg_l",
    "cip_cost_per_m3_product",
    "labor_fte",
    "labor_cost_per_fte_year",
    "om_contingency_factor",
    "fixed_opex_fraction",
    "variable_opex_per_m3",
    "capital_cost_multiplier",
    "opex_cost_multiplier",
    "chemical_price",
    "lime_price",
    "soda_ash_price",
    "h2so4_price",
    "aluminum_price",
    "solid_disposal_cost",
    "sodium_bisulfite_price",
    "gac_regeneration_cost",
    "gac_replacement_cost",
    "regeneration_fraction",
    "maintenance_fraction",
    "zeolite_price",
    "media_replacement_fraction_per_cycle",
    "nacl_price",
    "naoh_price",
    "salt_price",
    "hcl_price",
    "caustic_price",
    "cation_resin_price",
    "anion_resin_price",
    "resin_life",
    "annual_resin_loss",
    "media_cleaning_cost_per_m3",
    "ach_price",
    "polymer_price",
    "h2o2_price",
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
    unit_metadata = metadata_by_unit.get(unit_process, {})
    if parameter in unit_metadata:
        return unit_metadata[parameter]
    if parameter in metadata_by_parameter:
        return metadata_by_parameter[parameter]
    if unit_process == "BWRO":
        return (
            "SEDAT DesalinationModels/BWRO.py and BWRO_cost.py; BW30 PRO-400/34 membrane defaults",
            "model source",
        )
    return ("", "")


def technical_input_rows(unit_process):
    defaults = TECHNICAL_MODEL_DEFAULTS.get(unit_process)
    if not defaults:
        return []
    row_defaults = defaults.copy()
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
            row_defaults[parameter],
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
    row_defaults = defaults.copy()
    if "capex_per_flow" in row_defaults:
        row_defaults.setdefault("reference_capacity", 1000.0)
        row_defaults.setdefault("capex_scaling_exponent", 1.0)
    rows = []
    for parameter in COST_INPUT_ORDER:
        if parameter not in row_defaults:
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
            row_defaults[parameter],
            unit,
            description,
            source,
            data_type,
        ))
    return rows
