from datetime import datetime
from shire.app import app, db, User, Thing, ThingNote, Category, Progress

def _populate_db():
    """Populate testing data into database. """

    user = User.new('soasme', 'soasme@gmail.com', 'Ju', '111111')
    user.is_charged = True
    db.session.add(user)
    db.session.commit()

    thing_annihilation = Thing(user_id=user.id, category=Category.movie,
            title="Annihilation", shared=True,
            tags=["scifi", "horror", "NataliePortman"],
            extended={"Directed by": "Alex Garland", "Year": "2018", },
            time=datetime(2019, 10, 18, 10, 45, 00))
    db.session.add(thing_annihilation)
    db.session.commit()
    thing_annihilation_note = ThingNote(thing_id=thing_annihilation.id,
            user_id=user.id,
            text="""This is a new story that I've never seen. It was awesome.""",
            shared=True)
    db.session.add(thing_annihilation_note)
    db.session.commit()
    thing_orphan_train = Thing(user_id=user.id, category=Category.book,
            title="Orphan Train", shared=True,
            tags=["fiction", "novel"],
            extended={"ISBN": "9780061950728", "Author": "Christina Baker Kline"},
            time=datetime(2019, 7, 20, 10, 00, 00))
    db.session.add(thing_orphan_train)
    db.session.commit()
    thing_puyopuyo_tetris = Thing(user_id=user.id, category=Category.game,
            title="Puyo Puyo Tetris", shared=True,
            tags=["tetris", "nintendo", "switch", "puzzle"],
            extended={"Platform": "Nintendo Switch"},
            time=datetime(2019, 10, 18, 12, 00, 00))
    db.session.add(thing_puyopuyo_tetris)
    db.session.commit()
    thing_lover = Thing(user_id=user.id, category=Category.album,
            title="Lover", shared=True,
            tags=["TaylorSwift", "pop", "pop rock", "electropop"],
            extended={"Singer": "Taylor Swift"},
            time=datetime(2019, 8, 23, 0, 0, 0))
    db.session.add(thing_lover)
    db.session.commit()
    thing_queenstown_trail = Thing(user_id=user.id, category=Category.place,
            title="Queenstown Trail", shared=True,
            tags=["cycling", "NewZealand"],
            url='https://queenstowntrail.co.nz/',
            extended={},
            time=datetime(2019, 10, 12, 12, 30, 0))
    db.session.add(thing_queenstown_trail)
    db.session.commit()



def _reset_db():
    """Reset testing database."""
    import os; os.unlink('/tmp/pth.db')
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        _reset_db()
        _populate_db()
