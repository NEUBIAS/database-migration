FROM php:5.6-cli
RUN adduser bise
USER bise
WORKDIR /tmp
RUN curl -O https://raw.githubusercontent.com/pantheon-systems/terminus-installer/master/builds/installer.phar

USER root
RUN apt-get update
RUN apt-get install unzip
RUN apt-get install ssh


USER bise
RUN php installer.phar install

see http://docs.drush.org/en/master/install/
