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

def generate_titles_from_pdf(pdf_text, prompt_template, openai_api_key, num_titles):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    chunks = chunk_text(pdf_text)

    combined_titles = []
    for chunk in chunks:
        prompt = prompt_template.format(content=chunk, num_titles=num_titles)
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=2048)
        
        titles = response.choices[0].message.content.split('\n')
        course_titles = [title.strip('- ') for title in titles if title]
        combined_titles.extend(course_titles)

    return combined_titles[:num_titles]

def generate_chapter_summary(chapter_title, pdf_text, openai_api_key):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    chunks = chunk_text(pdf_text)

    combined_summary = ""
    for chunk in chunks:
        prompt = (
            f"Tu es un formateur expert. Résume les informations importantes du contenu suivant pour le chapitre intitulé '{chapter_title}':\n\n"
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

def generate_episode_script(chapter_title, episode_type, chapter_summary, previous_scripts, openai_api_key):
    OPENAI_API_KEY = openai_api_key
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = (
        f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
        f"Sur la base du contenu suivant {chapter_summary}\n\n  "
        "FIN DU CONTENU \n\n "
        f"Créer moi le dialogue d'un script pour un épisode {episode_type} pour le chapitre intitulé '{chapter_title}'. "
        "L'épisode doit commencer par une introduction pour expliquer ce qui sera dit dans cet épisode et une conclusion pour faire un rappel de ce qui a été dit dans l'épisode."
        "L'introduction et la conclusion doivent être des lignes en plus du script."
        f"Assure-toi que le script soit original, bien structuré et apporte de nouvelles informations par rapport aux scripts précédents du chapitre s'il y en a."
        "Tu dois me sortir le script juste avec le texte du narrateur et rien d'autre. Le narrateur s'appelle Hugo."
        "Tu dois m'écrire obligatoirement chaque ligne du script."
        "Tu ne dois surtout pas inventer du contenu, il faut que tu récupères seulement le contenu ci-dessus."
    )

    if previous_scripts:
        prompt += "\n\nScripts précédemment générés pour ce chapitre :\n"
        for previous_script in previous_scripts:
            prompt += previous_script + "\n\n"

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=2048)

    script = response.choices[0].message.content
    previous_scripts.append(script)

    return script

def generate_module_structure(module_title, pdf_text, openai_api_key, existing_titles):
    chapters_prompt_template = (
        f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
        f"Sur la base du contenu suivant : {{content}}, "
        "FIN DU CONTENU"
        f"Tu dois me trouver 3 titres de chapitre pour le module '{module_title}' pour comprendre le contenu. "
        "Tu dois me donner uniquement les titres des chapitres et rien d'autre. Il faut que cela soit des titres cohérents et qui permet de comprendre le sujet rapidement"
    )
    
    episodes_prompt_template = (
        f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
        f"Sur la base du contenu suivant : {{content}}, "
        "FIN DU CONTENU"
        f"Tu dois me trouver 3 titres d'épisode pour le chapitre '{module_title}' pour comprendre le contenu. "
        "Tu dois me donner uniquement les titres des épisodes et rien d'autre. Il faut que cela soit des titres cohérents et qui permet de comprendre le sujet rapidement"
    )
    
    chapters = generate_titles_from_pdf(pdf_text, chapters_prompt_template, openai_api_key, 3)
    episode_types = ["Apprentissage", "Études de cas", "Scénario"]

    module_structure = []
    for chapter_title in chapters:
        episodes = generate_titles_from_pdf(pdf_text, episodes_prompt_template, openai_api_key, 3)
        chapter_summary = generate_chapter_summary(chapter_title, pdf_text, openai_api_key)
        episode_structures = []
        for idx, episode_title in enumerate(episodes):
            episode_type = episode_types[idx % len(episode_types)]
            previous_scripts = existing_titles.get(episode_title, [])
            script = generate_episode_script(chapter_title, episode_type, chapter_summary, previous_scripts, openai_api_key)
            episode_structures.append({"title": episode_title, "type": episode_type, "scripts": previous_scripts})
            existing_titles[episode_title] = previous_scripts
        module_structure.append({"title": chapter_title, "episodes": episode_structures})
    
    return module_structure

