from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re
import unicodedata

app = Flask(__name__)

# Fonction pour convertir une chaîne en slug compatible avec l'URL
def slugify(value):
    if value:
        value = str(value)
        # Normaliser les caractères spéciaux
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        # Supprimer les caractères non alphanumériques
        value = re.sub('[^\w\s-]', '', value).strip().lower()
        # Remplacer les espaces et tirets par un seul tiret
        value = re.sub('[-\s]+', '-', value)
        return value
    return None

# Fonction pour générer l'URL de la chanson dynamiquement
def find_song_url(artist, title):
    base_url = 'https://tononkira.serasera.org'
    artist_slug = slugify(artist)  # Générer le slug de l'artiste
    title_slug = slugify(title)  # Générer le slug du titre

    if artist_slug and title_slug:
        # Générer l'URL dynamique en fonction de l'artiste et du titre
        song_url = f'{base_url}/hira/{artist_slug}/{title_slug}'
        # Vérifier si l'URL existe
        response = requests.get(song_url)
        if response.status_code == 200:
            return song_url
    return None

# Fonction pour extraire les paroles à partir du HTML
def scrape_lyrics_from_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    # Trouver la division principale contenant les paroles
    main_div = soup.find('div', class_='col-md-8')

    if not main_div:
        return None

    # Trouver la balise <h2> qui contient le titre de la chanson
    h2 = main_div.find('h2')
    if not h2:
        return None

    # Trouver la division avec la classe 'fst-italic' (indicateur de début des paroles)
    fst_italic_div = main_div.find('div', class_='fst-italic')
    if not fst_italic_div:
        return None

    # Rassembler les paroles en parcourant les éléments suivants
    lyrics_content = []
    for sibling in fst_italic_div.next_siblings:
        # Arrêter si on atteint une division qui marque la fin des paroles
        if sibling.name == 'div' and 'mw-100' in sibling.get('class', []):
            break
        if sibling.name == 'br':
            lyrics_content.append('\n')
        elif sibling.string:
            lyrics_content.append(sibling.string.strip())
        else:
            lyrics_content.append(sibling.get_text(separator='\n').strip())

    lyrics = ''.join(lyrics_content).strip()
    return lyrics

# Route pour obtenir les paroles d'une chanson avec un URL dynamique
@app.route('/parole', methods=['GET'])
def get_lyrics():
    artist = request.args.get('artist')
    title = request.args.get('title')

    if not artist or not title:
        return jsonify({'error': 'Veuillez fournir les paramètres "artist" et "title"'}), 400

    try:
        # Construire l'URL de la chanson en fonction de l'artiste et du titre
        song_url = find_song_url(artist, title)
        if not song_url:
            return jsonify({'error': 'Chanson non trouvée'}), 404

        # Récupérer la page HTML de la chanson
        response = requests.get(song_url)
        if response.status_code != 200:
            return jsonify({'error': 'Chanson non trouvée'}), 404

        # Extraire les paroles
        lyrics = scrape_lyrics_from_html(response.text)
        if not lyrics:
            return jsonify({'error': 'Paroles non trouvées'}), 404

        # Retourner les paroles
        return jsonify({'artist': artist, 'title': title, 'lyrics': lyrics})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lancement du serveur Flask sur host 0.0.0.0 et port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
