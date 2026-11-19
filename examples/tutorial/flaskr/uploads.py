import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def save_upload(file):
    """Salva a imagem e devolve o nome do arquivo (ou None se não enviou)."""
    if file is None or file.filename == "":
        return None

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato inválido. Use png, jpg, jpeg, gif ou webp.")

    unique_name = f"{uuid.uuid4().hex}_{filename}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name))
    return unique_name