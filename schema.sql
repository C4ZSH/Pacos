DROP TABLE IF EXISTS hashes;
CREATE TABLE hashes (
       urlhash text primary key not null,
       filehash text not null,
       filename text not null
       );
       
