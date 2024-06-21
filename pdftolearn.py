import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import os

# Définissez votre clé API OpenAI ici
OPENAI_API_KEY = ""

def extract_text_from_pdf_using_pypdf2(pdf_file_path):
    reader = PdfReader(pdf_file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def chunk_text(text, max_tokens=1000):
    # Divise le texte en chunks de taille max_tokens (environ)
    chunks = []
    current_chunk = ""
    current_length = 0

    for line in text.split('\n'):
        line_length = len(line.split())
        if current_length + line_length > max_tokens:
            chunks.append(current_chunk)
            current_chunk = line
            current_length = line_length
        else:
            current_chunk += " " + line
            current_length += line_length

    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def generate_course_titles_from_pdf(pdf_text, openai_api_key, num_titles):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    chunks = chunk_text(pdf_text)

    combined_titles = []
    for chunk in chunks:
        prompt = (
            f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
            f"Sur la base du contenu suivant : {chunk}, "
            "FIN DU CONTENU"
            f"Tu dois me trouver {num_titles} titres de module pour une formation pour comprendre le contenu. "
            "Tu dois me donner uniquement les titres des modules et rien d'autre. Il faut que cela soit des titres cohérents et qui permet de comprendre le sujet rapidement"
        )

        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=2048)
        
        titles = response.choices[0].message.content.split('\n')
        course_titles = [title.strip('- ') for title in titles if title]
        combined_titles.extend(course_titles)

    # Limiter le nombre de titres à num_titles
    return combined_titles[:num_titles]

def generate_chapters_for_module(module_title, num_chapters, pdf_text, openai_api_key):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    chunks = chunk_text(pdf_text)

    combined_chapters = []
    for chunk in chunks:
        prompt = (
            f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
            f"Sur la base du contenu suivant {chunk}, "
            f"Tu dois me trouver {num_chapters} titres de module pour une formation pour comprendre le contenu. '{module_title}'. "
            "Tu dois me donner uniquement les titres des Episodes et rien d'autre. Il faut que cela soit des titres cohérents et qui permet de comprendre le sujet rapidement"
        )

        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=2048)

        chapters = response.choices[0].message.content.split('\n')
        chapter_titles = [chapter.strip('- ') for chapter in chapters if chapter]
        combined_chapters.extend(chapter_titles)

    # Limiter le nombre de Episodes à num_chapters
    return combined_chapters[:num_chapters]

def generate_chapter_summary(chapter_title, pdf_text, openai_api_key):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    chunks = chunk_text(pdf_text)

    combined_summary = ""
    for chunk in chunks:
        prompt = (
            f"Tu es un formateur expert. Résume les informations importantes du contenu suivant pour le Episode intitulé '{chapter_title}':\n\n"
            f"{chunk}\n\n"
            "FIN DU CONTENU\n\n"
            "Le résumé doit être concis, structuré et contenir les points clés uniquement."
        )

        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=1024)

        summary = response.choices[0].message.content.strip()
        combined_summary += summary + "\n"

    return combined_summary.strip()

def generate_three_episode_scripts(chapter_title, episode_type, chapter_summary, openai_api_key):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)

    scripts = []
    for i in range(3):
        prompt = (
            f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
            f"Sur la base du contenu suivant {chapter_summary}\n\n  "
            "FIN DU CONTENU \n\n "
            f"Créer moi le dialogue d'un script pour un épisode {episode_type} pour le Episode intitulé '{chapter_title}'. "
            "L'épisode doit commencer par une introduction pour expliquer ce qui sera dit dans cet épisode et une conclusion pour faire un rappel de ce qui a été dit dans l'épisode."
            "L'introduction et la conclusion doivent être des lignes en plus du script."
            f"Assure-toi que le script soit original, bien structuré et apporte de nouvelles informations par rapport aux scripts précédents du Episode s'il y en a."
            "Tu dois me sortir le script juste avec le texte du narrateur et rien d'autre. Le narrateur s'appelle Hugo."
            "Tu dois m'écrire obligatoirement chaque ligne du script."
            "Tu ne dois surtout pas inventer du contenu, il faut que tu récupères seulement le contenu ci-dessus."
            "Le script doit faire 2000 mots."
        )

        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=2048)

        script = response.choices[0].message.content
        scripts.append(script)
    
    return scripts

def save_scripts_to_file(scripts, filename="scripts.txt"):
    with open(filename, "w") as file:
        for module, chapters in scripts.items():
            file.write(f"### Module: {module}\n")
            for chapter, script_types in chapters.items():
                file.write(f"#### Episode: {chapter}\n")
                for episode_type, scripts_list in script_types.items():
                    for idx, script in enumerate(scripts_list):
                        file.write(f"Script pour '{chapter}' ({episode_type}) - Version {idx+1}\n")
                        file.write(script + "\n\n")

