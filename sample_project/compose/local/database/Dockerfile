FROM postgres:14

COPY ./compose/local/database/create_database.sh /docker-entrypoint-initdb.d/

RUN chmod +x /docker-entrypoint-initdb.d/create_database.sh
