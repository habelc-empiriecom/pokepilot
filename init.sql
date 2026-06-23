CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER,
    name TEXT,
    type1 TEXT,
    type2 TEXT,
    total INTEGER,
    hp INTEGER,
    attack INTEGER,
    defense INTEGER,
    sp_atk INTEGER,
    sp_def INTEGER,
    speed INTEGER,
    generation INTEGER,
    legendary BOOLEAN
);

COPY pokemon(id, name, type1, type2, total, hp, attack, defense, sp_atk, sp_def, speed, generation, legendary)
FROM '/docker-entrypoint-initdb.d/pokemon.csv'
DELIMITER ','
CSV HEADER;
