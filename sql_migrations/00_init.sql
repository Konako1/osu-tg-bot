CREATE TABLE remembered_users(
    tg_id INT PRIMARY KEY NOT NULL,
    osu_id INT NOT NULL);
CREATE TABLE osu_users(
    osu_id INT PRIMARY KEY NOT NULL,
    username TEXT NOT NULL);
CREATE TABLE beatmap_data(
    map_id INT PRIMARY KEY NOT NULL,
    data TEXT NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL );
CREATE TABLE score_positions(
    score_id INT PRIMARY KEY NOT NULL,
    position BIGINT NOT NULL
);
CREATE TABLE stat(
    id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    command TEXT NOT NULL,
    tg_user_id INT NOT NULL
)