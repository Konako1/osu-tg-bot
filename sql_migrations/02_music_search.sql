CREATE TABLE IF NOT EXISTS music(
    id BIGINT NOT NULL GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    length INT NOT NULL,
    file_id TEXT NOT NULL,
    is_tv_size BOOLEAN NOT NULL,
    is_bpm_changed BOOLEAN NOT NULL,
    UNIQUE (artist, title, length, file_id)
);

CREATE TABLE IF NOT EXISTS music_tokens(
    word TEXT NOT NULL,
    file_id TEXT NOT NULL,
    UNIQUE (word, file_id)
);

CREATE TABLE IF NOT EXISTS mappers(
    id INT NOT NULL GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY ,
    mapper TEXT NOT NULL,
    beatmap_id INT NOT NULL,
    UNIQUE (mapper, beatmap_id)
);

CREATE TABLE IF NOT EXISTS music_mappers(
    music_id BIGINT NOT NULL REFERENCES music(id),
    mapper_id INT NOT NULL REFERENCES mappers(id),
    PRIMARY KEY (music_id, mapper_id)
);

CREATE INDEX ON music_tokens(word);