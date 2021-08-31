

-- SQL update SendStatus table
UPDATE send_status SET has_sent = 'False' WHERE match = 6305;

-- alc delete data from table
  # SendStatus.query.delete()


CREATE TABLE telegram_users (
	telegram_id INT PRIMARY KEY,
	first_name VARCHAR ( 50 ) NOT NULL,
	last_name  VARCHAR ( 50 ) NOT NULL);

CREATE TABLE players (
	player_id INT PRIMARY KEY,
	first_name VARCHAR ( 50 ) NOT NULL,
	last_name  VARCHAR ( 50 ) NOT NULL,
  playing BOOL DEFAULT 'f' );

CREATE TABLE results_for (
  id INT PRIMARY KEY,
  telegram_id INTEGER REFERENCES telegram_users ON DELETE CASCADE,
  player_id INTEGER REFERENCES players ON DELETE CASCADE);

CREATE TABLE alerts_for (
  id INT PRIMARY KEY,
  telegram_id INTEGER REFERENCES telegram_users ON DELETE CASCADE,
  player_id INTEGER REFERENCES players ON DELETE CASCADE);

