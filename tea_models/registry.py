from importlib import import_module


def model_key(unit_process):
    """Convert a unit-process name into a Python module-friendly key."""
    cleaned = []
    for char in unit_process.lower():
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append("_")
    return "_".join(part for part in "".join(cleaned).split("_") if part)


def _load_model(package, unit_process):
    module_name = model_key(unit_process)
    try:
        return import_module(f"{package}.{module_name}")
    except ModuleNotFoundError:
        return import_module(f"{package}.default")


def run_technical_model(unit_process, technical_inputs, stream):
    model = _load_model("tea_models.technical_models", unit_process)
    return model.run(unit_process, technical_inputs, stream)


def run_cost_model(unit_process, technical_result, cost_inputs, context):
    model = _load_model("tea_models.cost_models", unit_process)
    return model.run(unit_process, technical_result, cost_inputs, context)
