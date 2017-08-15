import os
import sqlite3
from flask import (Flask, request, session, g, redirect, url_for, abort,
                   render_template, flash)


app = Flask(__name__)
app.config.from_object(__name__)


app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'blog.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
    ))

app.config.from_envvar('BLOG_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('SELECT * FROM blogs ORDER by id DESC')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/detail/<int:post_id>')
def detail_view(post_id):
    db = get_db()
    cur = db.execute('SELECT * FROM blogs WHERE id = ?', [post_id])
    entry = cur.fetchall()
    return render_template('detail.html', entries=entry)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
            'INSERT INTO blogs (title, content) VALUES (?, ?)',
            [
                request.form['title'],
                request.form['content']
            ]
    )
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/update/<int:post_id>')
def update_form(post_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    cur = db.execute(
                'SELECT * FROM blogs WHERE id = ?', [post_id]
                )
    entry = cur.fetchall()
    return render_template('update_form.html', entries=entry)


@app.route('/update', methods=['POST'])
def update_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute(
        'UPDATE blogs SET title = ?, content = ?  WHERE id = ?',
        [
            request.form['title'],
            request.form['content'],
            request.form['post_id']
        ]
    )
    db.commit()
    flash('Update was successfully posted')
    cur = db.execute('SELECT * FROM  blogs ORDER BY id DESC')
    update = cur.fetchall()
    return redirect(url_for('show_entries'))


@app.route('/delete', methods=['POST'])
def delete():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute(
            'DELETE FROM blogs WHERE id = ?',
            [request.form['post_id']])
    db.commit()
    flash('Delete successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))
