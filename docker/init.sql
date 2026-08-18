CREATE SCHEMA qc;
ALTER SCHEMA qc OWNER TO qc_db_user;
ALTER DATABASE qc_db SET search_path TO qc, public;
