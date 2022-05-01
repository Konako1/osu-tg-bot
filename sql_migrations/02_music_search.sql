CREATE TABLE IF NOT EXISTS music_search(
    beatmap_id BIGINT NOT NULL PRIMARY KEY,
    file_id TEXT NOT NULL,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    length INT NOT NULL,
    mapper TEXT
);

CREATE TABLE IF NOT EXISTS music_tokens(
    word TEXT NOT NULL,
    beatmap_id BIGINT NOT NULL,
    UNIQUE (word, beatmap_id)
);

CREATE INDEX ON music_tokens(word);