-- >> mysql # enter mysql command line first
-- >> DROP DATABASE SmartHomeDB;
CREATE DATABASE SmartHomeDB;

USE SmartHomeDB;

CREATE TABLE UserTable (
    UserID INT UNSIGNED NOT NULL AUTO_INCREMENT,
    UserName VARCHAR (30) NOT NULL,
    UserPassword VARBINARY (1024) NOT NULL,
    UserSalt VARBINARY (1024) NOT NULL,
    UserMeta VARCHAR (10000),
    PRIMARY KEY (UserID),
    UNIQUE KEY (UserName)
);

CREATE TABLE DeviceTable (
    DeviceID INT UNSIGNED NOT NULL AUTO_INCREMENT,
    DeviceName VARCHAR (30) NOT NULL,
    DevicePassword VARBINARY (1024) NOT NULL,
    DeviceType VARCHAR (30) NOT NULL,
    DeviceMeta VARCHAR (10000),
    DeviceDescription VARCHAR (500),
    DeviceIsOn BOOLEAN,
    DeviceIsOnline BOOLEAN,
    PRIMARY KEY (DeviceID),
    UNIQUE KEY (DeviceName)
);

CREATE TABLE InstructionTable (
    InstructionID INT UNSIGNED NOT NULL AUTO_INCREMENT,
    InstructionName VARCHAR (30) NOT NULL,
    InstructionMeta VARCHAR (10000),
    InstructionDescription VARCHAR (500),
    InstructionIsOn BOOLEAN,
    PRIMARY KEY (InstructionID),
    UNIQUE KEY (InstructionName)
);

CREATE TABLE UserDevicePermissionTable (
    PermissionID INT UNSIGNED NOT NULL AUTO_INCREMENT,
    UserID INT UNSIGNED NOT NULL,
    DeviceID INT UNSIGNED NOT NULL,
    PermissionrMeta VARCHAR (100),
    CanView BOOLEAN,
    CanControl BOOLEAN,
    CanManage BOOLEAN,
    PRIMARY KEY (PermissionID),
    UNIQUE KEY (UserID, DeviceID),
    FOREIGN KEY (UserID) REFERENCES UserTable (UserID) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (DeviceID) REFERENCES DeviceTable (DeviceID) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE DeviceInstructionLinkTable (
    LinkID INT UNSIGNED NOT NULL AUTO_INCREMENT,
    DeviceID INT UNSIGNED NOT NULL,
    InstructionID INT UNSIGNED NOT NULL,
    LinkMeta VARCHAR (100),
    LinkCondition BOOLEAN,
    LinkAction BOOLEAN,
    PRIMARY KEY (LinkID),
    UNIQUE KEY (DeviceID, InstructionID),
    FOREIGN KEY (DeviceID) REFERENCES DeviceTable (DeviceID) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (InstructionID) REFERENCES InstructionTable (InstructionID) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE USER 'jim' @'localhost' IDENTIFIED BY 'jimmysql';
GRANT ALL ON SmartHomeDB.* TO 'jim' @'localhost';

-- optimization :
-- mysql name-resolve cost lots of time, turn it off
-- vim /etc/mysql/my.cnf -- and add code below

-- [mysqld]
-- skip-name-resolve

-- Also, USER 'jim' @'localhost' becomes invalid, require adding a new user :
-- CREATE USER 'jim' @'127.0.0.1' IDENTIFIED BY 'jimmysql';
-- GRANT ALL ON SmartHomeDB.* TO 'jim' @'127.0.0.1';
-- Meanwhile, in python code, use ip instead of localhost :
-- mysql = sqlModule.MYSQL(database="SmartHomeDB",
--                         user="jim", password="jimmysql", host="127.0.0.1")
