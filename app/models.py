from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Song(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    artists = db.Column(db.String(100))

class Lyric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.String(50), db.ForeignKey('song.id'))
    timestamp = db.Column(db.Float)
    line = db.Column(db.String(200))

    song = db.relationship('Song', backref=db.backref('lyrics', lazy=True))
