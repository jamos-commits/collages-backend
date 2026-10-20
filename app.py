import io
import re
import ssl
import urllib.request
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite peticiones desde Google Sites

ssl_context = ssl._create_unverified_context()


def extraer_fotos_mercadolibre(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ssl_context) as response:
        html = response.read().decode("utf-8", errors="ignore")

    foto_ids = re.findall(
        r"D_NQ_NP_(?:2X_)?([0-9]+-[A-Z]+[0-9]+_[0-9]+)", html
    )

    unique_ids = []
    seen = set()
    for f_id in foto_ids:
        f_id_clean = f_id.strip()
        if f_id_clean not in seen:
            seen.add(f_id_clean)
            unique_ids.append(f_id_clean)

    return [
        f"https://http2.mlstatic.com/D_NQ_NP_2X_{f_id}-O.webp"
        for f_id in unique_ids
    ]


@app.route("/api/extraer", methods=["GET"])
def api_extraer():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "Falta la URL de MercadoLibre"}), 400

    try:
        urls_fotos = extraer_fotos_mercadolibre(url)
        if not urls_fotos:
            return (
                jsonify(
                    {"error": "No se encontraron fotos en la publicación"}
                ),
                404,
            )
        return jsonify({"fotos": urls_fotos})
    except Exception as e:
        return jsonify({"error": f"Error al procesar: {str(e)}"}), 500


@app.route("/", methods=["GET"])
def home():
    return "Servidor Backend de Collages Activo ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)