st.title("Générateur de modules et Episodes à partir d'un PDF")

uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")

if uploaded_file is not None:
    pdf_file_path = "temp_uploaded_file.pdf"
    with open(pdf_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdf_text = extract_text_from_pdf_using_pypdf2(pdf_file_path)
    openai_api_key = st.text_input("Entrez votre clé API OpenAI", type="password")
    num_titles = st.number_input("Nombre de titres de module à générer", min_value=1, max_value=20, value=5, step=1)

    if st.button("Générer les titres de module"):
        titles = generate_course_titles_from_pdf(pdf_text, openai_api_key, num_titles)
        st.session_state['titles'] = titles
        st.session_state['module_chapter_counts'] = {title: 5 for title in titles}
        st.session_state['scripts'] = {title: {} for title in titles}  # Initialize script storage

if 'titles' in st.session_state:
    titles = st.session_state['titles']
    module_chapter_counts = st.session_state.get('module_chapter_counts', {})
    scripts = st.session_state.get('scripts', {})

    for i, title in enumerate(titles, start=1):
        modified_title = st.text_input(f"Titre {i}", value=title, key=f"title_{i}")
        num_chapters = st.number_input(f"Nombre de Episodes pour '{modified_title}'", min_value=1, max_value=20, value=module_chapter_counts.get(title, 5), step=1, key=f"chapters_{i}")
        module_chapter_counts[modified_title] = num_chapters

        generate_button = st.button(f"Générer les Episodes pour '{modified_title}'", key=f"generate_{title}")

        if generate_button:
            chapter_titles = generate_chapters_for_module(modified_title, num_chapters, pdf_text, openai_api_key)
            st.session_state[f'chapters_{modified_title}'] = chapter_titles

        if f'chapters_{modified_title}' in st.session_state:
            chapter_titles = st.session_state[f'chapters_{modified_title}']
            st.subheader(f"Episodes pour le module '{modified_title}'")
            for j, chapter in enumerate(chapter_titles, start=1):
                modified_chapter = st.text_input(f"Episode {j} pour '{modified_title}'", value=chapter, key=f"chapter_{title}_{j}")

                script_key = f"script_{modified_title}_{modified_chapter}"
                if script_key in scripts[modified_title]:
                    script_texts = scripts[modified_title][script_key]
                else:
                    script_texts = {"Apprentissage": [], "Études de cas": [], "Scénario": []}

                episode_type = st.selectbox(f"Type d'épisode pour '{modified_chapter}'", ["Apprentissage", "Études de cas", "Scénario"], key=f"type_{title}_{j}")

                if st.button(f"Générer les scripts pour '{modified_chapter}'", key=f"generate_all_scripts_{title}_{j}"):
                    summary = generate_chapter_summary(modified_chapter, pdf_text, openai_api_key)
                    all_scripts = generate_three_episode_scripts(modified_chapter, episode_type, summary, openai_api_key)
                    script_texts[episode_type] = all_scripts
                    scripts[modified_title][script_key] = script_texts
                    st.session_state['scripts'] = scripts  # Update session state with new scripts
                    script_texts = scripts[modified_title][script_key]  # Update the displayed script texts

                for ep_type in ["Apprentissage", "Études de cas", "Scénario"]:
                    for idx, script in enumerate(script_texts[ep_type]):
                        st.text_area(f"Script pour '{modified_chapter}' ({ep_type}) - Version {idx+1}", script, height=300)

    st.session_state['module_chapter_counts'] = module_chapter_counts

    # Display previously generated scripts
    st.subheader("Scripts précédemment générés")
    for module, chapters in scripts.items():
        st.markdown(f"### Module: {module}")
        for chapter, script_types in chapters.items():
            st.markdown(f"#### Episode: {chapter}")
            for episode_type, scripts_list in script_types.items():
                for idx, script in enumerate(scripts_list):
                    st.text_area(f"Script pour '{chapter}' ({episode_type}) - Version {idx+1}", script, height=200)

    # Save and provide download link for all scripts
    if st.button("Télécharger tous les scripts"):
        save_scripts_to_file(scripts)
        with open("scripts.txt", "rb") as file:
            btn = st.download_button(
                label="Télécharger le fichier des scripts",
                data=file,
                file_name="scripts.txt",
                mime="text/plain"
            )

if 'pdf_file_path' in locals() and os.path.exists(pdf_file_path):
    os.remove(pdf_file_path)
