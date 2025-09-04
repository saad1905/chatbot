import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import base64
from io import BytesIO
import mysql.connector
import re  # pour extraire les parties avec regex

# --- Fonction conversion image ---
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- Configuration page ---
st.set_page_config(page_title="Support Incidents — Gemini", page_icon="🛠️", layout="centered")

# --- Logo ---
image = Image.open("C:/Users/Lenovoo/Desktop/mtnra-logo.png")
logo_resized = image.resize((200, 200))
st.markdown(
    f"""
    <div style="display: flex; justify-content: center; margin-bottom: 10px;">
        <img src="data:image/png;base64,{image_to_base64(logo_resized)}" style="width: auto;">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("🛠️ Chatbot Support Incidents Machines")

# --- Clé API et modèle ---
API_KEY = "AIzaSyBRP-sEz5zr-6W_NjK7evTrmSywNDGk7uQ"
MODEL_NAME = "gemini-2.0-flash"

# --- Zone de texte ---
incident = st.text_area("Décrivez votre problème ", height=100)

if st.button("Obtenir une solution"):
    if not incident.strip():
        st.warning("Veuillez décrire le problème avant de continuer.")
    else:
        try:
            # Initialiser Gemini
            client = genai.Client(api_key=API_KEY)

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
                types.Content(role="user", parts=[types.Part(text=incident)]),
            ]

            response = client.models.generate_content(model=MODEL_NAME, contents=contents)
            answer = response.candidates[0].content.parts[0].text

            # --- Affichage formaté ---
            st.subheader("💡 Réponse du Chatbot :")
            st.markdown(answer)

            # --- Extraction par regex ---
            cause = re.search(r"\*\*Cause probable :\*\* (.+)", answer)
            categorie = re.search(r"\*\*Catégorie :\*\* (.+)", answer)
            solution = re.search(r"\*\*Solution :\*\*([\s\S]*)", answer)

            cause_text = cause.group(1).strip() if cause else ""
            categorie_text = categorie.group(1).strip() if categorie else ""
            solution_text = solution.group(1).strip() if solution else ""

            # --- Connexion MySQL ---
            conn = mysql.connector.connect(
                host="localhost",
                user="root",       # adapte selon ta config
                password="",       # ton mot de passe MySQL
                database="chatbot_db"
            )
            cursor = conn.cursor()

            # --- Insertion dans DB (avec incident) ---
            sql = "INSERT INTO incidents (incident, cause_probable, categorie, solution) VALUES (%s, %s, %s, %s)"
            values = (incident, cause_text, categorie_text, solution_text)
            cursor.execute(sql, values)
            conn.commit()

            cursor.close()
            conn.close()

            st.success("✅ Réponse et incident sauvegardés dans la base MySQL")

        except Exception as e:
            st.error(f"Erreur : {e}")
