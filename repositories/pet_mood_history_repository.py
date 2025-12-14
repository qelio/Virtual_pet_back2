class PetMoodHistoryRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, history_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM pet_mood_history WHERE id = %s;", (history_id,))
            history = cursor.fetchone()
        return history

    def get_by_pet_id(self, pet_id, limit=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM pet_mood_history WHERE pets_id = %s ORDER BY changed_at DESC"
            params = [pet_id]
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            history = cursor.fetchall()
        return history

    def create(self, last_mood, reason, changed_at, pets_id, tasks_id=None):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO pet_mood_history 
                (last_mood, reason, changed_at, pets_id, tasks_id) 
                VALUES (%s, %s, %s, %s, %s);
            """, (last_mood, reason, changed_at, pets_id, tasks_id))
            connection.commit()
            return cursor.lastrowid

    def delete_old_records(self, pet_id, keep_last=50):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                DELETE FROM pet_mood_history 
                WHERE pets_id = %s AND id NOT IN (
                    SELECT id FROM (
                        SELECT id FROM pet_mood_history 
                        WHERE pets_id = %s 
                        ORDER BY changed_at DESC 
                        LIMIT %s
                    ) AS temp
                );
            """, (pet_id, pet_id, keep_last))
            connection.commit()