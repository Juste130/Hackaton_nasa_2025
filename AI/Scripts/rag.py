# ============================================
# 🚀 AGENT CONVERSATIONNEL SCIENTIFIQUE NASA
# ============================================

# ---- Imports principaux ----
import os
import pandas as pd
from dotenv import load_dotenv

# LangChain & Google Gemini
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)
from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import BeautifulSoupTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# ---------------------------------------------
# 1️⃣ Charger la clé API Google depuis le fichier .env
# ---------------------------------------------
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("❌ Clé API Google Gemini manquante dans le fichier .env !")
else:
    print("🔐 Clé Google Gemini détectée.")

# ---------------------------------------------
# 2️⃣ Charger les liens d’articles depuis le CSV
# ---------------------------------------------

import os

# Construire le chemin relatif
csv_path = os.path.join("..", "..", "datas", "SB_publication_PMC.csv") 
df = pd.read_csv(csv_path)
links = df["Link"].tolist()
print(f"🔗 Nombre total d'articles à charger : {len(links)}")

# ---------------------------------------------
# 3️⃣ Charger les pages web en parallèle (AsyncHtmlLoader)
# ---------------------------------------------
print("📡 Téléchargement asynchrone des pages PMC en cours...")
loader = AsyncHtmlLoader(links)
docs = loader.load()
print(f"📥 Pages chargées : {len(docs)}")

# ---------------------------------------------
# 4️⃣ Nettoyer le contenu HTML (BeautifulSoupTransformer)
# ---------------------------------------------
print("🧹 Nettoyage du contenu HTML...")
bs_transformer = BeautifulSoupTransformer()
clean_docs = bs_transformer.transform_documents(docs, tags_to_extract=["p", "h1", "h2", "h3"])

# Ajouter la source (lien) dans les métadonnées
for i, d in enumerate(clean_docs):
    d.metadata["source"] = links[i] if i < len(links) else None

print(f"🧾 Documents nettoyés : {len(clean_docs)}")

# ---------------------------------------------
# 5️⃣ Découper les textes en chunks (pour le RAG)
# ---------------------------------------------
print("✂️ Découpage des textes en chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(clean_docs)
print(f"📚 Nombre de chunks créés : {len(chunks)}")

# ---------------------------------------------
# 6️⃣ Créer les embeddings Gemini
# ---------------------------------------------
print("🤖 Génération des embeddings avec Gemini...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# ---------------------------------------------
# 7️⃣ Créer et sauvegarder l’index FAISS
# ---------------------------------------------
print("💾 Création de l’index FAISS...")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("faiss_index_nasa_gemini")
print("✅ Index vectoriel sauvegardé sous : faiss_index_nasa_gemini")

# ---------------------------------------------
# 8️⃣ Charger l’index et créer le retriever
# ---------------------------------------------
print("📂 Chargement de l’index FAISS...")
db = FAISS.load_local("faiss_index_nasa_gemini", embeddings, allow_dangerous_deserialization=True)
retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})

# ---------------------------------------------
# 9️⃣ Initialiser le modèle de conversation Gemini
# ---------------------------------------------
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True
)

# ---------------------------------------------
# 🔟 Exemple de conversation scientifique
# ---------------------------------------------
print("\n🧪 Assistant scientifique NASA prêt !")
print("Posez une question (ex : 'Quels sont les effets de la microgravité sur l’ADN ?')\n")

while True:
    query = input("❓ Votre question : ")
    if query.lower() in ["quit", "exit", "q"]:
        print("👋 Fin de la session.")
        break

    result = qa_chain({"question": query})
    print("\n💬 Réponse :")
    print(result["answer"])
    
    print("\n📚 Sources :")
    for doc in result["source_documents"]:
        print("-", doc.metadata.get("source"))
    print("\n" + "="*60 + "\n")
