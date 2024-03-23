create table CONFIGURATION (
    ID integer not null primary key autoincrement,
    NAME text not null unique,
    CREATED text not null
);  

create table RECORDING (
    ID integer not null primary key autoincrement,
    UUID text not null unique,
    NAME text not null,
    CONFIGURATION_ID integer not null,
    SECONDS integer not null,
    IN_PROGRESS integer not null,
    IS_STANDBY integer not null,
    CREATED text not null
);