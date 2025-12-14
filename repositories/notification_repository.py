class NotificationRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, notification_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM notifications WHERE id = %s;", (notification_id,))
            notification = cursor.fetchone()
        return notification

    def get_by_user_id(self, user_id, is_read=None, limit=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM notifications WHERE users_id = %s"
            params = [user_id]
            
            if is_read is not None:
                query += " AND is_read = %s"
                params.append(is_read)
            
            query += " ORDER BY created_at DESC"
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            notifications = cursor.fetchall()
        return notifications

    def create(self, message, created_at, is_read, users_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO notifications 
                (message, created_at, is_read, users_id) 
                VALUES (%s, %s, %s, %s);
            """, (message, created_at, is_read, users_id))
            connection.commit()
            return cursor.lastrowid

    def mark_as_read(self, notification_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = 1 
                WHERE id = %s;
            """, (notification_id,))
            connection.commit()

    def mark_all_as_read(self, user_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = 1 
                WHERE users_id = %s AND is_read = 0;
            """, (user_id,))
            connection.commit()

    def delete(self, notification_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("DELETE FROM notifications WHERE id = %s;", (notification_id,))
            connection.commit()

    def get_all_notifications(self, user_id=None, is_read=None, limit=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM notifications"
            params = []

            conditions = []
            if user_id is not None:
                conditions.append("users_id = %s")
                params.append(user_id)
            if is_read is not None:
                conditions.append("is_read = %s")
                params.append(is_read)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)

            cursor.execute(query, params)
            return cursor.fetchall()