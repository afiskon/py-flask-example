#!/usr/bin/env python3

import postgresql
import flask
import json

app = flask.Flask(__name__)

# disables JSON pretty-printing in flask.jsonify
# app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False # disables JSON
# pretty-printing

# TODO: use config!


def db_conn():
    return postgresql.open('pq://eax@192.168.122.184/eax')


def to_json(data):
    return json.dumps(data) + "\n"


def resp(code, data):
    return flask.Response(
        status=code,
        mimetype="application/json",
        response=to_json(data)
    )


def theme_validate():
    errors = []
    json = flask.request.get_json()
    if json is None:
        errors.append(
            "No JSON sent. Did you forget to set Content-Type header to application/json?")
        return (None, errors)

    for field_name in ['title', 'url']:
        if type(json.get(field_name)) is not str:
            errors.append(
                "Field '{}' is missing or is not a string".format(field_name))

    return (json, errors)


def affected_num_to_code(cnt):
    code = 200
    if cnt == 0:
        code = 404
    return code


@app.route('/')
def root():
    return flask.redirect('/api/1.0/themes')

# e.g. failed to parse json


@app.errorhandler(400)
def page_not_found(e):
    return resp(400, {})


@app.errorhandler(404)
def page_not_found(e):
    return resp(400, {})


@app.errorhandler(405)
def page_not_found(e):
    return resp(405, {})


@app.route('/api/1.0/themes', methods=['GET'])
def get_themes():
    with db_conn() as db:
        tuples = db.query("SELECT id, title, url FROM themes")
        themes = []
        for (id, title, url) in tuples:
            themes.append({"id": id, "title": title, "url": url})
        return resp(200, {"themes": themes})


@app.route('/api/1.0/themes', methods=['POST'])
def post_theme():
    (json, errors) = theme_validate()
    if errors:  # list is not empty
        return resp(400, {"errors": errors})

    with db_conn() as db:
        insert = db.prepare(
            "INSERT INTO themes (title, url) VALUES ($1, $2) RETURNING id")
        [(theme_id,)] = insert(json['title'], json['url'])
        return resp(200, {"theme_id": theme_id})


@app.route('/api/1.0/themes/<int:theme_id>', methods=['PUT'])
def put_theme(theme_id):
    (json, errors) = theme_validate()
    if errors:  # list is not empty
        return resp(400, {"errors": errors})

    with db_conn() as db:
        update = db.prepare(
            "UPDATE themes SET title = $2, url = $3 WHERE id = $1")
        (_, cnt) = update(theme_id, json['title'], json['url'])
        return resp(affected_num_to_code(cnt), {})


@app.route('/api/1.0/themes/<int:theme_id>', methods=['DELETE'])
def delete_theme(theme_id):
    with db_conn() as db:
        delete = db.prepare("DELETE FROM themes WHERE id = $1")
        (_, cnt) = delete(theme_id)
        return resp(affected_num_to_code(cnt), {})

if __name__ == '__main__':
    app.debug = True  # enables auto reload during development
    app.run()
