class LogActionRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM log_action;")
            log = cursor.fetchall()
        return log

    def get_by_id(self, log_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM log_action WHERE id = %s;", (log_id,))
            log = cursor.fetchone()
        return log

    def get_by_user_id(self, user_id, limit=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM log_action WHERE users_id = %s ORDER BY data_action DESC"
            params = [user_id]
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            logs = cursor.fetchall()
        return logs

    def create(self, action, data_action, users_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO log_action 
                (action, data_action, users_id) 
                VALUES (%s, %s, %s);
            """, (action, data_action, users_id))
            connection.commit()
            return cursor.lastrowid

    def delete_old_logs(self, days_to_keep=30):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                DELETE FROM log_action 
                WHERE data_action < DATE_SUB(NOW(), INTERVAL %s DAY);
            """, (days_to_keep,))
            connection.commit()