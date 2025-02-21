# XAI Tasks Component Library

A SQLite-based task management component library that enables AI agents to track, update and manage their tasks. This library provides components for creating, updating, and managing tasks with features like:

- Task creation with summary, conversation history, details and steps
- Task status tracking (active/inactive, waiting/not waiting)
- Step-by-step progress tracking
- Task deferral and resumption
- Active task listing
- Task completion marking

## Prerequisites

- Python 3.7+
- SQLite3 (comes with Python)
- Xircuits

## Installation

To use this component library, ensure you have Xircuits installed, then run:

```bash
xircuits install https://github.com/xpressai/xai-tasks
```

Alternatively you may manually clone the repository to your Xircuits project directory:

```bash
git clone https://github.com/xpressai/xai-tasks
cd xai-tasks
pip install -r requirements.txt
```

## Components

The library provides these key components:

- **TasksOpenDB**: Opens/creates SQLite database with proper schema
- **TasksCreateTask**: Creates a new task with summary, conversation, details and steps
- **TasksGetTaskDetails**: Retrieves full task details by ID
- **TasksUpdateTask**: Updates an existing task's details
- **TasksListActiveTasks**: Lists all currently active tasks
- **TasksCompleteTask**: Marks a task as complete
- **TasksDeferTask**: Marks a task as waiting
- **TasksResumeTask**: Resumes a waiting task
- **TasksDeleteTask**: Deletes a task by ID
- **TasksCloseDB**: Closes the database connection

## Usage

1. Start by using `TasksOpenDB` to initialize your database connection
2. Create tasks using `TasksCreateTask` with required details
3. Use other components to manage and track task progress
4. Always close your database connection with `TasksCloseDB` when done

See the examples directory for sample workflows demonstrating common use cases.
