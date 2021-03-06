import mysql.connector
from mysql.connector import Error
import pandas as pd
from typing import List, Optional

import constants as c


class Connector:
    """
    Allows inserting and retrieving training data from a MySQL database.
    """
    def __init__(self):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=c.HOST_NAME,
                user=c.USER_NAME,
                passwd=c.PASSWORD,
                database=c.DATABASE,
            )
        except Error as e:
            print(f"The error '{e}' occurred")

    def insert_examples(self, examples: List[tuple], table: str) -> None:
        """
        Inserts training examples into a database table. A new table is created if none with the given name exists.

        :param examples: List of examples as List[(state,(policy, value))]
        :param table: Name of the database table
        """
        self._create_training_data_table(table)
        for ex in examples:
            self._send_query(
                f"INSERT INTO {table} (STATE, MOVE, VAL)"
                f"VALUES ('{ex[0]}', '{ex[1][0]}', '{ex[1][1]}');",
                print_out_errors=False
            )
        print(f'Inserted {len(examples)} examples.')

    def get_data(self, limit: Optional[int], table: str) -> pd.DataFrame:
        """
        Returns a random sample of training examples as s pandas DataFrame.

        :param limit: Number of examples, None gives all examples in the table
        :param table: Name of the database table
        :return: Pandas DataFrame with examples as ['state', 'move', 'val']
        """
        return self._retrieve_data(
            f"SELECT state, move, val FROM {table} ORDER BY RAND() {f'LIMIT {limit}' if limit else ''};"
        )

    def _send_query(self, query: str, print_out=False, print_out_errors=True) -> Optional[List[tuple]]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.connection.commit()
            if print_out:
                print('send query successfully')
            return result
        except Error as e:
            if print_out_errors:
                print(f"The error '{e}' occurred")

    def _retrieve_data(self, query: str) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_sql(query, self.connection)
            self.connection.commit()
            return df
        except Error as e:
            print(f"The error '{e}' occurred")

    def _create_training_data_table(self, table: str) -> None:
        self._send_query(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            f"id INT(11) NOT NULL AUTO_INCREMENT,"
            f"state VARCHAR(100) UNIQUE NOT NULL,"
            f"move CHAR(4) NOT NULL,"
            f"val DECIMAL(10,7) NOT NULL,"
            f"PRIMARY KEY (ID)"
            f");"
        )
        self._send_query(
            f"CREATE UNIQUE INDEX state_index ON {table}(state);",
            print_out_errors=False
        )



