import sqlite3
import json
from xai_components.base import InArg, InCompArg, OutArg, Component, xai_component

@xai_component
class TasksOpenDB(Component):
    """Opens or creates a SQLite database with the proper schema for task management.
    
    ##### inPorts:
    - db_file: Path to the SQLite database file
    
    ##### outPorts:
    - connection: SQLite database connection object
    """
    
    db_file: InCompArg[str]  # Path to the SQLite database file
    connection: OutArg[sqlite3.Connection]  # Output connection to the database

    def execute(self, ctx) -> None:
        conn = sqlite3.connect(self.db_file.value)
        cursor = conn.cursor()
        
        # Create the tasks table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
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
    """Creates a new task in the database with the specified details.
    
    ##### inPorts:
    - connection: SQLite database connection
    - summary: Brief description of the task
    - conversation: List of conversation history related to the task
    - details: Detailed description of the task
    - steps: List of steps to complete the task
    
    ##### outPorts:
    - task_id: ID of the newly created task
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]
    summary: InCompArg[str]
    conversation: InCompArg[list]
    details: InCompArg[str]
    steps: InCompArg[list]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (task_id, summary, conversation, details, steps)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.task_id.value, self.summary.value, json.dumps(self.conversation.value), self.details.value, json.dumps(self.steps.value)))
        conn.commit()

@xai_component
class TasksGetTaskDetails(Component):
    """Retrieves all details of a specific task by its ID.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to retrieve
    
    ##### outPorts:
    - task_details: Complete task information as a dictionary
    - summary: Brief description of the task
    - conversation: List of conversation history
    - details: Detailed description
    - steps: List of task steps
    - current_step_num: Current step number
    - is_active: Whether the task is active
    - is_waiting: Whether the task is waiting
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]
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

        cursor.execute('SELECT task_id, summary, conversation, details, steps, current_step_num, is_active, is_waiting FROM tasks WHERE task_id = ?', (self.task_id.value,))
        row = cursor.fetchone()
        if row:
            self.task_details.value = {
                'task_id': row[0],
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
            self.summary.value = None
            self.conversation.value = None
            self.details.value = None
            self.steps.value = None
            self.current_step_num.value = None
            self.is_active.value = None
            self.is_waiting.value = None

@xai_component
class TasksDeleteTask(Component):
    """Deletes a task from the database.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to delete
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE task_id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksUpdateTask(Component):
    """Updates an existing task's details.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to update
    - summary: New summary text
    - conversation: Updated conversation history
    - details: New detailed description
    - steps: Updated list of steps
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]
    summary: InArg[str]
    conversation: InArg[dict]
    details: InArg[str]
    steps: InArg[list]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()

        cursor.execute('SELECT task_id, summary, conversation, details, steps FROM tasks WHERE task_id = ?', (self.task_id.value,))
        row = cursor.fetchone()
        if row:
            summary = self.summary.value if self.summary.value is not None else row[1]
            conversation = self.conversation.value if self.conversation.value is not None else json.loads(row[2])
            details = self.details.value if self.details.value is not None else row[3]
            steps = self.steps.value if self.steps.value is not None else json.loads(row[4])
            
            cursor.execute('''
                UPDATE tasks
                SET summary = ?, conversation = ?, details = ?, steps = ?
                WHERE task_id = ?
            ''', (summary, json.dumps(conversation), details, json.dumps(steps), self.task_id.value))
        conn.commit()

@xai_component
class TasksListActiveTasks(Component):
    """Retrieves a list of all active tasks from the database.
    
    ##### inPorts:
    - connection: SQLite database connection
    
    ##### outPorts:
    - active_tasks: List of dictionaries containing active task details
    """
    
    connection: InArg[sqlite3.Connection]
    active_tasks: OutArg[list]  # Output list of active tasks

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('SELECT task_id, summary, conversation, details, steps, current_step_num, is_active, is_waiting FROM tasks WHERE is_active = 1')
        rows = cursor.fetchall()
        self.active_tasks.value = [{
            'task_id': row[0],
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
    """Marks a task as completed by setting is_active to false.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to complete
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_active = 0 WHERE task_id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksDeferTask(Component):
    """Marks a task as waiting.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to defer
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_waiting = 1 WHERE task_id = ?', (self.task_id.value,))
        conn.commit()

@xai_component
class TasksResumeTask(Component):
    """Resumes a waiting task by setting is_waiting to false.
    
    ##### inPorts:
    - connection: SQLite database connection
    - task_id: ID of the task to resume
    """
    
    connection: InArg[sqlite3.Connection]
    task_id: InCompArg[str]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET is_waiting = 0 WHERE task_id = ?', (self.task_id.value,))
        conn.commit()
        

@xai_component
class TasksCloseDB(Component):
    """Closes the SQLite database connection.
    
    ##### inPorts:
    - connection: SQLite database connection to close
    """
    
    connection: InArg[sqlite3.Connection]

    def execute(self, ctx) -> None:
        conn = self.connection.value if self.connection.value is not None else ctx['tasksdb_conn']
        conn.close()
