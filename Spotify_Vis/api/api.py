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
from datetime import datetime


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
        'specific_artists': {},
        'listening_behavior': {}
    }
    #top artists
    if 'master_metadata_album_artist_name' in combined_df.columns:
        artist_counts = combined_df['master_metadata_album_artist_name'].value_counts()
        analysis['top_artists'] = {
            'top_5': artist_counts.head(5).to_dict(),
            'top_15': artist_counts.head(15).to_dict(),
            'total_unique': len(artist_counts)
        }
    return analysis
    
    
def artist_stream_buildup(combined_df, artist_name, start_date=None, end_date=None):
    if 'master_metadata_album_artist_name' not in combined_df.columns or 'ts' not in combined_df.columns:
        return {}
    
    artist_df = combined_df[combined_df['master_metadata_album_artist_name'] == artist_name].copy()
    
    if artist_df.empty:
        return {'error': f'No data found for artist: {artist_name}'}
    
    # Convert to datetime and sort
    artist_df['ts'] = pd.to_datetime(artist_df['ts'])
    artist_df = artist_df.sort_values('ts')
    
    # Apply date filter if provided
    if start_date:
        start_date = pd.to_datetime(start_date)
        artist_df = artist_df[artist_df['ts'] >= start_date]
    if end_date:
        end_date = pd.to_datetime(end_date)
        artist_df = artist_df[artist_df['ts'] <= end_date]

    # Calculate cumulative streams
    artist_df = artist_df.sort_values('ts')
    artist_df['cumulative_streams'] = range(1, len(artist_df) + 1)
    
    # Group by different time periods for different views
    daily_streams = artist_df.groupby(artist_df['ts'].dt.date).size()
    weekly_streams = artist_df.groupby(artist_df['ts'].dt.to_period('W')).size()
    monthly_streams = artist_df.groupby(artist_df['ts'].dt.to_period('M')).size()
    
    # Create buildup data points (for charting)
    buildup_data = []
    cumulative = 0
    for date, count in daily_streams.items():
        cumulative += count
        buildup_data.append({
            'date': date.isoformat(),
            'daily_streams': count,
            'cumulative_streams': cumulative
        })
    
    return {
        'artist_name': artist_name,
        'total_streams': len(artist_df),
        'date_range': {
            'first_stream': artist_df['ts'].min().isoformat(),
            'last_stream': artist_df['ts'].max().isoformat()
        },
        'buildup_data': buildup_data,
        'period_totals': {
            'daily': daily_streams.to_dict(),
            'weekly': {str(period): count for period, count in weekly_streams.items()},
            'monthly': {str(period): count for period, count in monthly_streams.items()}
        },
        'stream_frequency': {
            'average_daily': len(artist_df) / max(1, (artist_df['ts'].max() - artist_df['ts'].min()).days),
            'most_active_day': daily_streams.idxmax().isoformat() if not daily_streams.empty else None,
            'most_streams_in_day': daily_streams.max() if not daily_streams.empty else 0
        }
    }

def get_time_of_day_analysis(combined_df, start_date=None, end_date=None):
    """
    Get detailed time of day analysis for a specific date range
    """
    if 'ts' not in combined_df.columns:
        return {}
    
    df = combined_df.copy()
    df['ts'] = pd.to_datetime(df['ts'])
    
    # Apply date filter if provided
    if start_date:
        start_date = pd.to_datetime(start_date)
        df = df[df['ts'] >= start_date]
    if end_date:
        end_date = pd.to_datetime(end_date)
        df = df[df['ts'] <= end_date]
    
    # Hourly analysis
    df['hour'] = df['ts'].dt.hour
    hourly_counts = df['hour'].value_counts().sort_index()
    
    # Fill missing hours with 0
    all_hours = pd.Series(0, index=range(24))
    hourly_counts = hourly_counts.reindex(all_hours.index, fill_value=0)
    
    return {
        'hourly_distribution': hourly_counts.to_dict(),
        'peak_hour': hourly_counts.idxmax(),
        'peak_hour_count': hourly_counts.max(),
        'time_of_day_summary': {
            'early_morning_0_5': hourly_counts.loc[0:5].sum(),
            'morning_6_11': hourly_counts.loc[6:11].sum(),
            'afternoon_12_17': hourly_counts.loc[12:17].sum(),
            'evening_18_21': hourly_counts.loc[18:21].sum(),
            'late_night_22_23': hourly_counts.loc[22:23].sum()
        },
        'total_streams_in_range': len(df)
    }

current_combined = None

