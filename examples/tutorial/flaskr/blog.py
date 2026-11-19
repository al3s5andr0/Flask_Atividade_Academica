from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .models import Post, db

import os

from flask import current_app

from .uploads import save_upload

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    posts = Post.query.order_by(Post.created.desc()).all()
    return render_template("blog/index.html", posts=posts)


def get_post(id, check_author=True):
    post = db.session.get(Post, id)

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None
        image_name = None

        if not title:
            error = "Title is required."

        if error is None:
            try:
                image_name = save_upload(request.files.get("imagem_post"))
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            db.session.add(
                Post(title=title, body=body, author_id=g.user.id,
                     imagem_post=image_name)
            )
            db.session.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None
        new_image = None

        if not title:
            error = "Title is required."

        if error is None:
            try:
                new_image = save_upload(request.files.get("imagem_post"))
            except ValueError as e:
                error = str(e)

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            if new_image:
                # apaga a imagem antiga e guarda a nova
                if post.imagem_post:
                    old = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], post.imagem_post
                    )
                    if os.path.exists(old):
                        os.remove(old)
                post.imagem_post = new_image
            db.session.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("blog.index"))