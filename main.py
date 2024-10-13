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

# Fonction pour extraire les chansons d'une page spécifique
def scrape_page(page_number):
    url = f'https://tononkira.serasera.org/hira/?page={page_number}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    songs = []
    song_items = soup.find_all('div', class_='border p-2 mb-3')  # Chaque chanson est dans cette div

    for item in song_items:
        # Extraire le titre du lien
        title_tag = item.find('a')
        title = title_tag.text.strip()

        # Extraire le nom de l'artiste
        artist_tag = title_tag.find_next('a')
        artist = artist_tag.text.strip()

        # Extraire le nombre de likes
        likes_tag = item.find('i', class_='bi-heart-fill')
        if likes_tag:
            likes = likes_tag.find_next(string=True).strip()
        else:
            likes = '0'

        songs.append({
            'title': title,
            'artist': artist,
            'likes': likes
        })

    return songs

# Fonction pour rechercher l'URL de la chanson en fonction du prénom d'artiste et du titre
def find_song_url(prenom_artiste, title):
    base_url = 'https://tononkira.serasera.org'
    
    # Récupérer toutes les chansons pour trouver les artistes correspondant au prénom
    page_number = 1
    while True:
        songs = scrape_page(page_number)
        matching_songs = [song for song in songs if prenom_artiste.lower() in song['artist'].lower() and song['title'].lower() == title.lower()]
        
        if matching_songs:
            # Retourner l'URL de la première correspondance trouvée
            artist_slug = slugify(matching_songs[0]['artist'])
            title_slug = slugify(matching_songs[0]['title'])
            song_url = f'{base_url}/hira/{artist_slug}/{title_slug}'
            return song_url
        
        # Si aucune chanson trouvée, passer à la page suivante
        page_number += 1
        if page_number > 10:  # Limiter la recherche à 10 pages pour éviter un temps d'attente trop long
            break
    
    return None

# Fonction pour extraire les paroles à partir du HTML
def scrape_lyrics_from_html(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    # Trouver la division principale contenant les paroles
    main_div = soup.find('div', class_='col-md-8')

    if not main_div:
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

# Route pour obtenir les chansons par page
@app.route('/hira/rehetra', methods=['GET'])
def get_songs():
    page = request.args.get('page', 1, type=int)
    try:
        songs = scrape_page(page)
        return jsonify({'page': page, 'songs': songs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route pour obtenir les paroles d'une chanson avec un prénom d'artiste
@app.route('/parole', methods=['GET'])
def get_lyrics():
    prenom_artiste = request.args.get('artist')
    title = request.args.get('title')

    if not prenom_artiste or not title:
        return jsonify({'error': 'Veuillez fournir les paramètres "artist" et "title"'}), 400

    try:
        # Construire l'URL de la chanson en fonction du prénom d'artiste et du titre
        song_url = find_song_url(prenom_artiste, title)
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
        return jsonify({'artist': prenom_artiste, 'title': title, 'lyrics': lyrics})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Lancement du serveur Flask sur host 0.0.0.0 et port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
