import base64
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional
import csv
import random
import os

class Question(BaseModel):
    question: str
    subject: str
    correct: List[str]
    use: str
    responseA: str
    responseB: str
    responseC: str
    responseD: Optional[str] = None

class RequestQcm(BaseModel):
    use: str
    subject: List[str]
    number: int

class ResponseQcm(BaseModel):
    question: str
    subject: str
    correct: List[str]
    use: str
    responseA: str
    responseB: str
    responseC: str
    responseD: Optional[str] = None

class AdminQuest(BaseModel):
    admin_username: str
    admin_password: str
    question: str
    subject: str
    correct: List[str]
    use: str
    responseA: str
    responseB: str
    responseC: str
    responseD: Optional[str] = None

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "4dm1N"

app = FastAPI()

security = HTTPBasic()
users = {
    "alice": "wonderland",
    "bob": "builder",
    "clementine": "mandarine"
}

# Authentification basique
async def basicAuth(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    if username in users and users[username] == password:
        return username
    raise HTTPException(status_code=401, detail="Unauthorized")


# Charger les questions à partir d'un fichier CSV
async def load_question(filepath: str) -> List[Question]: 
    questions = []
    with open(filepath, 'r') as file:
        data = csv.DictReader(file)
        for row in data:
            questions.append(
                Question(
                    question=row["question"],
                    subject=row["subject"],
                    correct=row["correct"].split(","),  # Assurez-vous que les réponses correctes sont une liste
                    use=row["use"],
                    responseA=row["responseA"],
                    responseB=row["responseB"],
                    responseC=row["responseC"],
                    responseD=row["responseD"],
                )
            )
    return questions


# Endpoint de vérification
@app.get('/verify', description="Vérifie que l'API est fonctionnelle")
async def get_index():
    return {"message": "L'API est fonctionnelle."}


# Endpoint pour générer le quiz
@app.post('/generate_quiz', description="Génère un QCM basé sur les paramètres fournis.")
async def generate_quiz(quiz_quest: RequestQcm, username: str = Depends(basicAuth)):
    if quiz_quest.number not in [5, 10, 20]:
        raise HTTPException(status_code=400, detail="Invalid number of questions requested")
    
    filepath = "questions.csv"  
    data = os.path.join(os.path.dirname(__file__), filepath)
    all_questions = await load_question(data)

    # Filtrer les questions en fonction du type de test (use) et des catégories (subject)
    filtered_questions = [
        q for q in all_questions
        if q.use == quiz_quest.use and any(subject in quiz_quest.subject for subject in q.subject.split(","))
    ]
    
    if len(filtered_questions) < quiz_quest.number:
        raise HTTPException(status_code=400, detail="Not enough questions available for the request.")
    
    # Sélectionner un nombre aléatoire de questions
    selected_questions = random.sample(filtered_questions, quiz_quest.number)
    response = [
        ResponseQcm(
            question=q.question,
            subject=q.subject,
            correct=q.correct,
            use=q.use,
            responseA=q.responseA,
            responseB=q.responseB,
            responseC=q.responseC,
            responseD=q.responseD
        )
        for q in selected_questions
    ]
    return response

@app.post('/create_question', description="Crée une nouvelle question par un utilisateur admin.")
async def create_admin_question(admin_quest: AdminQuest):
    if admin_quest.admin_username != "admin" or admin_quest.admin_password != "4dm1N":
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Charger les questions existantes et ajouter la nouvelle question
    filepath = "questions.csv"
    data = os.path.join(os.path.dirname(__file__), filepath)
    all_questions = await load_question(data)

    # Ajouter la nouvelle question à la liste
    new_question = Question(
        question=admin_quest.question,
        subject=admin_quest.subject,
        correct=admin_quest.correct,
        use=admin_quest.use,
        responseA=admin_quest.responseA,
        responseB=admin_quest.responseB,
        responseC=admin_quest.responseC,
        responseD=admin_quest.responseD
    )
    
    with open(filepath, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            new_question.question,
            new_question.subject,
            ",".join(new_question.correct),
            new_question.use,
            new_question.responseA,
            new_question.responseB,
            new_question.responseC,
            new_question.responseD
        ])

    return {"message": "Question créée avec succès."}
