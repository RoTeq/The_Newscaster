import sqlite_inter


db = sqlite_inter.oracleDB("resources/oracle.db")


print(f"{db.get_top_ghouls(10)}")