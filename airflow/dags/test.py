from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

# Define the DAG and its schedule
with DAG(
    dag_id="example_dag",
    description="A simple example DAG",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",  # runs daily
    catchup=False
) as dag:
    # Task 1: Print current date
    task1 = BashOperator(
        task_id="print_date",
        bash_command="date"
    )
    # Task 2: Echo a message
    task2 = BashOperator(
        task_id="echo_hello",
        bash_command="echo 'Hello, Airflow!'"
    )
    # Define dependency: task1 must run before task2
    task1 >> task2
