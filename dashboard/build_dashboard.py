"""Bangun dashboard/index.html dari template + data asli hasil analisis.

Sumber:
  - dashboard/data.json                         (provinsi, garis kemiskinan & inflasi kab/kota, sensitivitas)
  - dashboard/indonesia-kabkota.geojson         (batas kab/kota)
  - outputs/pangantahan_validasi_model.csv      (MAE holdout per model)

Jalankan:  python dashboard/build_dashboard.py
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def norm_key(name):
    key = name.upper().replace(".", "").replace("KEPULAUAN", "KEP")
    return re.sub(r"\s+", "", key)


def load_validation(provinces):
    key_by_norm = {norm_key(p["provinsi_key"]): p["provinsi_key"] for p in provinces}
    rows = []
    with open(ROOT / "outputs" / "pangantahan_validasi_model.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = key_by_norm.get(norm_key(r["provinsi"]))
            if key is None:
                raise ValueError(f"Provinsi validasi tidak dikenali: {r['provinsi']}")
            rows.append({
                "provinsi_key": key,
                "MAE_naive": round(float(r["MAE_naive"]), 4),
                "MAE_ets": round(float(r["MAE_ets"]), 4),
                "MAE_sarima": round(float(r["MAE_sarima"]), 4),
                "best_model": r["best_model"],
            })
    return rows


def to_script_json(obj, **kw):
    # "</" di dalam <script> bisa menutup tag lebih awal
    return json.dumps(obj, ensure_ascii=False, **kw).replace("</", "<\\/")


def main():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    data["validation"] = load_validation(data["provinces"])
    geo = json.loads((HERE / "indonesia-kabkota.geojson").read_text(encoding="utf-8"))

    template = (HERE / "src" / "template.html").read_text(encoding="utf-8")
    html = (template
            .replace("__SIAGA_DATA__", to_script_json(data))
            .replace("__SIAGA_GEO__", to_script_json(geo, separators=(",", ":"))))
    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html ditulis ({len(html) / 1e6:.2f} MB), {len(data['provinces'])} provinsi, "
          f"{len(geo['features'])} kab/kota, {len(data['validation'])} baris validasi")


if __name__ == "__main__":
    main()
