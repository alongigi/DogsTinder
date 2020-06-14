#!/usr/bin/env bash
os=$(awk -F= '/^NAME/{print $2}' /etc/os-release)


set_mysql() {
	systemctl enable $1
	systemctl start $1
}

if [ $os == '"Ubuntu"' ]
then
    apt-get update
    # !----------! Setting MySQL root user password root/root !----------!
    debconf-set-selections <<< 'mysql-server mysql-server/root_password password LoginPass@@12'
    debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password LoginPass@@12'
    # !----------! install python and mysql !----------!
    apt-get -y install python3-pip mysql-server mysql-client
    set_mysql "mysql"


fi
pip3 install -r /vagrant/requirements.txt

    new_pw='LoginPass@@12'
    mysql -u root -p"$new_pw" <<MYSQL_SCRIPT
    CREATE DATABASE DogsTinder;
    USE DogsTinder;
    create table users(username VARCHAR(25) NOT NULL, password VARCHAR(100) NOT NULL, firstName VARCHAR(25) NOT NULL, lastName VARCHAR(25) NOT NULL,
    phone VARCHAR(11) NOT NULL, email VARCHAR(50) NOT NULL, create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, PRIMARY KEY(username));
    create table dogs(dog_id VARCHAR(10) NOT NULL, name VARCHAR(25) NOT NULL, bday DATE NOT NULL, gender VARCHAR(9) NOT NULL, area VARCHAR(20) NOT NULL, city VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL, details TEXT NOT NULL, pic1 LONGBLOB NOT NULL,path1 TEXT NOT NULL, pic2 LONGBLOB, path2 TEXT, pic3 LONGBLOB, path3 TEXT, username VARCHAR(25), primary key(dog_id), foreign key(username) references users(username));
    create table likes(username varchar(25), dog_id int(11), answer varchar(10));
    create table adopted(dog_id VARCHAR(10) NOT NULL, name VARCHAR(25) NOT NULL, bday DATE NOT NULL, gender VARCHAR(9) NOT NULL, area VARCHAR(20) NOT NULL, city VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL, details TEXT NOT NULL, pic1 BLOB NOT NULL,path1 TEXT NOT NULL, path2 TEXT, path3 TEXT, pic2 BLOB, pic3 BLOB, username VARCHAR(25));
    create table messages(message_id int NOT NULL AUTO_INCREMENT, sender_username VARCHAR(25) NOT NULL, 
    receiver_username VARCHAR(25) NOT NULL, content text NOT NULL, sending_date datetime NOT NULL, 
    meeting_proposal VARCHAR(5) NOT NULL, primary key(message_id), foreign key(sender_username) references users(username),
    foreign key(receiver_username) references users(username));
    DESCRIBE users;
    DESCRIBE dogs;
    DESCRIBE likes;
    DESCRIBE adopted;
    DESCRIBE messages;
MYSQL_SCRIPT

    chmod 755 /vagrant/app.py
    nohup python3 /vagrant/app.py > /dev/null 2>&1 &