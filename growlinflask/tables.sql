CREATE TABLE "group"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "position" INTEGER NOT NULL,
  "name" VARCHAR(128) NOT NULL,
  "visible" SMALLINT NOT NULL
);
CREATE INDEX "group_name" ON "group" ("name");


CREATE TABLE "user"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "username" VARCHAR(32) NOT NULL,
  "password" VARCHAR2(512),
  "group_id" INTEGER NOT NULL,
  "refnum" VARCHAR2(255),
  "name" VARCHAR(64) NOT NULL,
  "email" VARCHAR2(64),
  "phone" VARCHAR2(16),
  "birthday" DATE,
  "active" SMALLINT NOT NULL,
  FOREIGN KEY ("group_id") REFERENCES "group" ("id")
);
CREATE UNIQUE INDEX "user_username" ON "user" ("username");
CREATE INDEX "user_group_id" ON "user" ("group_id");

CREATE TABLE "publishplace"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(512) NOT NULL
);
CREATE UNIQUE INDEX "publishplace_name" ON "publishplace" ("name");

CREATE TABLE "publisher"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR(256) NOT NULL,
  "address" TEXT,
  "imprint_of_id" INTEGER, /* do we need this? */
  FOREIGN KEY ("imprint_of_id") REFERENCES "publisher" ("id")
);
CREATE INDEX "publisher_imprint_of_id" ON "publisher" ("imprint_of_id");

CREATE TABLE "currency"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "name" VARCHAR2(32) NOT NULL,
  "symbol" VARCHAR2(4) NOT NULL,
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

CREATE TABLE "publication"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "title" VARCHAR(512) NOT NULL,
  "display_title" VARCHAR(256) NOT NULL,
  "pubtype" VARCHAR(255),
  "pubdata_id" INTEGER,
  "identifier" VARCHAR(256),
  "call_no" VARCHAR(8) NOT NULL,
  "keywords" VARCHAR(1024),
  "comments" TEXT
);

CREATE TABLE "copy"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "accession" INTEGER NOT NULL,
  "item_id" INTEGER NOT NULL,
  "location_id" INTEGER NOT NULL,
  "copydata_type" VARCHAR(255),
  "copydata_id" VARCHAR(255),
  "price" REAL,
  "price_currency_id" INTEGER,
  "receipt_date" DATE,
  "source" VARCHAR(512),
  FOREIGN KEY ("item_id") REFERENCES "publication" ("id"),
  FOREIGN KEY ("location_id") REFERENCES "location" ("id"),
  FOREIGN KEY ("price_currency_id") REFERENCES "currency" ("id")
);
CREATE INDEX "copy_price_currency_id" ON "copy" ("price_currency_id");
CREATE UNIQUE INDEX "copy_accession" ON "copy" ("accession");
CREATE INDEX "copy_item_id" ON "copy" ("item_id");
CREATE INDEX "copy_location_id" ON "copy" ("location_id");


CREATE TABLE "borrowing"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "copy_id" INTEGER NOT NULL,
  "user_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL,
  "borrow_date" DATETIME NOT NULL,
  "renew_times" INTEGER NOT NULL,
  "is_longterm" SMALLINT NOT NULL,
  FOREIGN KEY ("copy_id") REFERENCES "copy" ("id"),
  FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
  FOREIGN KEY ("group_id") REFERENCES "group" ("id"));
CREATE INDEX "borrowing_group_id" ON "borrowing" ("group_id");
CREATE INDEX "borrowing_user_id" ON "borrowing" ("user_id");
CREATE UNIQUE INDEX "borrowing_copy_id" ON "borrowing" ("copy_id");


CREATE TABLE "pastborrowing"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "accession" INTEGER NOT NULL, "user_id" INTEGER NOT NULL,
  "group_id" INTEGER NOT NULL, "borrow_date" DATETIME NOT NULL,
  "return_date" DATETIME NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "user" ("id"),
  FOREIGN KEY ("group_id") REFERENCES "group" ("id")
);
CREATE INDEX "pastborrowing_group_id" ON "pastborrowing" ("group_id");
CREATE INDEX "pastborrowing_user_id" ON "pastborrowing" ("user_id");


CREATE TABLE "copybook"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "pub_name_id" INTEGER, "pub_place_id" INTEGER,
  "pub_date" DATE,
  FOREIGN KEY ("pub_name_id") REFERENCES "publisher" ("id"),
  FOREIGN KEY ("pub_place_id") REFERENCES "publishplace" ("id")
);
CREATE INDEX "copybook_pub_place_id" ON "copybook" ("pub_place_id");
CREATE INDEX "copybook_pub_name_id" ON "copybook" ("pub_name_id");


CREATE TABLE "pubperiodical"
(
  "id" INTEGER NOT NULL PRIMARY KEY,
  "cover_content" VARCHAR(512),
  "issue" INTEGER,
  "vol_no" INTEGER,
  "vol_issue" INTEGER,
  "date" DATE,
  "date_hide_day" SMALLINT
);
