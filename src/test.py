import sqlite_inter


db = sqlite_inter.oracleDB("resources/oracle.db")

print(f"{db.get_global_stat("ghoul_count",0)}")