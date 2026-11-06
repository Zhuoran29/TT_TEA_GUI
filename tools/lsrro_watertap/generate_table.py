"""Generate the LSRRO lookup table used by the TEA app from the WaterTAP LSRRO flowsheet.

For every (feed TDS, recovery) grid point, the flowsheet is solved for increasing stage counts. The
search stops once the LCOW rises with an added stage; the feasible design with the lowest LCOW is
kept. Points whose brine would exceed NaCl solubility are skipped. Failed solves are recorded in the raw
file and left out of the table. The table keeps every feasible stage count tried at each point, so the
app can interpolate between designs with the same stage count.

Usage:
  python generate_table.py                          # full grid, resumes from earlier raw results
  python generate_table.py --tds 20 30 40 --raw a   # part of the grid (run parts in parallel)
  python generate_table.py --build-table            # rebuild lsrro_table.csv from all raw files

Outputs (this folder):
  raw_*.jsonl         every solve attempt (one JSON line each)
  lsrro_table.csv     every feasible design per grid point and stage count (per-flow quantities,
                      WaterTAP 2018 dollars); lowest_lcow = 1 marks the lowest-LCOW design
"""
import argparse, csv, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE = HERE / "lsrro_table.csv"
TDS_GRID = list(range(20, 151, 10))                       # g/L NaCl
REC_GRID = [round(0.20 + 0.05 * i, 2) for i in range(11)] # 0.20-0.70
MAX_STAGES = 8
BRINE_LIMIT_G_L = 320.0                                   # NaCl solubility (~26.4 wt%)
TIMEOUT_S = 900


def load_raw():
    done = {}
    for path in sorted(HERE.glob("raw_*.jsonl")):
        for line in path.read_text().splitlines():
            d = json.loads(line)
            done[(round(d["cin_g_l"], 3), round(d["recovery"], 3), d["stages"])] = d
    return done


def solve(stages, rec, tds, done, raw):
    key = (round(float(tds), 3), round(rec, 3), stages)
    if key in done:
        return done[key]
    try:
        out = subprocess.run([sys.executable, str(HERE / "solve_point.py"), str(stages), str(rec), str(tds)],
                             capture_output=True, text=True, timeout=TIMEOUT_S).stdout.strip().splitlines()
        d = json.loads(out[-1]) if out else {"ok": False, "error": "no output"}
    except subprocess.TimeoutExpired:
        d = {"ok": False, "error": f"timeout {TIMEOUT_S} s"}
    d.update(stages=stages, recovery=rec, cin_g_l=float(tds))
    with raw.open("a") as f:
        f.write(json.dumps(d) + "\n")
    done[key] = d
    return d


def best_design(tds, rec, done, raw):
    best = None
    for s in range(1, MAX_STAGES + 1):
        d = solve(s, rec, tds, done, raw)
        if not d["ok"]:
            if best is not None:
                break
            continue
        if best is not None and d["LCOW"] >= best["LCOW"]:
            break
        best = d
    return best


def per_flow(d):
    """Per m3/day of feed (capital, $), per m3/day feed per year (opex), per m3 product (SEC).

    WaterTAP unit capital costs include its TIC (2); they are divided by TIC here so the table holds
    equipment costs and the app applies its own installation and investment factors.
    """
    feed_m3_d = d["feed_m3_s"] * 86400.0
    tic = d.get("TIC", 2.0)
    prod_m3_d = d["prod_m3_s"] * 86400.0
    return {
        "feed_tds_g_l": d["cin_g_l"], "recovery": d["recovery"], "stages": d["stages"],
        "sec_kwh_m3_product": d["SEC"], "sec_kwh_m3_feed": d["SEC"] * prod_m3_d / feed_m3_d,
        "membrane_area_m2_per_m3d_product": d["area_m2"] / prod_m3_d,
        "first_stage_area_m2_per_m3d_product": d["area_hp_m2"] / prod_m3_d,
        "membrane_capex_usd_per_m3d_feed": d["mem_capex"] / tic / feed_m3_d,
        "pump_capex_usd_per_m3d_feed": d["pump_capex"] / tic / feed_m3_d,
        "erd_capex_usd_per_m3d_feed": d["erd_capex"] / tic / feed_m3_d,
        "equipment_capex_usd_per_m3d_feed": d["direct_capex"] / tic / feed_m3_d,
        "membrane_replacement_usd_yr_per_m3d_feed": d["mem_opex"] / feed_m3_d,
        "watertap_lcow_usd_m3_product": d["LCOW"], "product_nacl_ppm": d["product_ppm"],
        "brine_g_l": d["brine_g_l"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tds", type=float, nargs="*")
    ap.add_argument("--rec", type=float, nargs="*")
    ap.add_argument("--raw", default="results", help="raw file suffix: raw_<suffix>.jsonl")
    ap.add_argument("--build-table", action="store_true")
    a = ap.parse_args()
    tds_grid = a.tds or TDS_GRID
    rec_grid = a.rec or REC_GRID
    raw = HERE / f"raw_{a.raw}.jsonl"
    done = load_raw()
    if not a.build_table:
        for tds in tds_grid:
            for rec in rec_grid:
                if tds / (1.0 - rec) > BRINE_LIMIT_G_L:
                    continue
                b = best_design(tds, rec, done, raw)
                print(f"{tds:5.0f} g/L  r={rec:.2f}  " + (f"stages {b['stages']}  SEC {b['SEC']:.2f}  LCOW {b['LCOW']:.2f}" if b else "no feasible design"), flush=True)
        return
    rows = []
    for tds in TDS_GRID:
        for rec in REC_GRID:
            tried = [d for (t, r, _s), d in done.items() if t == round(float(tds), 3) and r == round(rec, 3)]
            ok = sorted((d for d in tried if d["ok"]), key=lambda d: d["stages"])
            if not ok:
                continue
            best = min(ok, key=lambda d: d["LCOW"])["stages"]
            for d in ok:
                rows.append(dict(per_flow(d), lowest_lcow=int(d["stages"] == best)))
    if rows:
        with TABLE.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
