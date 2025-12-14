class TaskRepository:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    def get_by_id(self, task_id):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute("SELECT * FROM tasks WHERE id = %s;", (task_id,))
            task = cursor.fetchone()
        return task

    def get_by_user_id(self, user_id, completed=None):
        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            query = "SELECT * FROM tasks WHERE users_id = %s"
            params = [user_id]
            
            if completed is not None:
                query += " AND is_completed = %s"
                params.append(completed)
            
            cursor.execute(query, params)
            tasks = cursor.fetchall()
        return tasks

    def create(self, title, description, is_completed, created_at, experience_num, users_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("""
                INSERT INTO tasks 
                (title, description, is_completed, created_at, experience_num, users_id) 
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (title, description, is_completed, created_at, experience_num, users_id))
            connection.commit()
            return cursor.lastrowid

    def update(self, task_id, title=None, description=None, is_completed=None, experience_num=None):
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
            if is_completed is not None:
                updates.append("is_completed = %s")
                params.append(is_completed)
                if is_completed:
                    updates.append("completed_at = NOW()")
            if experience_num is not None:
                updates.append("experience_num = %s")
                params.append(experience_num)
            
            if updates:
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s;"
                cursor.execute(query, params)
                connection.commit()

    def delete(self, task_id):
        connection = self.db_connector.connect()
        with connection.cursor(named_tuple=True) as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            connection.commit()

    def get_paginated_tasks(self, user_id, page=1, per_page=10, sort_by='created_at',
                            sort_order='desc', completed=None):
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        if sort_by not in ['created_at', 'experience_num']:
            sort_by = 'created_at'
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'

        offset = (page - 1) * per_page

        query = "SELECT * FROM tasks WHERE users_id = %s"
        params = [user_id]

        if completed is not None:
            query += " AND is_completed = %s"
            params.append(completed)

        query += f" ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        with self.db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, params)
            tasks = cursor.fetchall()

        count_query = "SELECT COUNT(*) FROM tasks WHERE users_id = %s"
        count_params = [user_id]

        if completed is not None:
            count_query += " AND is_completed = %s"
            count_params.append(completed)

        with self.db_connector.connect().cursor() as cursor:
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

        return {
            'tasks': tasks,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'completed_filter': completed
        }