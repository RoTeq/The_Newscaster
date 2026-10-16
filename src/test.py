import sqlite_inter


db = sqlite_inter.oracleDB("resources/oracle.db")


print(f"{db.get_user_stat(280364445421535233)}")