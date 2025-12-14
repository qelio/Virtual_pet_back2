class PetRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, pet_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM pets WHERE id = %s;", (pet_id,))
            pet = cursor.fetchone()
        return pet

    def get_by_user_id(self, user_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM pets WHERE users_id = %s;", (user_id,))
            pets = cursor.fetchall()
        return pets

    def create(self, name, mood, picture_url, created_at, life_status, users_id, experience_dead):
        connection = self.db_connector.connect()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                INSERT INTO pets 
                (name, mood, picture_url, created_at, life_status, users_id, experience_dead) 
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (name, mood, picture_url, created_at, life_status, users_id, experience_dead))
            connection.commit()
            return cursor.lastrowid

    def update(self, pet_id, name=None, mood=None, picture_url=None, life_status=None, experience_dead=None):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = %s")
                params.append(name)
            if mood is not None:
                updates.append("mood = %s")
                params.append(mood)
            if picture_url is not None:
                updates.append("picture_url = %s")
                params.append(picture_url)
            if life_status is not None:
                updates.append("life_status = %s")
                params.append(life_status)
            if experience_dead is not None:
                updates.append("experience_dead = %s")
                params.append(experience_dead)
            
            if updates:
                updates.append("last_update = NOW()")
                params.append(pet_id)
                query = f"UPDATE pets SET {', '.join(updates)} WHERE id = %s;"
                cursor.execute(query, params)
                connection.commit()

    def delete(self, pet_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("DELETE FROM pets WHERE id = %s;", (pet_id,))
            connection.commit()