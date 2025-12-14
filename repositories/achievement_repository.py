class AchievementRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, achievement_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM achievements WHERE id = %s;", (achievement_id,))
            achievement = cursor.fetchone()
        return achievement

    def all(self):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM achievements;")
            achievements = cursor.fetchall()
        return achievements

    def create(self, title, description, experience_num, icon_url):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO achievements 
                (title, description, experience_num, icon_url) 
                VALUES (%s, %s, %s, %s);
            """, (title, description, experience_num, icon_url))
            connection.commit()
            return cursor.lastrowid

    def update(self, achievement_id, title=None, description=None, experience_num=None, icon_url=None):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            updates = []
            params = []
            
            if title is not None:
                updates.append("title = %s")
                params.append(title)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            if experience_num is not None:
                updates.append("experience_num = %s")
                params.append(experience_num)
            if icon_url is not None:
                updates.append("icon_url = %s")
                params.append(icon_url)
            
            if updates:
                params.append(achievement_id)
                query = f"UPDATE achievements SET {', '.join(updates)} WHERE id = %s;"
                cursor.execute(query, params)
                connection.commit()

    def delete(self, achievement_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("DELETE FROM achievements WHERE id = %s;", (achievement_id,))
            connection.commit()

    def get_user_achievements(self, user_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("""
                SELECT a.*, uha.received_at 
                FROM achievements a
                JOIN users_has_achievements uha ON a.id = uha.achievements_id
                WHERE uha.users_id = %s;
            """, (user_id,))
            achievements = cursor.fetchall()
        return achievements

    def add_user_achievement(self, user_id, achievement_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO users_has_achievements 
                (users_id, achievements_id, received_at) 
                VALUES (%s, %s, NOW());
            """, (user_id, achievement_id))
            connection.commit()