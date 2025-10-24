from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os

app = FastAPI(
    title="Habit Tracker API",
    description="API для трекера привычек",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_index():
    return FileResponse("index.html")

@app.get("/style.css")
async def get_css():
    return FileResponse("style.css", media_type="text/css")

@app.get("/script.js")
async def get_js():
    return FileResponse("script.js", media_type="application/javascript")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

class HabitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    habit_type: str = "bad"
    frequency: str = "daily"
    target_count: int = 1
    motivation_text: Optional[str] = None
    difficulty_level: str = "medium"

class HabitCompletion(BaseModel):
    habit_id: int
    completion_date: str
    completed: bool = True
    notes: Optional[str] = None
    craving_level: int = 0
    resistance_level: int = 0

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database="priv",
            user="root",
            password="123456789",
            port=3306
        )
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

@app.post("/habits/")
async def create_habit(habit: HabitCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO habits (name, description, habit_type, frequency, target_count, motivation_text, difficulty_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (habit.name, habit.description, habit.habit_type, habit.frequency,
              habit.target_count, habit.motivation_text, habit.difficulty_level))

        habit_id = cursor.lastrowid
        conn.commit()
        return {"id": habit_id, "message": "Habit created successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating habit: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/habits/")
async def get_habits():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT id, name, description, habit_type, frequency, target_count, 
                   motivation_text, difficulty_level,
                   DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
            FROM habits 
            ORDER BY created_at DESC
        ''')
        habits = cursor.fetchall()
        return habits
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching habits: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.post("/habits/complete/")
async def complete_habit(completion: HabitCompletion):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO habit_completions (habit_id, completion_date, completed, notes, craving_level, resistance_level)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            completed = VALUES(completed), 
            notes = VALUES(notes),
            craving_level = VALUES(craving_level),
            resistance_level = VALUES(resistance_level)
        ''', (completion.habit_id, completion.completion_date, completion.completed,
              completion.notes, completion.craving_level, completion.resistance_level))

        conn.commit()
        return {"message": "Habit completion recorded"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error recording completion: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/analytics/")
async def get_analytics():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT h.id, h.name, COUNT(hc.id) as completed_count
            FROM habits h
            LEFT JOIN habit_completions hc ON h.id = hc.habit_id 
            AND hc.completion_date >= %s AND hc.completed = TRUE
            GROUP BY h.id, h.name
        ''', (thirty_days_ago,))

        stats = cursor.fetchall()

        cursor.execute('''
            SELECT 
                COUNT(*) as total_habits,
                SUM(CASE WHEN frequency = 'daily' THEN 1 ELSE 0 END) as daily_habits,
                SUM(CASE WHEN frequency = 'weekly' THEN 1 ELSE 0 END) as weekly_habits,
                SUM(CASE WHEN frequency = 'monthly' THEN 1 ELSE 0 END) as monthly_habits
            FROM habits
        ''')

        total_stats = cursor.fetchone()

        analytics = {
            "habit_stats": [
                {
                    "habit_id": row["id"],
                    "habit_name": row["name"],
                    "completed_count": row["completed_count"],
                    "completion_rate": round((row["completed_count"] / 30) * 100, 1) if row["completed_count"] else 0
                }
                for row in stats
            ],
            "total_stats": total_stats
        }

        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/habits/{habit_id}/completions/")
async def get_habit_completions(habit_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute('''
            SELECT id, habit_id, completion_date, completed, notes, craving_level, resistance_level,
                   DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
            FROM habit_completions 
            WHERE habit_id = %s 
            ORDER BY completion_date DESC
            LIMIT 10
        ''', (habit_id,))
        completions = cursor.fetchall()
        return completions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching completions: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/habits/{habit_id}")
async def delete_habit(habit_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM habits WHERE id = %s', (habit_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Habit not found")

        return {"message": "Habit deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting habit: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    print("Сервер запущен! Веб-клиент: http://localhost:8000")
    print("Убедитесь, что все файлы находятся в одной папке:")
    print("- server.py")
    print("- index.html") 
    print("- style.css")
    print("- script.js")
    uvicorn.run(app, host="0.0.0.0", port=8000)