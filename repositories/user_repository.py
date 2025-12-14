class UserRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def _get_user_with_role(self, query, params=None):
        with self.db_connector.connect().cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            user = cursor.fetchone()
            if user:
                user['is_admin'] = user.get('role_name') == 'admin'
            return user

    def get_by_id(self, user_id):
        return self._get_user_with_role("""
            SELECT users.*, roles.name AS role_name 
            FROM users 
            LEFT JOIN roles ON users.roles_id = roles.id 
            WHERE users.id = %s;
        """, (user_id,))

    def get_by_username(self, username):
        return self._get_user_with_role("""
            SELECT users.*, roles.name AS role_name 
            FROM users 
            LEFT JOIN roles ON users.roles_id = roles.id 
            WHERE username = %s;
        """, (username,))

    def get_by_email(self, email):
        return self._get_user_with_role("""
            SELECT users.*, roles.name AS role_name 
            FROM users 
            LEFT JOIN roles ON users.roles_id = roles.id 
            WHERE email = %s;
        """, (email,))

    def authenticate(self, username, password):
        user = self._get_user_with_role("""
            SELECT users.*, roles.name AS role_name 
            FROM users 
            LEFT JOIN roles ON users.roles_id = roles.id 
            WHERE username = %s AND password = %s;
        """, (username, password))
        if user:
            user['is_admin'] = user.get('role_name') == 'admin'
        return user

    def all(self):
        with self.db_connector.connect().cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT users.*, roles.name AS role_name 
                FROM users 
                LEFT JOIN roles ON users.roles_id = roles.id;
            """)
            users = cursor.fetchall()
            for user in users:
                user['is_admin'] = user.get('role_name') == 'admin'
            return users

    def create(self, username, email, password, avatar, roles_id, current_points=0):
        connection = self.db_connector.connect()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                INSERT INTO users 
                (username, email, password, avatar, roles_id, сurrent_points) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (username, email, password, avatar, roles_id, current_points))
            connection.commit()
            return cursor.lastrowid

    def update(self, user_id, username=None, email=None, avatar=None, roles_id=None, current_points=None):
        connection = self.db_connector.connect()
        with connection.cursor(dictionary=True) as cursor:
            updates = []
            params = []
            
            if username is not None:
                updates.append("username = %s")
                params.append(username)
            if email is not None:
                updates.append("email = %s")
                params.append(email)
            if avatar is not None:
                updates.append("avatar = %s")
                params.append(avatar)
            if roles_id is not None:
                updates.append("roles_id = %s")
                params.append(roles_id)
            if current_points is not None:
                updates.append("сurrent_points = %s")
                params.append(current_points)
            
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s;"
                cursor.execute(query, params)
                connection.commit()

    def update_password(self, user_id, new_password):
        connection = self.db_connector.connect()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("""
                UPDATE users SET password = %s WHERE id = %s;
            """, (new_password, user_id))
            connection.commit()

    def delete(self, user_id):
        connection = self.db_connector.connect()
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            connection.commit()