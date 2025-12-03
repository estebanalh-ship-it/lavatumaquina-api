from sqlalchemy import create_engine

DB_URI = "mysql+pymysql://Lavatumaquina01:Lavatest2025@Lavatumaquina01.mysql.pythonanywhere-services.com/Lavatumaquina01$default"
engine = create_engine(DB_URI, pool_pre_ping=True)

db_config = {
     'host': 'Lavatumaquina01.mysql.pythonanywhere-services.com',
     'user': 'Lavatumaquina01',
     'password': 'Lavatest2025',
     'database': 'Lavatumaquina01$default'
}