@app.route('/api/top-tracks', methods=['POST'])
def get_top_tracks():
    try:
        # Get the raw track data from the request body
        data = request.get_json()
        
        if not data or 'processedFiles' not in data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get filter parameters
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')
        
        # Reconstruct the dataframe from the processed files data
        # We'll need the raw data sent from frontend
        tracks_data = data.get('tracks_data', [])
        
        if not tracks_data:
            return jsonify({'error': 'No track data available'}), 400
        
        # Create DataFrame from the tracks data
        df = pd.DataFrame(tracks_data)
        
        # Apply date filters if provided
        if 'ts' in df.columns:
            df['timestamp'] = pd.to_datetime(df['ts'])
            
            if start_date and start_date.strip():
                df = df[df['timestamp'] >= pd.to_datetime(start_date)]
            if end_date and end_date.strip():
                df = df[df['timestamp'] <= pd.to_datetime(end_date)]
        
        # Get top tracks
        if 'master_metadata_track_name' in df.columns and 'master_metadata_album_artist_name' in df.columns:
            # Group by track and artist to get play counts
            track_counts = df.groupby([
                'master_metadata_track_name',
                'master_metadata_album_artist_name'
            ]).size().reset_index(name='play_count')
            
            # Sort by play count and get top 10
            top_tracks = track_counts.nlargest(10, 'play_count')
            
            # Convert to list of dictionaries
            tracks_list = []
            for idx, row in top_tracks.iterrows():
                tracks_list.append({
                    'rank': len(tracks_list) + 1,
                    'title': row['master_metadata_track_name'],
                    'artist': row['master_metadata_album_artist_name'],
                    'play_count': int(row['play_count'])
                })
            
            return jsonify(tracks_list), 200
        else:
            return jsonify({'error': 'Track data not available'}), 400
            
    except Exception as e:
        print(f"Error in top-tracks: {str(e)}")
        return jsonify({'error': f'Error fetching tracks: {str(e)}'}), 500

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
        
        # Perform Spotify-specific analysis
        analysis_results = analyze_spotify_data(combined_df)
        
        # Extract minimal tracks data for frontend filtering
        tracks_data = []
        if 'master_metadata_track_name' in combined_df.columns and 'master_metadata_album_artist_name' in combined_df.columns:
            # Only send the essential columns to reduce payload size
            essential_cols = ['master_metadata_track_name', 'master_metadata_album_artist_name', 'ts']
            available_cols = [col for col in essential_cols if col in combined_df.columns]
            tracks_data = combined_df[available_cols].to_dict('records')
        
        current_analysis_data = {
            'combined_df': combined_df,
            'analysis_results': analysis_results
        }
        
        response_data = {
            'message': f'Successfully analyzed {len(processed_files)} Spotify data files',
            'processedFiles': processed_files,
            'combinedData': {
                'totalRecords': len(combined_df),
                'totalSongs': total_songs,
                'tracksData': tracks_data  # Add raw tracks data here
            },
            'analysis': analysis_results,
            'errors': errors
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/artists/time-of-day-analysis', methods=['GET'])
def get_artists_TOD_analysis():
    global current_combined

    if not current_combined or current_combined['combined_df'] is None:
        return jsonify({'error': 'No analysis data available. Please analyze files first.'}), 400
    try:
        time_analysis = get_time_of_day_analysis(current_combined['combined_df'])
        return jsonify(time_analysis)
    except Exception as e:
        return jsonify({'error': f'Error analyzing time patterns: {str(e)}'}), 500
    
@app.route('/api/artists/stream-buildup', methods=['POST'])
def get_artists_buildup():
    global current_combined

    if not current_combined or current_combined['combined_df'] is None:
        return jsonify({'error': 'No analysis data available. Please analyze files first.'}), 400
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        artist_name = data.get('artistName')
        start_date = data.get('startDate')
        end_date = data.get('endDate')

        if not artist_name:
            return jsonify({'error': 'Artist name is required'}), 400
        
        buildup_data = artist_stream_buildup(
            current_combined['combined_df'],
            artist_name,
            start_date,
            end_date
        )

        return jsonify(buildup_data)
    except Exception as e:
        return jsonify({'error': f'Error analyzing artist buildup: {str(e)}'}), 500


@app.route('/api/artists/top-artists', methods=['GET'])
def get_top_artists():
    global current_combined

    if not current_combined:
        return jsonify({'top_artists': {}})
    
    try:
        top_artists = current_combined['analysis_results'].get('top_artists', {})
        return jsonify({'top_artists': top_artists})
    except Exception as e:
        return jsonify({'error':f'Error getting top artists: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5173)