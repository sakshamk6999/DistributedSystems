# syntax=docker/dockerfile:1

# Use the base image mysql:latest
FROM mysql:latest

ENV MYSQL_ROOT_PASSWORD my-secret-pw

# Copy custom scripts or configuration files from your host to the container
COPY ./scripts/ /docker-entrypoint-initdb.d/