import time
from flask import Flask, request, jsonify
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from werkzeug.utils import secure_filename
from flask_cors import CORS




# ======================================
# FLASK SETUP
# ======================================

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'json'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024
current_combined = None

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

current_combined = None  # STORES ANALYZED DATA


# ======================================
# HELPERS
# ======================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Create visualizations (optional)
def create_spotify_visualizations(combined_df, analysis_results):
    images = {}
    try:
        plt.style.use('default')

        if 'master_metadata_album_artist_name' in combined_df.columns:
            artist_count = combined_df['master_metadata_album_artist_name'].value_counts()
            artist_count_top_5 = artist_count.head()

            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(artist_count_top_5.index, artist_count_top_5.values,
                           color=['#1DB954', '#191414', '#1ED760', '#1AA34A', '#168B3C'])
            plt.xticks(rotation=45)
            ax.set_title("Top 5 Artists")
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            images['top_artists_5'] = base64.b64encode(buf.getvalue()).decode()
            plt.close()

    except Exception as e:
        print("Visualization error:", e)

    return images


def analyze_spotify_data(combined_df):
    analysis = {
        'total_streams': combined_df.shape[0],
        'unique_artists': combined_df['master_metadata_album_artist_name'].nunique() if 'master_metadata_album_artist_name' in combined_df.columns else 0,
        'unique_tracks': combined_df['master_metadata_track_name'].nunique() if 'master_metadata_track_name' in combined_df.columns else 0,
        'unique_albums': combined_df['master_metadata_album_album_name'].nunique() if 'master_metadata_album_album_name' in combined_df.columns else 0,
        'top_artists': {}
    }

    if 'master_metadata_album_artist_name' in combined_df.columns:
        artist_counts = combined_df['master_metadata_album_artist_name'].value_counts()
        analysis['top_artists'] = {
            'top_5': artist_counts.head(5).to_dict(),
            'top_15': artist_counts.head(15).to_dict(),
            'total_unique': len(artist_counts)
        }

    return analysis


# ======================================
# API ENDPOINT — UPLOAD & ANALYZE SPOTIFY FILES
# ======================================

@app.route('/api/analyze-spotify', methods=['POST'])
def analyze_spotify_files():
    global current_combined

    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    uploaded = [f for f in files if f.filename]

    if not uploaded:
        return jsonify({'error': 'No valid files selected'}), 400

    dfs = []
    processed_files = []
    errors = []
    total_songs = 0

    for file in uploaded:
        if allowed_file(file.filename):
            try:
                content = file.read().decode('utf-8')
                json_data = json.loads(content)

                if isinstance(json_data, list):
                    total_songs += len(json_data)
                    df = pd.DataFrame(json_data)
                else:
                    total_songs += 1
                    df = pd.DataFrame([json_data])

                df['source_file'] = file.filename
                dfs.append(df)

                processed_files.append({
                    'filename': file.filename,
                    'records': df.shape[0],
                    'song_count': len(df),
                    'columns': list(df.columns)
                })

                print(f"Processed {file.filename} -> {df.shape[0]} rows")

            except Exception as e:
                errors.append(str(e))
        else:
            errors.append(f"Invalid file type: {file.filename}")

    if not dfs:
        return jsonify({'error': 'No valid JSON data processed', 'errors': errors}), 400

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df['ts'] = pd.to_datetime(combined_df['ts'], errors='coerce')

    print("Total rows:", combined_df.shape[0])

    # Perform analysis
    analysis_results = analyze_spotify_data(combined_df)

    # 🔥 IMPORTANT — SAVE COMBINED DATA FOR OTHER ENDPOINTS
    current_combined = {
        'combined_df': combined_df,
        'analysis_results': analysis_results
    }

    # Minimal track data for filtering
    essential_cols = ['master_metadata_track_name', 'master_metadata_album_artist_name', 'ts']
    tracks_data = combined_df[essential_cols].to_dict('records')

    return jsonify({
        'message': 'Analysis complete',
        'processedFiles': processed_files,
        'combinedData': {
            'totalRecords': len(combined_df),
            'totalSongs': total_songs,
            'tracksData': tracks_data
        },
        'analysis': analysis_results,
        'errors': errors
    })


# ======================================
# TOP TRACKS
# ======================================

@app.route('/api/top-tracks', methods=['POST'])
def get_top_tracks():
    data = request.get_json()

    if not data or 'tracks_data' not in data:
        return jsonify({'error': 'No track data provided'}), 400

    df = pd.DataFrame(data['tracks_data'])

    if 'ts' in df.columns:
        df['ts'] = pd.to_datetime(df['ts'])

    if 'master_metadata_track_name' not in df.columns:
        return jsonify([])

    grouped = df.groupby(
        ['master_metadata_track_name', 'master_metadata_album_artist_name']
    ).size().reset_index(name='count')

    top10 = grouped.sort_values('count', ascending=False).head(10)

    return jsonify([
        {
            'rank': i + 1,
            'title': row['master_metadata_track_name'],
            'artist': row['master_metadata_album_artist_name'],
            'play_count': int(row['count'])
        }
        for i, row in top10.iterrows()
    ])


# ======================================
# TOP ALBUMS — Album Page
# ======================================

