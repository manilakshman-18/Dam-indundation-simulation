from flask import Flask, render_template, request, jsonify
from pathlib import Path
from werkzeug.utils import secure_filename
import json
import uuid

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {".tif", ".tiff"}

# Approximate location of Mettur Dam.
# This is used only to center the demonstration map.
DAM_LAT = 11.7870
DAM_LON = 77.8000


def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def simulate():
    try:
        dam_name = request.form.get("dam_name", "Mettur Dam")
        model = request.form.get("model", "Preliminary scenario")
        water_level = request.form.get("water_level", "")
        breach_width = request.form.get("breach_width", "")
        simulation_time = request.form.get("simulation_time", "")

        # Validate numeric inputs.
        water_level = float(water_level)
        breach_width = float(breach_width)
        simulation_time = float(simulation_time)

        if water_level <= 0 or breach_width <= 0 or simulation_time <= 0:
            return jsonify({
                "error": "All numerical inputs must be greater than zero."
            }), 400

        # Save uploaded DEM.
        dem = request.files.get("dem")

        if dem is None or dem.filename == "":
            return jsonify({"error": "Please upload a DEM GeoTIFF file."}), 400

        if not allowed_file(dem.filename):
            return jsonify({
                "error": "Only .tif or .tiff DEM files are accepted."
            }), 400

        filename = secure_filename(dem.filename)
        saved_name = f"{uuid.uuid4().hex}_{filename}"
        dem.save(UPLOAD_DIR / saved_name)

        # IMPORTANT:
        # This polygon is only a visual demonstration.
        # It is NOT a hydrodynamic flood prediction.
        # It is NOT derived from the uploaded DEM.
        flood_polygon = {
            "type": "Feature",
            "properties": {
                "name": "Illustrative scenario area",
                "status": "NOT A HYDRODYNAMIC PREDICTION",
                "model": model
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [77.775, 11.805],
                    [77.825, 11.805],
                    [77.850, 11.770],
                    [77.820, 11.735],
                    [77.770, 11.745],
                    [77.750, 11.775],
                    [77.775, 11.805]
                ]]
            }
        }

        result = {
            "scenario_id": uuid.uuid4().hex[:8],
            "dam_name": dam_name,
            "model": model,
            "water_level": water_level,
            "breach_width": breach_width,
            "simulation_time": simulation_time,
            "dem_file": filename,
            "status": "Preliminary scenario generated",
            "warning": (
                "This is an illustrative map only. "
                "No SPH, Delft3D, or hydraulic calculation was performed."
            ),
            "flood_layer": {
                "type": "FeatureCollection",
                "features": [flood_polygon]
            }
        }

        result_file = BASE_DIR / "scenario_result.json"
        result_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

        return jsonify(result)

    except ValueError:
        return jsonify({
            "error": "Please enter valid numerical values."
        }), 400

    except Exception as error:
        return jsonify({
            "error": f"Server error: {error}"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)