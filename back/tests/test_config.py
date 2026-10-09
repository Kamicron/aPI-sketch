from sqlalchemy.engine import make_url

from app.config import Settings


def test_url_mysql_avec_caracteres_speciaux():
    s = Settings(
        _env_file=None,
        database_url="",
        db_host="localhost",
        db_username="api-sketch",
        db_password="p@ss:w/rd#1%",
        db_name="aPI-sketch",
    )
    url = make_url(s.sqlalchemy_url)
    assert url.host == "localhost"
    assert url.port == 3306
    assert url.username == "api-sketch"
    assert url.password == "p@ss:w/rd#1%"
    assert url.database == "aPI-sketch"
