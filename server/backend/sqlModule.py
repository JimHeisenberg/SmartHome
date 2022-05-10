import json
import datetime
import pymysql


class MYSQL():
    """
    mysql opreations  
    init paramaters:
        database: string, database name in sql
        user: string, sql username
        host: string, sql server ip address, default "localhost
        port: integer, sql port, default "5432"
    return
        object of mysql class

    e.g. mysql = sql.MYSQL(database="SmartPillowDB",user="jim",password="jimmysql")
    """

    def __init__(self, database, user, password, host="localhost"):
        """
        init connection info
        """
        self.database = database
        self.user = user
        self.password = password
        self.host = host

    def _connect(self):
        """shortcut for pymysql.connect"""
        return pymysql.connect(database=self.database, user=self.user, password=self.password, host=self.host)

    def _check(self, data):
        """
        check if dangerous characters are in data  
        to prevent sql injection  
        do not return if pass else raise exception  
        """
        if type(data) is str:
            if '"' in data or "'" in data or ';' in data or '-' in data:
                raise Exception("dangerous character may cause sql injection")

    def _autoConvert(self, data, addSingleQuote=True):
        """
        change data into sql command form  
        convert datetime into str with single quote,  
        auto add single quote for str,  
        other types of data will be changed to str  
        e.g. _autoConvert(123) => str(123)  
        _autoConvert(asd) => str('asd')  
        """
        self._check(data)
        if type(data) in (datetime.date, datetime.datetime, datetime.time):
            data = data.isoformat()
        if type(data) is dict:
            data = json.dumps(data)
        if type(data) is str and addSingleQuote:
            data = "'" + data + "'"
        if type(data) is bytes:
            data = data.hex()
            data = "UNHEX('" + data + "')"
        if data is None:
            data = "NULL"
        return str(data)

    def exe(self, command):
        """
        Run a command  
        paramaters:
            command: string, sql command
        return:
            cursor.fetchall(), if cursor.fetchall() has a result
            None, otherwise
        """
        result = None
        connection = self._connect()
        cursor = connection.cursor()
        cursor.execute(command)
        try:
            result = cursor.fetchall()
        except:
            pass
        cursor.close()
        connection.commit()
        connection.close()
        return result

    def select(self, columns, table, condition=None):
        """
        SELECT columns FROM table WHERE condition;  
        paramaters:
            table: string, table name
            columns: a tuple of string or "*", contains columns you want, e.g. ("UserName", "Password")
            condition: string, default is None, e.g. f" UID='{UID}' "
        """
        command = "SELECT "
        if columns == "*":
            command += " * "
        elif type(columns) is str:
            command += self._autoConvert(columns, False)
        elif type(columns) is tuple or type(columns) is list:
            command += self._autoConvert(columns[0], False)
            for column in columns[1:]:
                command += ',' + self._autoConvert(column, False)
        command += " FROM "
        command += self._autoConvert(table, False)
        if condition is not None:
            command += " WHERE " + condition
        command += ";"
        result = self.exe(command)
        return result

    def insert(self, data, table):
        """
        INSERT INTO table VALUES data;
        paramaters:
            data: dict, e.g. {"UserID":"123","UserName":"Tom","Password":"1234"}
            table: string, table name
        """
        command = "INSERT INTO "
        command += self._autoConvert(table, False) + '('
        columns = list(data.keys())
        command += self._autoConvert(columns[0], False)
        for column in columns[1:]:
            command += ',' + self._autoConvert(column, False)
        command += ') VALUES ('
        values = list(data.values())
        command += self._autoConvert(values[0])
        for value in values[1:]:
            command += ',' + self._autoConvert(value)
        command += ');'
        result = self.exe(command)
        return result

    def delete(self, table, condition=None):
        """
        DELETE FROM table WHERE condition;
        paramaters:
            table: string, table name
            condition: string, default is None, e.g. f" UID='{UID}' "
        """
        command = "DELETE FROM "
        command += self._autoConvert(table, False)
        if condition is not None:
            command += " WHERE " + condition
        else:
            raise Exception("dangerous condition",
                            "please double check and use MYSQL.exe instead")
        command += ';'
        result = self.exe(command)
        return result

    def update(self, data, table, condition=None):
        """
        UPDATE table SET data WHERE condition;
        paramaters:
            data: dict, e.g. {"UserID":"123","UserName":"Tom","Password":"1234"}
            table: string, table name
            condition: string, default is None, e.g. f" UID='{UID}' "
        """
        command = "UPDATE "
        command += self._autoConvert(table, False) + " SET "
        items = list(data.items())
        command += self._autoConvert(items[0][0], False) + \
            '=' + self._autoConvert(items[0][1])
        for item in items[1:]:
            command += ',' + self._autoConvert(item[0], False) + \
                '=' + self._autoConvert(item[1])
        if condition is not None:
            command += " WHERE " + condition
        else:
            raise Exception("dangerous condition",
                            "please double check and use MYSQL.exe() instead")
        command += ";"
        result = self.exe(command)
        return result


if __name__ == "__main__":
    pass
