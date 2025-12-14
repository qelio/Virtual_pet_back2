class ExperienceCounterRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, counter_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM experience_counter WHERE id = %s;", (counter_id,))
            counter = cursor.fetchone()
        return counter

    def get_by_user_id(self, user_id, limit=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM experience_counter WHERE users_id = %s ORDER BY action_date DESC"
            params = [user_id]
            
            if limit is not None:
                query += " LIMIT %s"
                params.append(limit)
            
            cursor.execute(query, params)
            counters = cursor.fetchall()
        return counters

    def create(self, action_date, experience_adding_tasks_id, experience_subtraction_pets_id, 
               users_id, total_points, action_type):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO experience_counter 
                (action_date, experience_adding_tasks_id, experience_subtraction_pets_id, 
                 users_id, total_points, action_type) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (action_date, experience_adding_tasks_id, experience_subtraction_pets_id, 
                 users_id, total_points, action_type))
            connection.commit()
            return cursor.lastrowid

    def get_user_total_points(self, user_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("""
                SELECT SUM(total_points) AS total 
                FROM experience_counter 
                WHERE users_id = %s;
            """, (user_id,))
            result = cursor.fetchone()
        return result.total if result and result.total is not None else 0