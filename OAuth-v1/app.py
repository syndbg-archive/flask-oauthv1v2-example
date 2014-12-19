from flask import Flask, session, request, render_template, redirect, jsonify
from flask_oauthlib.provider import OAuth1Provider
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import gen_salt


# APP
app = Flask(__name__, template_folder='templates')
app.secret_key = 'whatever'
app.config.update({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///db.sqlite',
})
db = SQLAlchemy(app)
oauth = OAuth1Provider(app)


# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)


class Client(db.Model):
    client_key = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), nullable=False)

    user_id = db.Column(db.ForeignKey('user.id'))
    user = db.relationship('User')
    _realms = db.Column(db.Text)
    _redirect_uris = db.Column(db.Text)

    @property
    def redirect_uris(self):
        return self._redirect_uris.split() if self._redirect_uris else []

    @property
    def default_realms(self):
        return self._realms.split() if self._realms else []


# HELPERS
def current_user():
    if 'id' not in session:
        return
    return User.query.get(session['id'])


# ROUTES
@app.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
        session['id'] = user.id
        return redirect('/')
    user = current_user()
    return render_template('home.html', user=user)


@app.route('/client')
def client():
    user = current_user()
    if not user:
        return redirect('/')
    item = Client(
        client_key=gen_salt(40),
        client_secret=gen_salt(55),
        user_id=user.id,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(
        client_key=item.client_key,
        client_secret=item.client_secret,
    )


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
