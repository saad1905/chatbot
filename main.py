from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import types
import re
import mysql.connector

# --- Configuration API Gemini ---
API_KEY = "AIzaSyBRP-sEz5zr-6W_NjK7evTrmSywNDGk7uQ"
MODEL_NAME = "gemini-2.0-flash"
client = genai.Client(api_key=API_KEY)

# --- Initialiser FastAPI ---
app = FastAPI(title="Chatbot Support Incidents API")

# --- Définir le format d'entrée ---
class IncidentRequest(BaseModel):
    incident: str

@app.post("/chatbot")
def solve_incident(req: IncidentRequest):
    system_prompt = """Tu es un assistant support informatique.
Quand je t’envoie un ticket décrivant un incident (PC, imprimante, logiciel, etc.),
ta tâche est :

1. Identifier rapidement la cause probable.
2. Sélectionner la catégorie de l’incident parmi la liste suivante :
- Installation logicielle
- Problème avec les outils collaboratifs
- Problème d'impression
- Problème de performance
- Problème de site web ou intranet
- Problème logiciel
- Problème matériel
- Problème messagerie
- Problème réseau
3. Proposer une solution claire et concrète en 3 à 5 étapes maximum.
4. Répondre uniquement avec ce format :

**Cause probable :** [texte court]  

**Catégorie :** [une seule catégorie parmi la liste]  

**Solution :**  
1. ...  
2. ...  
3. ...
"""

    contents = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="user", parts=[types.Part(text=req.incident)]),
    ]

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents
    )

    answer = response.candidates[0].content.parts[0].text

    # --- Extraction via regex ---
    cause = re.search(r"\*\*Cause probable :\*\* (.+)", answer)
    categorie = re.search(r"\*\*Catégorie :\*\* (.+)", answer)
    solution = re.search(r"\*\*Solution :\*\*([\s\S]*)", answer)

    cause_text = cause.group(1).strip() if cause else ""
    categorie_text = categorie.group(1).strip() if categorie else ""
    solution_text = solution.group(1).strip() if solution else ""

    # --- Connexion MySQL ---
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",       # adapte selon ta config
            password="",       # ton mot de passe MySQL
            database="chatbot_db"
        )
        cursor = conn.cursor()

        sql = "INSERT INTO incidents (incident, cause_probable, categorie, solution) VALUES (%s, %s, %s, %s)"
        values = (req.incident, cause_text, categorie_text, solution_text)
        cursor.execute(sql, values)
        conn.commit()


        cursor.close()
        conn.close()
    except Exception as db_error:
        return {"error": f"Erreur lors de l'insertion en DB : {db_error}"}

    return {
        "cause_probable": cause_text,
        "categorie": categorie_text,
        "solution": solution_text
    }
