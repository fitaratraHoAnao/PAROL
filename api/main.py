from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Function to scrape songs from a specific page
def scrape_page(page_number):
    url = f'https://tononkira.serasera.org/hira/?page={page_number}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    songs = []
    song_items = soup.find_all('div', class_='border p-2 mb-3')  # Each song is in this div

    for item in song_items:
        # Extract the title from the link
        title_tag = item.find('a')
        title = title_tag.text.strip()

        # Extract the artist name
        artist_tag = title_tag.find_next('a')
        artist = artist_tag.text.strip()

        # Extract the number of likes (number after the heart icon)
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

# Function to scrape the lyrics page
def scrape_lyrics(song_url):
    response = requests.get(song_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the section that contains the lyrics
    lyrics_div = soup.find('div', class_='fst-italic')  # Adjust this based on your page structure
    if not lyrics_div:
        return None

    # Extract the lyrics
    lyrics = lyrics_div.get_text(separator='\n').strip()
    return lyrics

# Function to search for a song's URL based on the title and artist
def find_song_url(texte):
    base_url = 'https://tononkira.serasera.org'
    search_url = f'{base_url}/tononkira?lohateny={texte.replace(" ", "%20")}'
    
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the link to the song page (adjusted to be more flexible)
    song_link = soup.find('a', href=True, string=lambda s: texte.lower() in s.lower())  # Make the search case-insensitive
    if song_link:
        return base_url + song_link['href']
    return None

# Route to get songs by page
@app.route('/hita/rehetra', methods=['GET'])
def get_songs():
    page = request.args.get('page', 1, type=int)
    try:
        songs = scrape_page(page)
        return jsonify({'page': page, 'songs': songs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to get the lyrics of a song
@app.route('/parole', methods=['GET'])
def get_lyrics():
    texte = request.args.get('texte')  # Text format is 'artist-title'

    if not texte:
        return jsonify({'error': 'Please provide the text parameter'}), 400

    try:
        song_url = find_song_url(texte)
        if not song_url:
            return jsonify({'error': 'Song not found'}), 404

        lyrics = scrape_lyrics(song_url)
        if not lyrics:
            return jsonify({'error': 'Lyrics not found'}), 404

        return jsonify({'texte': texte, 'lyrics': lyrics})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