def save_scripts_to_file(scripts, filename="scripts.txt"):
    with open(filename, "w") as file:
        for module, chapters in scripts.items():
            file.write(f"### Module: {module}\n")
            for chapter in chapters:
                file.write(f"#### Chapitre: {chapter['title']}\n")
                for episode in chapter['episodes']:
                    for idx, script in enumerate(episode['scripts']):
                        file.write(f"Script pour '{episode['title']}' ({episode['type']}) - Version {idx+1}\n")
                        file.write(script + "\n\n")

st.title("Générateur de modules et chapitres à partir d'un PDF")

uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")

if uploaded_file is not None:
    pdf_file_path = "temp_uploaded_file.pdf"
    with open(pdf_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    pdf_text = extract_text_from_pdf_using_pypdf2(pdf_file_path)
    openai_api_key = st.text_input("Entrez votre clé API OpenAI", type="password")
    num_titles = st.number_input("Nombre de titres de module à générer", min_value=1, max_value=20, value=5, step=1)

    if st.button("Générer les titres de module"):
        prompt_template = (
            f"A partir de maintenant agis en tant que formateur confirmé de formation tu es capable de créer des formations avec un ton enthousiaste et inspirant."
            f"Sur la base du contenu suivant : {{content}}, "
            "FIN DU CONTENU"
            f"Tu dois me trouver {num_titles} titres de module pour une formation pour comprendre le contenu. "
            "Tu dois me donner uniquement les titres des modules et rien d'autre. Il faut que cela soit des titres cohérents et qui permet de comprendre le sujet rapidement"
        )
        titles = generate_titles_from_pdf(pdf_text, prompt_template, openai_api_key, num_titles)
        st.session_state['titles'] = titles
        st.session_state['current_module_index'] = 0
        st.session_state['scripts'] = {title: [] for title in titles}
        st.session_state['existing_titles'] = {}

if 'titles' in st.session_state:
    titles = st.session_state['titles']
    module_index = st.session_state.get('current_module_index', 0)
    scripts = st.session_state.get('scripts', {})
    existing_titles = st.session_state.get('existing_titles', {})

    if module_index < len(titles):
        current_module = titles[module_index]
        st.subheader(f"Module actuel : {current_module}")

        if f'module_{current_module}' not in st.session_state:
            if st.button(f"Générer le contenu du module '{current_module}'"):
                chapters = generate_module_structure(current_module, pdf_text, openai_api_key, existing_titles)
                st.session_state[f'module_{current_module}'] = chapters
                scripts[current_module] = chapters
                st.session_state['scripts'] = scripts
                st.session_state['current_module_index'] += 1  # Passer automatiquement au module suivant
        else:
            st.button("Passer au module suivant", key=f"next_module_{current_module}", on_click=lambda: st.session_state.update({'current_module_index': st.session_state['current_module_index'] + 1}))

        if f'module_{current_module}' in st.session_state:
            chapters = st.session_state[f'module_{current_module}']
            st.subheader(f"Chapitres pour le module '{current_module}'")
            for chapter_index, chapter in enumerate(chapters):
                st.text_area(f"Chapitre: {chapter['title']}", value='\n'.join([episode['title'] for episode in chapter['episodes']]), height=150, key=f"chapter_{current_module}_{chapter_index}")

    # Display previously generated scripts
    st.subheader("Scripts précédemment générés")
    for module, chapters in scripts.items():
        st.markdown(f"### Module: {module}")
        for chapter_index, chapter in enumerate(chapters):
            st.markdown(f"#### Chapitre: {chapter['title']}")
            for episode_index, episode in enumerate(chapter['episodes']):
                st.text_area(f"Script pour '{episode['title']}'", '\n'.join(existing_titles.get(episode['title'], [])), height=200, key=f"script_{module}_{chapter_index}_{episode_index}")

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