@app.route('/api/top-albums', methods=['GET'])
def get_top_albums():
    global current_combined

    if not current_combined:
        return jsonify([])

    df = current_combined['combined_df'].copy()

    start = request.args.get('start', '')
    end = request.args.get('end', '')
    timef = request.args.get('time', 'all')
    season = request.args.get('season', 'all')

    df['ts'] = pd.to_datetime(df['ts'], errors='coerce', utc=True)
    df['ts'] = df['ts'].dt.tz_convert(None)   # removes timezone


    # ----- DATE FILTER -----
    if start:
        df = df[df['ts'] >= pd.to_datetime(start)]
    if end:
        df = df[df['ts'] <= pd.to_datetime(end)]

    # ----- TIME FILTER -----
    hour = df['ts'].dt.hour
    if timef == 'morning':
        df = df[(hour >= 6) & (hour < 12)]
    elif timef == 'afternoon':
        df = df[(hour >= 12) & (hour < 17)]
    elif timef == 'evening':
        df = df[(hour >= 17) & (hour < 21)]
    elif timef == 'night':
        df = df[(hour >= 21) | (hour < 6)]

    # ----- SEASON FILTER -----
    month = df['ts'].dt.month
    if season == 'spring':
        df = df[month.isin([3, 4, 5])]
    elif season == 'summer':
        df = df[month.isin([6, 7, 8])]
    elif season == 'fall':
        df = df[month.isin([9, 10, 11])]
    elif season == 'winter':
        df = df[month.isin([12, 1, 2])]

    # ----- ALBUM AGGREGATION -----
    if 'master_metadata_album_album_name' not in df.columns:
        return jsonify([])

    grouped = df.groupby(
        ['master_metadata_album_album_name', 'master_metadata_album_artist_name']
    ).size().reset_index(name='plays')

    grouped = grouped.sort_values('plays', ascending=False)

    return jsonify([
        {
            'title': row['master_metadata_album_album_name'],
            'artist': row['master_metadata_album_artist_name'],
            'plays': int(row['plays']),
            'cover': ''  # Placeholder
        }
        for _, row in grouped.iterrows()
    ])


# ======================================
# Run Backend (Port 5001)
# ======================================

@app.route('/api/artists/available-artists', methods=['GET'])
def get_available_artists():
    global current_combined
    
    if not current_combined or current_combined['combined_df'] is None:
        return jsonify({'artists': []})
    
    try:
        if 'master_metadata_album_artist_name' in current_combined['combined_df'].columns:
            artist_counts = current_combined['combined_df']['master_metadata_album_artist_name'].value_counts()
            artists = artist_counts.head(50).index.tolist()  # Top 50 artists
        else:
            artists = []
        
        return jsonify({'artists': artists})
    
    except Exception as e:
        return jsonify({'error': f'Error getting artists list: {str(e)}'}), 500

@app.route('/api/visualizations/top-artists', methods=['GET'])
def get_top_artists_visualization():
    """Get the top artists visualization as base64 image"""
    global current_combined
    
    if not current_combined or 'visualizations' not in current_combined:
        return jsonify({'error': 'No visualizations available'}), 400
    
    try:
        # Get specific visualization
        top_5_image = current_combined['visualizations'].get('top_artists_5')
        top_15_image = current_combined['visualizations'].get('top_artists_15')
        
        if not top_5_image and not top_15_image:
            return jsonify({'error': 'Artist visualizations not found'}), 404
        
        return jsonify({
            'top_artists_5': top_5_image,
            'top_artists_15': top_15_image
        })
    
    except Exception as e:
        return jsonify({'error': f'Error getting visualization: {str(e)}'}), 500

@app.route('/api/visualizations/all', methods=['GET'])
def get_all_visualizations():
    """Get all available visualizations"""
    global current_combined
    
    if not current_combined or 'visualizations' not in current_combined:
        return jsonify({'error': 'No visualizations available'}), 400
    
    return jsonify(current_combined['visualizations'])

@app.route('/api/debug', methods=['GET'])
def debug_endpoint():
    global current_combined
    return jsonify({
        'has_data': current_combined is not None,
        'has_combined_df': current_combined and 'combined_df' in current_combined,
        'has_visualizations': current_combined and 'visualizations' in current_combined,
        'data_keys': list(current_combined.keys()) if current_combined else []
    })

@app.route('/api/analysis/status', methods=['GET'])
def get_analysis_status():
    """Check if analysis data is available"""
    global current_combined
    status = {
        'hasAnalysis': current_combined is not None,
        'analysisReady': False,
        'totalRecords': 0,
        'totalArtists': 0,
        'ready': False
    }
    
    if current_combined and 'combined_df' in current_combined:
        df = current_combined['combined_df']
        status.update({
            'analysisReady': True,
            'ready': True,
            'totalRecords': len(df),
            'totalArtists': df['master_metadata_album_artist_name'].nunique() if 'master_metadata_album_artist_name' in df.columns else 0,
            'hasVisualizations': 'visualizations' in current_combined and bool(current_combined['visualizations'])
        })
    
    return jsonify(status)



if __name__ == '__main__':
    app.run(debug=True, port=5001)
