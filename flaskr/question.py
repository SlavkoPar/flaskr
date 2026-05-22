from urllib import request

from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)
from werkzeug.exceptions import abort


from .auth import login_required
from .db import get_db

bp = Blueprint("question", __name__)


@bp.route("/<int:category_id>/")
def index(category_id):
    """Show all the questions, most recent first."""
    db = get_db()
    questions = db.execute(
        "SELECT id, text, link, created, author_id"
        " FROM question"
        " WHERE category_id = ?"
        " ORDER BY created DESC",
        (category_id,)
    ).fetchall()
    return render_template("question/index.html", questions=questions)


def get_question(id, check_author=True):
    """Get a question and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of question to get
    :param check_author: require the current user to be the author
    :return: the question with author information
    :raise 404: if a question with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    question = (
        get_db()
        .execute(
            "SELECT category_id, c.id, text, link, created, author_id, username"
            " FROM question c JOIN user u ON c.author_id = u.id"
            " WHERE c.id = ?",
            (id,),
        )
        .fetchone()
    )

    if question is None:
        abort(404, f"Question id {id} doesn't exist.")

    if check_author and question["author_id"] != g.user["id"]:
        abort(403)

    return question


@bp.route("/<int:category_id>/add_question", methods=("GET", "POST"))
@login_required
def create(category_id):
    """Create a new question for the current user."""
    if request.method == "POST":
        text = request.form["text"]
        link = request.form["link"]
        error = None

        if not text:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO question (text, link, author_id, category_id) VALUES (?, ?, ?, ?)",
                (text, link, g.user["id"], category_id),
            )
            db.commit()
            # return redirect(url_for("question.index", category_id=category_id))
            return redirect(url_for("category.update", id=category_id))

    return render_template("question/create.html", category_id=category_id)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a question if the current user is the author."""
    question = get_question(id)

    if request.method == "POST":
        text = request.form["text"]
        link = request.form["link"]
        error = None

        if not text:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE question SET text = ?, link = ? WHERE id = ?", (text, link, id)
            )
            db.commit()
            # return redirect(url_for("question.index"))
            return redirect(url_for("category.update", id=question["category_id"]))
    return render_template("question/update.html", question=question)



@bp.route("/<int:id>/delete", methods=("POST","GET"))
@login_required
def delete(id):
    """Delete a question.

    Ensures that the question exists and that the logged in user is the
    author of the question.
    """
    question = get_question(id)
    db = get_db()
    db.execute("DELETE FROM question WHERE id = ?", (id,))
    db.commit()
    # return redirect(url_for("question.index"))
    return redirect(url_for("category.update", id=question["category_id"]))
