import re
import ssl
import urllib.request
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Permitir peticiones CORS desde cualquier origen (Google Sites, localhost, etc.)
CORS(app)

ssl_context = ssl._create_unverified_context()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
}


def extraer_fotos_mercadolibre(url):
    # 1. Realizar la petición HTTP con timeout
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
        html = response.read().decode("utf-8", errors="ignore")

    # 2. Expresión regular que captura IDs de alta resolución de ML
    # Soporta formatos como 123456-MLA123456789_012024 y variantes
    foto_ids = re.findall(
        r"D_NQ_NP_(?:2X_)?([0-9]+-[A-Z0-9]+(?:_[0-9]+)?)", html
    )

    # 3. Eliminar duplicados preservando el orden original de las fotos
    unique_ids = []
    seen = set()
    for f_id in foto_ids:
        f_id_clean = f_id.strip()
        if f_id_clean not in seen:
            seen.add(f_id_clean)
            unique_ids.append(f_id_clean)

    # 4. Devolver las URLs en calidad original (-O.webp)
    return [
        f"https://http2.mlstatic.com/D_NQ_NP_2X_{f_id}-O.webp"
        for f_id in unique_ids
    ]


@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    """Ruta para verificar que el servidor está vivo (y para UptimeRobot)"""
    return jsonify({
        "status": "online",
        "service": "MercadoLibre Collages Backend",
        "version": "1.0"
    }), 200


@app.route("/api/extraer", methods=["GET"])
def api_extraer():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Falta el parámetro 'url' de MercadoLibre"}), 400

    if "mercadolibre." not in url:
        return jsonify({"error": "La URL no parece ser de MercadoLibre"}), 400

    try:
        urls_fotos = extraer_fotos_mercadolibre(url)
        if not urls_fotos:
            return jsonify({
                "error": "No se encontraron fotos en la publicación. Verifica que la publicación esté activa."
            }), 404

        return jsonify({
            "ok": True,
            "total": len(urls_fotos),
            "fotos": urls_fotos
        })

    except urllib.error.HTTPError as e:
        return jsonify({"error": f"MercadoLibre respondió con error: HTTP {e.code}"}), 502
    except urllib.error.URLError:
        return jsonify({"error": "No se pudo conectar con MercadoLibre (timeout o error de red)"}), 504
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


@app.route("/api/proxy", methods=["GET"])
def proxy_imagen():
    """
    Ruta opcional por si el navegador bloquea el Canvas por CORS.
    Permite cargar: /api/proxy?url=https://http2.mlstatic.com/...
    """
    img_url = request.args.get("url", "")
    if not img_url or not img_url.startswith("https://http2.mlstatic.com/"):
        return jsonify({"error": "URL de imagen no permitida"}), 400

    try:
        req = urllib.request.Request(img_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
            content = resp.read()
            content_type = resp.headers.get("Content-Type", "image/webp")
            return Response(
                content,
                mimetype=content_type,
                headers={"Access-Control-Allow-Origin": "*"}
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Para desarrollo local; en Render se recomienda usar gunicorn
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
