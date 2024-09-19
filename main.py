from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

# Fonction pour extraire les données de la chanson
def get_song_data(song_url):
    # Envoyer la requête GET à l'URL
    response = requests.get(song_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Vérifier la présence du titre de la chanson (balise h1 ou autre)
    title_element = soup.find('h1')
    title = title_element.get_text(strip=True) if title_element else 'Title not found'

    # Vérifier la présence de l'artiste (balise h2 ou autre)
    artist_element = soup.find('h2')
    artist = artist_element.get_text(strip=True) if artist_element else 'Artist not found'

    # Chercher les paroles (lyrics) dans un div avec class 'song-text' (adapter si nécessaire)
    lyrics_div = soup.find('div', class_='song-text')
    lyrics = lyrics_div.get_text("\n", strip=True) if lyrics_div else 'Lyrics not found'

    # Retourner les données sous forme de dictionnaire
    return {
        'title': title,
        'artist': artist,
        'lyrics': lyrics
    }

# Route pour rechercher un chanteur et retourner les chansons (exemple basique)
@app.route('/search', methods=['GET'])
def search_songs():
    singer = request.args.get('singer')
    if not singer:
        return jsonify({'error': 'Singer not specified'}), 400
    
    # Exemple d'URL de recherche (adapter si nécessaire)
    search_url = f'https://tononkira.serasera.org/search?q={singer}'
    
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraire les liens vers les chansons (à adapter selon la structure HTML)
    song_links = soup.find_all('a', href=True, text=True)
    songs = []
    for link in song_links:
        songs.append({
            'title': link.get_text(strip=True),
            'url': link['href']
        })
    
    return jsonify({'singer': singer, 'songs': songs})

# Route pour obtenir les détails d'une chanson
@app.route('/song', methods=['GET'])
def get_song():
    song_url = request.args.get('url')
    if not song_url:
        return jsonify({'error': 'Song URL not specified'}), 400
    
    # Appeler la fonction pour extraire les données de la chanson
    song_data = get_song_data(song_url)
    
    return jsonify(song_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
