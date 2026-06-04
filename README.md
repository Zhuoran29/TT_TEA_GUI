# GUI for Water Treatment Train Techno-Economic Analysis

## Recommended Setup

Reaktoro is required for scaling tendency calculations and should be installed with conda.

Create the environment from `environment.yml`:

```bash
conda env create -f environment.yml
conda activate tea-gui
python -m streamlit run TEA_GUI.py
```

Or create the environment manually:

```bash
conda create -n TEA python=3.10.14
conda activate TEA
conda install -c conda-forge reaktoro=2.11.0=py310h2b8a7e3_0 streamlit pandas numpy openpyxl matplotlib
python -m streamlit run TEA_GUI.py
```

If you update `environment.yml`, refresh the environment with:

```bash
conda env update -f environment.yml --prune
```
