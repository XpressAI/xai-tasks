import sqlite3
import json
from xai_components.base import InArg, InCompArg, OutArg, Component, xai_component

@xai_component
class TasksOpenDB(Component):
    """Component to open the SQLite database and create the schema if necessary."""
    
    db_file: InCompArg[str]  # Path to the SQLite database file
    connection: OutArg[sqlite3.Connection]  # Output connection to the database

    def execute(self, ctx) -> None:
        conn = sqlite3.connect(self.db_file.value)
        cursor = conn.cursor()
        
        # Create the tasks table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                conversation TEXT,
                details TEXT,
                steps TEXT,
                current_step_num INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_waiting BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        self.connection.value = conn
        ctx['tasksdb_conn'] = conn

@xai_component
class TasksCreateTask(Component):
    """Component to create a new task."""
    
    connection: InArg[sqlite3.Connection]
    summary: InCompArg[str]
    conversation: InCompArg[list]
    details: InCompArg[str]
    steps: InCompArg[list]
    task_id: OutArg[int]  # Output task ID

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (summary, conversation, details, steps)
            VALUES (?, ?, ?, ?)
        ''', (self.summary.value, json.dumps(self.conversation.value), self.details.value, json.dumps(self.steps.value)))
        conn.commit()
        self.task_id.value = cursor.lastrowid

@xai_component
class TasksGetTaskDetails(Component):
    """Component to get details of a task by ID."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]
    task_details: OutArg[dict]  # Output task details all in one for JSON
    summary: OutArg[str]
    conversation: OutArg[list]
    details: OutArg[str]
    steps: OutArg[list]
    current_step_num: OutArg[int]
    is_active: OutArg[bool]
    is_waiting: OutArg[bool]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM tasks WHERE id = ?', (self.task_id.value,))
        row = cursor.fetchone()
        if row:
            self.task_details.value = {
                'id': row[0],
                'summary': row[1],
                'conversation': json.loads(row[2]),
                'details': row[3],
                'steps': json.loads(row[4]),
                'current_step_num': row[5],
                'is_active': row[6],
                'is_waiting': row[7]
            }
            self.summary.value = row[1]
            self.conversation.value = json.loads(row[2])
            self.details.value = row[3]
            self.steps.value = json.loads(row[4])
            self.current_step_num.value = row[5]
            self.is_active.value = row[6]
            self.is_waiting.value = row[7]
        else:
            self.task_details.value = None

@xai_component
class TasksDeleteTask(Component):
    """Component to delete a task by ID."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksUpdateTask(Component):
    """Component to update a task by ID."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]
    summary: InArg[str]
    conversation: InArg[dict]
    details: InArg[str]
    steps: InArg[list]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks
            SET summary = ?, conversation = ?, details = ?, steps = ?
            WHERE id = ?
        ''', (self.summary.value, json.dumps(self.conversation.value), self.details.value, json.dumps(self.steps.value), self.task_id.value))
        conn.commit()

@xai_component
class TasksListActiveTasks(Component):
    """Component to list all active tasks."""
    
    connection: InArg[sqlite3.Connection]
    active_tasks: OutArg[list]  # Output list of active tasks

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE is_active = 1')
        rows = cursor.fetchall()
        self.active_tasks.value = [{
            'id': row[0],
            'summary': row[1],
            'conversation': json.loads(row[2]),
            'details': row[3],
            'steps': json.loads(row[4]),
            'current_step_num': row[5],
            'is_active': row[6],
            'is_waiting': row[7]
        } for row in rows]

@xai_component
class TasksCompleteTask(Component):
    """Component to mark a task as complete."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_active = 0 WHERE id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksDeferTask(Component):
    """Component to defer a task."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_waiting = 1 WHERE id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksResumeTask(Component):
    """Component to defer a task."""
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[int]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_waiting = 0 WHERE id = ?', (self.task_id.value,))
        conn.commit()
        

@xai_component
class TasksCloseDB(Component):
    """Component to close the SQLite database connection."""
    
    connection: InArg[sqlite3.Connection]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        conn.close()
