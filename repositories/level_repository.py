class LevelRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_level_num(self, level_num):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM levels WHERE level_num = %s;", (level_num,))
            level = cursor.fetchone()
        return level

    def get_by_experience(self, experience):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("""
                SELECT * FROM levels 
                WHERE experience_num <= %s 
                ORDER BY experience_num DESC 
                LIMIT 1;
            """, (experience,))
            level = cursor.fetchone()
        return level

    def all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM levels ORDER BY level_num;")
            levels = cursor.fetchall()
        return levels

    def get_next_level(self, current_level_num):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("""
                SELECT * FROM levels 
                WHERE level_num > %s 
                ORDER BY level_num 
                LIMIT 1;
            """, (current_level_num,))
            level = cursor.fetchone()
        return level

    def get_user_level(self, user_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("""
                SELECT l.* FROM levels l
                JOIN users_has_levels uhl ON l.level_num = uhl.levels_level_num
                WHERE uhl.users_id = %s;
            """, (user_id,))
            level = cursor.fetchone()
        return level

    def set_user_level(self, user_id, level_num):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            # First remove any existing level for this user
            cursor.execute("""
                DELETE FROM users_has_levels WHERE users_id = %s;
            """, (user_id,))
            
            # Then add the new level
            cursor.execute("""
                INSERT INTO users_has_levels (users_id, levels_level_num) 
                VALUES (%s, %s);
            """, (user_id, level_num))
            connection.commit()