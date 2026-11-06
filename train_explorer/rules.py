"""Explorer metadata and operational warning rules.

Edit this file to change how units are drawn, which waste-disposal path their
reject stream is shown in, and which operational warnings are checked.

Every rule cites where its threshold comes from.  Rules evaluate the water
quality entering the unit, estimated with the default removal efficiencies.
"""

# Units offered in the library even though they have no dedicated technical model.
EXTRA_LIBRARY_UNITS = {
    "pretreatment": ["Antiscalant / pH adjustment"],
}

# Literature removal efficiencies that differ from UNIT_REMOVAL_RATES. They are only offered
# as suggestions when a Fit-for-Purpose target may be exceeded; the app defaults stay unchanged.
LITERATURE_REMOVALS = [
    {"unit": "GAC", "param": "Naphthalene", "value": 0.98,
     "note": "The removal-table value is the TOC removal from one NMSU simulation applied to all organics.",
     "source": "https://par.nsf.gov/servlets/purl/10601094"},
]

# Units that may be placed in more than one stage.
CROSS_STAGE_UNITS = {
    "GAC": ["pretreatment", "posttreatment"],
    "Ammonia stripping": ["pretreatment", "posttreatment"],
}

# How each unit is drawn and where its removed mass goes.
#   mech: float | settle | media | membrane | thermal | strip | dose
#   path: brine  -> Brine management
#         solid  -> Sludge / solid waste and other residuals (off-gas, spent media)
#   residual: name of the reject stream, taken from the unit's technical model outputs.
UNIT_DISPLAY = {
    "3-phase separator": {"mech": "float", "path": "solid", "residual": "Separated oil / solids"},
    "DAF": {"mech": "float", "path": "solid", "residual": "DAF float",
            "note": "TOC removal is calculated by the DAF model from the H2O2 dose, which is set by DAF feed iron."},
    "Chemical softening": {"mech": "settle", "path": "solid", "residual": "Softening sludge",
                           "note": "The TEA run uses the Reaktoro softening model; these are the removal-table values it falls back to."},
    "Electrocoagulation": {"mech": "settle", "path": "solid", "residual": "EC sludge"},
    "Walnut shell filtration": {"mech": "media", "path": "solid", "residual": "Backwash"},
    "Ultrafiltration": {"mech": "membrane", "path": "solid", "residual": "Backwash"},
    "Ammonia stripping": {"mech": "strip", "path": "solid", "residual": "Off-gas (NH3)"},
    "MVC": {"mech": "thermal", "path": "brine", "residual": "Brine"},
    "Vacuum membrane distillation (VMD)": {"mech": "thermal", "path": "brine", "residual": "Brine"},
    "LSRRO": {"mech": "membrane", "path": "brine", "residual": "Concentrate",
              "note": "Removal follows tea_models/lsrro_core.py (regression or average removal), so it changes with LSRRO feed concentration."},
    "BWRO": {"mech": "membrane", "path": "brine", "residual": "Concentrate"},
    "GAC": {"mech": "media", "path": "solid", "residual": "Spent GAC"},
    "Zeolite": {"mech": "media", "path": "brine", "residual": "Spent regenerant brine"},
    "Ion exchange": {"mech": "media", "path": "brine", "residual": "Regenerant brine",
                     "note": "Removed cations are replaced by Na+ and removed anions by Cl-, so TDS does not drop; the TEA run adds the released Na and Cl."},
    "Ion exchange (demineralization)": {"mech": "media", "path": "brine", "residual": "Spent acid and caustic",
                                        "note": "All ions are removed at the TDS removal."},
    "Ion exchange / EDI": {"mech": "media", "path": "brine", "residual": "Regenerant brine"},
    "Antiscalant / pH adjustment": {"mech": "dose", "path": "brine"},
    "Saltwater disposal well": {"mech": "dose", "path": "brine"},
    "Evaporation pond": {"mech": "dose", "path": "brine"},
    # Units without their own technical model file (generic template); shown when already in the train.
    "Cartridge filter": {"mech": "media", "path": "solid", "residual": "Spent cartridges"},
    "Bag filter": {"mech": "media", "path": "solid", "residual": "Spent bags"},
    "Media filtration": {"mech": "media", "path": "solid", "residual": "Backwash"},
    "Ultra-fine filtration": {"mech": "membrane", "path": "solid", "residual": "Backwash"},
    "NF": {"mech": "membrane", "path": "brine", "residual": "Concentrate"},
}

_LSRRO = "tea_models/lsrro_core.py (calculate_recovery_fraction)"
_RO_VENDOR = "Aquaporin Industrial RO User Manual, Operation Guide (July 2023): feed water guidelines"

# test: "outside" (range), "gt" (value), "missing" (absent or <= 0 at the unit inlet)
OPERATIONAL_RULES = [
    # --- Model inputs the technical models need -------------------------------------------
    {"units": ["GAC"], "param": "TOC", "test": "missing", "kind": "Model input",
     "message": "Feed TOC is unavailable; GAC bed life and media OPEX are zero.", "source": "tea_models/technical_models/gac.py"},
    {"units": ["Zeolite"], "param": "Ammonia nitrogen", "test": "missing", "kind": "Model input",
     "message": "Feed ammonia is unavailable; zeolite bed life is not calculated.", "source": "tea_models/technical_models/zeolite.py"},
    {"units": ["Ammonia stripping"], "param": "Ammonia nitrogen", "test": "missing", "kind": "Model input",
     "message": "Feed ammonia is unavailable or zero; ammonia stripping removal is zero.",
     "source": "tea_models/technical_models/ammonia_stripping.py"},
    {"units": ["DAF"], "param": "Iron", "test": "missing", "kind": "Model input",
     "message": "Feed iron is zero or missing: no H2O2 is dosed and the calculated TOC and H2S removals are zero.",
     "source": "tea_models/technical_models/daf.py"},
    # --- RO membrane feed guidelines (vendor manual) --------------------------------------
    {"units": ["BWRO", "LSRRO"], "param": "Oil", "test": "gt", "value": 0.1, "kind": "Membrane feed",
     "message": "Oil and grease entering the RO is about {value} mg/L; the vendor guideline maximum is 0.1 mg/L (membrane fouling).",
     "source": _RO_VENDOR},
    {"units": ["BWRO", "LSRRO"], "param": "Iron", "test": "gt", "value": 0.5, "kind": "Membrane feed",
     "message": "Iron entering the RO is about {value} mg/L; the vendor guideline maximum for ferric iron is 0.5 mg/L.",
     "source": _RO_VENDOR},
    {"units": ["BWRO", "LSRRO"], "param": "Manganese", "test": "gt", "value": 0.5, "kind": "Membrane feed",
     "message": "Manganese entering the RO is about {value} mg/L; the vendor guideline maximum is 0.5 mg/L.",
     "source": _RO_VENDOR},
    {"units": ["BWRO", "LSRRO"], "param": "Turbidity", "test": "gt", "value": 1.0, "kind": "Membrane feed",
     "message": "Turbidity entering the RO is about {value} NTU; the vendor guideline maximum is 1 NTU.",
     "source": _RO_VENDOR},
    {"units": ["BWRO", "LSRRO"], "param": "TOC", "test": "gt", "value": 3.0, "kind": "Membrane feed",
     "message": "TOC entering the RO is about {value} mg/L; the vendor guideline maximum is 3 mg/L (organic fouling).",
     "source": _RO_VENDOR},
]
