CREATE TABLE "user_group"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "position" INTEGER NOT NULL,
  "name" VARCHAR(128) NOT NULL,
  "visible" SMALLINT NOT NULL
);
CREATE INDEX "user_group_name" ON "user_group" ("name");


CREATE TABLE "user"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "username" VARCHAR(32) NOT NULL,
  "password" VARCHAR(512),
  "group_id" INTEGER NOT NULL,
  "refnum" VARCHAR(255),
  "name" VARCHAR(64) NOT NULL,
  "email" VARCHAR(64),
  "phone" VARCHAR(16),
  "birthday" DATE,
  "active" SMALLINT NOT NULL,
  FOREIGN KEY ("group_id") REFERENCES "user_group" ("id")
);
CREATE UNIQUE INDEX "user_username" ON "user" ("username");
CREATE INDEX "user_group_id" ON "user" ("group_id");

CREATE TABLE "publishplace"
(
  "name" VARCHAR(512) NOT NULL PRIMARY KEY
);
CREATE UNIQUE INDEX "publishplace_name" ON "publishplace" ("name");

CREATE TABLE "publisher"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(128) NOT NULL,
  "address" VARCHAR(1024), /* is the length ok? */
);
CREATE INDEX "publisher_imprint_of_id" ON "publisher" ("imprint_of_id");

CREATE TABLE "currency"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(32) NOT NULL,
  "symbol" VARCHAR(4) NOT NULL,
  "conversion_factor" REAL NOT NULL /* do we need this? */
);
CREATE UNIQUE INDEX "currency_name" ON "currency" ("name");


CREATE TABLE "author"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(128) NOT NULL,
  "is_pseudonym" SMALLINT NOT NULL, /* do we need this? */
  "author_sort" VARCHAR(128) NOT NULL /* will be auto-set by standardizing name */
);
CREATE INDEX "author_author_sort" ON "author" ("author_sort");


CREATE TABLE "location"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "prevent_borrowing" SMALLINT NOT NULL
);
CREATE UNIQUE INDEX "location_name" ON "location" ("name");

CREATE TABLE "item"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "accession" INTEGER NOT NULL,
  "pubtype" VARCHAR(32), /* is the size okay? should it be made into CHAR? */
  
  "title" VARCHAR(512) NOT NULL,
  "display_title" VARCHAR(256) NOT NULL,

  "call_no" VARCHAR(8) NOT NULL,
  "keywords" VARCHAR(1024), /* still need to decide on best way to do this */
  "comments" TEXT,

  "location_id" INTEGER NOT NULL,

  "receipt_date" DATE,
  "source" VARCHAR(512),
  "price" REAL,
  "price_currency_id" INTEGER,

  "identifier" VARCHAR(256),

  /* now comes the type-specific data */

  "publisher_id" INTEGER,
  "pub_place_id" INTEGER,
  "pub_date" DATE,

  "cover_content" VARCHAR(512), /* make it into text? */
  "issue" INTEGER,
  "vol_no" INTEGER,
  "vol_issue" INTEGER,
  "date" DATE,
  "date_hide_day" SMALLINT, /* eg. 'Jun 2015' instead of '12 Jun 2015' */

  /* foreign keys */
  
  FOREIGN KEY ("location_id") REFERENCES "location" ("id"),
  FOREIGN KEY ("price_currency_id") REFERENCES "currency" ("id"),


  /* type-specific foreign-keys */

  FOREIGN KEY ("publisher_id") REFERENCES "publisher" ("id"),
  FOREIGN KEY ("pub_place_id") REFERENCES "publishplace" ("id")
  
);


CREATE INDEX "item_price_currency_id" ON "item" ("price_currency_id");
CREATE UNIQUE INDEX "item_accession" ON "item" ("accession");
CREATE INDEX "item_location_id" ON "item" ("location_id");

/* type-specific indexes... */
/* ...or is it called "indices"? */
CREATE INDEX "item_publisher_id" ON "item" ("publisher_id");
CREATE INDEX "item_pub_place_id" ON "item" ("pub_place_id");

CREATE TABLE "borrowing"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "item_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  "borrow_date" DATETIME NOT NULL,
  "renew_times" INTEGER NOT NULL,
  "is_longterm" SMALLINT NOT NULL,
  FOREIGN KEY ("item_id") REFERENCES "item" ("id"),
  FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
  FOREIGN KEY ("group_id") REFERENCES "user_group" ("id"));
CREATE INDEX "borrowing_group_id" ON "borrowing" ("group_id");
CREATE INDEX "borrowing_user_id" ON "borrowing" ("user_id");
CREATE UNIQUE INDEX "borrowing_item_id" ON "borrowing" ("item_id");


CREATE TABLE "pastborrowing"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "accession" INTEGER NOT NULL, /* should this be made an FK? */
  "user_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  "borrow_date" DATETIME NOT NULL,
  "return_date" DATETIME NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
  FOREIGN KEY ("group_id") REFERENCES "user_group" ("id")
);
CREATE INDEX "pastborrowing_group_id" ON "pastborrowing" ("user_group_id");
CREATE INDEX "pastborrowing_user_id" ON "pastborrowing" ("user_id");

