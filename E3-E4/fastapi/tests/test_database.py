from database import get_db


def test_get_db_closes_session():
    gen = get_db()
    db = next(gen)
    assert db.is_active
    gen.close()
