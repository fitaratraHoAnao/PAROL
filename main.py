from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Fonction pour extraire les données d'une chanson spécifique
def get_song_data(song_url):
    response = requests.get(song_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.find('h1').get_text(strip=True)
    artist = soup.find('h2').get_text(strip=True)
    lyrics_div = soup.find('div', class_='song-text')
    lyrics = lyrics_div.get_text("\n", strip=True) if lyrics_div else 'Lyrics not found'

    return {
        'title': title,
        'artist': artist,
        'lyrics': lyrics
    }

# Fonction pour extraire les informations d'un chanteur
def get_singer_songs(singer):
    url = f'https://tononkira.serasera.org/mpihira/{singer}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extraction des informations principales sur le chanteur
    singer_name = soup.find('h1').get_text(strip=True)
    songs = []
    
    # Supposons que les chansons soient listées dans des <a> avec un lien vers chaque chanson
    song_links = soup.find_all('a', href=True, text=True)
    
    for link in song_links:
        song_title = link.get_text(strip=True)
        song_url = f"https://tononkira.serasera.org{link['href']}"
        songs.append({
            'title': song_title,
            'url': song_url
        })

    return {
        'singer': singer_name,
        'songs': songs
    }

# Route pour chercher un chanteur
@app.route('/search', methods=['GET'])
def search_singer():
    singer = request.args.get('singer')
    if singer:
        # Appel de la fonction pour extraire les chansons du chanteur
        singer_data = get_singer_songs(singer)
        return jsonify(singer_data)
    else:
        return jsonify({'error': 'Please provide a singer name'}), 400

# Route pour chercher une chanson spécifique et récupérer ses paroles
@app.route('/song', methods=['GET'])
def get_song():
    song_url = request.args.get('url')
    if song_url:
        song_data = get_song_data(song_url)
        return jsonify(song_data)
    else:
        return jsonify({'error': 'Please provide a song URL'}), 400

# Exécuter l'application Flask avec host '0.0.0.0'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
