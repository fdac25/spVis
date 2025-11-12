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


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'json'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_spotify_visualizations(combined_df, analysis_results):
    images = {}
    
    try:
        plt.style.use('default')
        
        # 1. Top Artists (Top 5 and Top 15)
        if 'master_metadata_album_artist_name' in combined_df.columns:
            artist_count = combined_df['master_metadata_album_artist_name'].value_counts()
            artist_count_top_5 = artist_count.head()
            artist_count_top_15 = artist_count.head(15)
            
            # Top 5 Artists
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(artist_count_top_5.index, artist_count_top_5.values, 
                         color=['#1DB954', '#191414', '#1ED760', '#1AA34A', '#168B3C'])
            ax.set_xlabel('Artist')
            ax.set_ylabel('Stream Count')
            ax.set_title('Top 5 Most Streamed Artists')
            plt.xticks(rotation=45)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            images['top_artists_5'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

            # Top 15 Artists
            fig, ax = plt.subplots(figsize=(14, 8))
            bars = ax.bar(artist_count_top_15.index, artist_count_top_15.values,
                         color=plt.cm.Set3(range(len(artist_count_top_15))))
            ax.set_xlabel('Artist')
            ax.set_ylabel('Stream Count')
            ax.set_title('Top 15 Most Streamed Artists')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            images['top_artists_15'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

        # 2. Top Albums
        if 'master_metadata_album_album_name' in combined_df.columns:
            album_count = combined_df['master_metadata_album_album_name'].value_counts()
            album_count_top_5 = album_count.head()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(album_count_top_5.index, album_count_top_5.values,
                         color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
            ax.set_xlabel('Album')
            ax.set_ylabel('Stream Count')
            ax.set_title('Top 5 Most Streamed Albums')
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            images['top_albums_5'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

    except Exception as e:
        print(f"Error creating visualizations: {e}")
    
    return images

def analyze_spotify_data(combined_df):
    analysis = {
        'total_streams': combined_df.shape[0],
        'unique_artists': combined_df['master_metadata_album_artist_name'].nunique() if 'master_metadata_album_artist_name' in combined_df.columns else 0,
        'unique_tracks': combined_df['master_metadata_track_name'].nunique() if 'master_metadata_track_name' in combined_df.columns else 0,
        'unique_albums': combined_df['master_metadata_album_album_name'].nunique() if 'master_metadata_album_album_name' in combined_df.columns else 0,
        'time_period': {},
        'top_artists': {},
        'top_albums': {},
        'top_tracks': {},
        'specific_artists': {},
        'listening_behavior': {},
        'platform_usage': {}
    }
    #top artists
    if 'master_metadata_album_artist_name' in combined_df.columns:
        artist_counts = combined_df['master_metadata_album_artist_name'].value_counts()
        analysis['top_artists'] = {
            'top_5': artist_counts.head(5).to_dict(),
            'top_15': artist_counts.head(15).to_dict(),
            'total_unique': len(artist_counts)
        }
    #top albums
    if 'master_metadata_album_album_name' in combined_df.columns:
        album_counts = combined_df['master_metadata_album_album_name'].value_counts()
        analysis['top_albums'] = {
            'top_5': album_counts.head(5).to_dict(),
            'top_15': album_counts.head(15).to_dict(),
            'total_unique': len(album_counts)
        }

    return analysis

@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/api/analyze-spotify', methods=['POST'])
def analyze_spotify_files():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = [file for file in files if file.filename != '']
        
        if len(uploaded_files) == 0:
            return jsonify({'error': 'No valid files selected'}), 400
        
        all_dataframes = []
        processed_files = []
        errors = []
        total_songs = 0
        
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                try:
                    file_content = file.read().decode('utf-8')
                    json_data = json.loads(file_content)

                    # Count songs in this file
                    if isinstance(json_data, list):
                        file_song_count = len(json_data)
                    else:
                        file_song_count = 1
                    
                    total_songs += file_song_count  # ADDED: Accumulate total songs
                    
                    # Handle Spotify JSON structure (array of listening events)
                    if isinstance(json_data, list):
                        df = pd.DataFrame(json_data)
                    else:
                        df = pd.DataFrame([json_data])
                    
                    # Add filename for tracking
                    df['source_file'] = file.filename
                    all_dataframes.append(df)
                    
                    processed_files.append({
                        'filename': file.filename,
                        'records': df.shape[0],
                        'song_count': file_song_count,
                        'columns': list(df.columns)
                    })
                    
                    print(f"Processed: {file.filename} -> {df.shape[0]} records")
                    
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON in {file.filename}: {str(e)}")
                except Exception as e:
                    errors.append(f"Error processing {file.filename}: {str(e)}")
            else:
                errors.append(f"Invalid file type: {file.filename}")
        
        if len(all_dataframes) == 0:
            return jsonify({'error': 'No valid JSON files could be processed', 'errors': errors}), 400
        
        # Combine all DataFrames
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Print basic info (for debugging)
        num_rows = combined_df.shape[0]
        print(f"Total rows: {num_rows}")
        print(f"Total songs: {total_songs}")
        
        if 'master_metadata_album_artist_name' in combined_df.columns:
            artist_count = combined_df['master_metadata_album_artist_name'].value_counts()
            print("Top artists:")
            print(artist_count.head())
            
            # Specific artist count (like in your example)
            if 'Kanye West' in artist_count:
                kanye_count = artist_count['Kanye West']
                print(f"# of streams for Kanye West: {kanye_count}")
            if 'Mac Miller' in artist_count:
                mac_count = artist_count['Mac Miller']
                print(f"# of streams for Mac Miller: {mac_count}")
        
        # Perform Spotify-specific analysis
        analysis_results = analyze_spotify_data(combined_df)
        
        # Create visualizations
        visualization_images = create_spotify_visualizations(combined_df, analysis_results)
        
        # Sample data for preview
        sample_data = combined_df.head(10).to_dict('records')
        
        response_data = {
            'message': f'Successfully analyzed {len(processed_files)} Spotify data files',
            'processedFiles': processed_files,
            'combinedData': {
                'totalRecords': len(combined_df),
                'totalSongs': total_songs,
                'shape': combined_df.shape,
                'sample': sample_data
            },
            'analysis': analysis_results,
            'visualizations': visualization_images,
            'errors': errors
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5173)