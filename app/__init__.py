
from io import BytesIO
from pathlib import Path
import warnings

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, UnidentifiedImageError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from app.image_processing import OPERATIONS, process_image

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    if test_config:
        app.config.update(test_config)

    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(error):
        return jsonify(error="Image exceeds the 8 MB upload limit."), 413

    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify(error="Invalid request."), 400

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="PixelLab")

    @app.post("/api/process")
    def process():
        upload = request.files.get("image")
        operation = request.form.get("operation", "").strip().lower()

        if upload is None or not upload.filename:
            return jsonify(error="Choose an image to upload."), 400

        if operation not in OPERATIONS:
            return jsonify(error="Choose a valid processing operation."), 400

        safe_original_name = secure_filename(Path(upload.filename).name)
        extension = Path(safe_original_name).suffix.lower()

        if not safe_original_name or extension not in ALLOWED_EXTENSIONS:
            return jsonify(error="Upload a JPG, JPEG, or PNG image."), 400

        brightness = 100

        if operation == "brightness":
            raw_brightness = request.form.get("brightness", "")

            try:
                if not raw_brightness.strip():
                    raise ValueError
                brightness = int(raw_brightness)
            except (ValueError, AttributeError):
                return jsonify(error="Brightness must be a whole number from 20 to 200."), 400

            if not 20 <= brightness <= 200:
                return jsonify(error="Brightness must be between 20 and 200."), 400

        try:
            upload.stream.seek(0)

            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)

                with Image.open(upload.stream) as image:
                    if image.format not in {"JPEG", "PNG"}:
                        return jsonify(error="The file contents must be a JPG or PNG image."), 400

                    if image.width * image.height > MAX_IMAGE_PIXELS:
                        return jsonify(error="Image dimensions are too large."), 400

                    image.verify()

                upload.stream.seek(0)

                with Image.open(upload.stream) as image:
                    image.load()
                    result = process_image(image, operation, brightness)

        except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError,
                Image.DecompressionBombWarning):
            return jsonify(error="The uploaded image is corrupted or invalid."), 400

        output = BytesIO()
        result.save(output, format="PNG", optimize=True)
        output.seek(0)

        original_stem = Path(safe_original_name).stem or "image"
        download_name = f"{original_stem}_{operation}.png"

        response = send_file(
            output,
            mimetype="image/png",
            as_attachment=True,
            download_name=download_name,
            max_age=0,
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
