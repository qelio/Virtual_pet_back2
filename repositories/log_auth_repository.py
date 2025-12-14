class LogAuthRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM log_auth;")
            log = cursor.fetchall()
        return log

    def get_by_id(self, log_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM log_auth WHERE id = %s;", (log_id,))
            log = cursor.fetchone()
        return log

    def get_by_user_id(self, user_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM log_auth WHERE users_id = %s ORDER BY data_auth DESC;", (user_id,))
            logs = cursor.fetchall()
        return logs

    def create(self, data_auth, remember_me, users_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO log_auth 
                (data_auth, remember_me, users_id) 
                VALUES (%s, %s, %s);
            """, (data_auth, remember_me, users_id))
            connection.commit()
            return cursor.lastrowid

    def delete_old_logs(self, user_id, keep_last=5):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                DELETE FROM log_auth 
                WHERE users_id = %s AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM log_auth 
                        WHERE users_id = %s 
                        ORDER BY data_auth DESC 
                        LIMIT %s
                    ) AS temp
                );
            """, (user_id, user_id, keep_last))
            connection.commit()