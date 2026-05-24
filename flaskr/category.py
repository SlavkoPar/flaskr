from urllib import request

from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("category", __name__)

@bp.route("/")
def index(expanded_id = None, questions = None):
    """Show all the categories, most recent first."""
    db = get_db()
    categories = db.execute(
        "SELECT c.id, c.name, c.description, c.created, c.author_id, COUNT(q.id) AS num_of_questions"
        " FROM category c LEFT OUTER JOIN question q ON c.id = q.category_id"
        " GROUP BY c.id"
        " ORDER BY c.created DESC"
    ).fetchall()
    return render_template("category/index.html", categories=categories, expanded_id=expanded_id, questions=questions)


def get_category(id, check_author=True):
    """Get a category and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of category to get
    :param check_author: require the current user to be the author
    :return: the category with author information
    :raise 404: if a category with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    category = (
        get_db()
        .execute(
            "SELECT c.id, name, description, c.created, c.author_id, username, COUNT(q.id) AS num_of_questions"
            " FROM category c "
            "JOIN user u ON c.author_id = u.id "
            "LEFT OUTER JOIN question q ON c.id = q.category_id"
            " WHERE c.id = ?"
            " GROUP BY c.id" ,
            (id,),
        )
        .fetchone()
    )

    if category is None:
        abort(404, f"Category id {id} doesn't exist.")

    if check_author and category["author_id"] != g.user["id"]:
        abort(403)

    return category

def get_category_questions(id, check_author=True):
    """Get a category and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of category to get
    :param check_author: require the current user to be the author
    :return: the category with author information
    :raise 404: if a category with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    questions = (
        get_db()
        .execute(
            "SELECT id, text, link, created, author_id"
            " FROM question"
            " WHERE category_id = ?"
            " ORDER BY created DESC",
            (id,)
        )
        .fetchall()
    )

    if questions is None:
        abort(404, f"Questions for category{id} doesn't exist.")

    # if check_author and category["author_id"] != g.user["id"]:
    #     abort(403)

    return questions


def get_category_questions_count(id, check_author=True):
    """Get the count of questions for a category.

    Checks that the id exists and optionally that the current user is
    the author.
    """

    questions_count = (
        get_db()
        .execute("SELECT COUNT(*) FROM question WHERE category_id = ?", (id,))
        .fetchone()
    )

    if questions_count is None:
        abort(404, f"Questions for category{id} doesn't exist.")

    # if check_author and category["author_id"] != g.user["id"]:
    #     abort(403)

    return questions_count


@bp.route("/<int:id>/add_question", methods=("GET", "POST"))
def add_question(id):
    return redirect(url_for("question.create", category_id=id))

@bp.route("/<int:id>/expand", methods=("GET", "POST"))
def expand(id):
    # return render_template("category/index.html", questions=get_category_questions(id), expanded_id = id)
    questions = get_category_questions(id)
    return index(expanded_id = id, questions = questions)

@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():

    """Create a new category for the current user."""
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        error = None

        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO category (name, description, author_id) VALUES (?, ?, ?)",
                (name, description, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("category.index"))

    return render_template("category/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a category if the current user is the author."""
    category = get_category(id)
    questions = get_category_questions(id)

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        error = None

        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE category SET name = ?, description = ? WHERE id = ?", (name, description, id)
            )
            db.commit()
            return redirect(url_for("category.index"))

    return render_template("category/update.html", category=category, questions=questions)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a category.

    Ensures that the category exists and that the logged in user is the
    author of the category.
    """
    get_category(id)
    db = get_db()
    db.execute("DELETE FROM category WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("category.index"))
