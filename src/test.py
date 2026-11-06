import sqlite_inter


db = sqlite_inter.oracleDB("resources/oracle.db")


print(f"{db.upsert_global("ghoul_count","22300")}")