import numpy as np
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
from datetime import datetime, date
from flask_cors import CORS



app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'json'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024
current_combined = None

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def analyze_spotify_data(combined_df):
    analysis = {
        'total_streams': combined_df.shape[0],
        'unique_artists': combined_df['master_metadata_album_artist_name'].nunique() if 'master_metadata_album_artist_name' in combined_df.columns else 0,
        'unique_tracks': combined_df['master_metadata_track_name'].nunique() if 'master_metadata_track_name' in combined_df.columns else 0,
        'unique_albums': combined_df['master_metadata_album_album_name'].nunique() if 'master_metadata_album_album_name' in combined_df.columns else 0,
        'time_period': {},
        'top_artists': {},
        'specific_artists': {},
        'listening_behavior': {},
        'images': {}
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
    try:
        if 'ts' not in combined_df.columns:
            return {'error': 'Timestamp data not available'}
        
        df = combined_df.copy()
        
        # Convert to datetime and handle errors
        df['ts'] = pd.to_datetime(df['ts'], errors='coerce')
        
        # Check for invalid timestamps
        invalid_timestamps = df['ts'].isna().sum()
        if invalid_timestamps > 0:
            df = df.dropna(subset=['ts'])
        
        if len(df) == 0:
            return {'error': 'No valid timestamp data available'}
        
        # Apply date filter if provided
        if start_date:
            try:
                start_date = pd.to_datetime(start_date)
                df = df[df['ts'] >= start_date]
            except Exception:
                pass
        
        if end_date:
            try:
                end_date = pd.to_datetime(end_date)
                df = df[df['ts'] <= end_date]
            except Exception:
                pass
        
        # Hourly analysis - ensure we use native Python types
        df['hour'] = df['ts'].dt.hour
        hourly_counts = df['hour'].value_counts().sort_index()
        
        # Fill missing hours with 0 and convert to native types
        all_hours = pd.Series(0, index=range(24))
        hourly_counts = hourly_counts.reindex(all_hours.index, fill_value=0)
        
        # Convert Series to native Python dict with native types
        hourly_distribution = {}
        for hour, count in hourly_counts.items():
            hourly_distribution[int(hour)] = int(count)
        
        # Calculate time period summaries with native types
        time_periods = {
            'early_morning_0_5': int(hourly_counts.loc[0:5].sum()),
            'morning_6_11': int(hourly_counts.loc[6:11].sum()),
            'afternoon_12_17': int(hourly_counts.loc[12:17].sum()),
            'evening_18_21': int(hourly_counts.loc[18:21].sum()),
            'late_night_22_23': int(hourly_counts.loc[22:23].sum())
        }
        
        # Find peak hour with native types
        peak_hour_idx = hourly_counts.idxmax()
        peak_hour_count = hourly_counts.max()
        
        result = {
            'hourly_distribution': hourly_distribution,
            'peak_hour': int(peak_hour_idx),
            'peak_hour_count': int(peak_hour_count),
            'time_of_day_summary': time_periods,
            'total_streams_in_range': int(len(df))
        }
        
        print(f"Debug: Analysis completed - peak_hour: {result['peak_hour']}")
        return result
        
    except Exception as e:
        print(f"Error in get_time_of_day_analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': f'Analysis failed: {str(e)}'}
    
def convert_to_serializable(obj):
    """
    Recursively convert pandas/numpy types to native Python types for JSON serialization
    """
    if obj is None:
        return None
    elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.bool_, np.bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif hasattr(obj, 'dtype') and hasattr(obj, 'tolist'):  # Other pandas/numpy types
        return obj.tolist()
    else:
        return obj

def safe_jsonify(data):
    """
    Safely convert data to JSON, handling all pandas/numpy types
    """
    serializable_data = convert_to_serializable(data)
    return jsonify(serializable_data)

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

        # 2. Time of Day Analysis (if timestamp data available)
        if 'ts' in combined_df.columns:
            combined_df['ts'] = pd.to_datetime(combined_df['ts'])
            combined_df['hour'] = combined_df['ts'].dt.hour
            hourly_counts = combined_df['hour'].value_counts().sort_index()
            
            # Time of day chart
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(hourly_counts.index, hourly_counts.values, marker='o', linewidth=2, markersize=6, color='#1DB954')
            ax.fill_between(hourly_counts.index, hourly_counts.values, alpha=0.3, color='#1DB954')
            ax.set_xlabel('Hour of Day')
            ax.set_ylabel('Number of Streams')
            ax.set_title('Listening Activity Throughout the Day')
            ax.set_xticks(range(0, 24, 2))
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            images['time_of_day'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

        # 3. Streams Over Time (if timestamp data available)
        if 'ts' in combined_df.columns:
            daily_streams = combined_df.groupby(combined_df['ts'].dt.date).size()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(daily_streams.index, daily_streams.values, linewidth=2, color='#191414')
            ax.set_xlabel('Date')
            ax.set_ylabel('Daily Streams')
            ax.set_title('Listening Activity Over Time')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            images['streams_over_time'] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()

    except Exception as e:
        print(f"Error creating visualizations: {e}")
    
    return images


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
    global current_combined
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
                    
                    total_songs += file_song_count
                    
                    # Handle Spotify JSON structure
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

        # Perform analysis ONCE
        analysis_results = analyze_spotify_data(combined_df)
        
        # Create visualizations
        visualization_images = create_spotify_visualizations(combined_df, analysis_results)
        
        # Print debug info
        num_rows = combined_df.shape[0]
        print(f"Total rows: {num_rows}")
        print(f"Total songs: {total_songs}")
        
        if 'master_metadata_album_artist_name' in combined_df.columns:
            artist_count = combined_df['master_metadata_album_artist_name'].value_counts()
            print("Top artists:")
            print(artist_count.head())
        
        # Extract tracks data for frontend ONCE
        tracks_data = []
        if 'master_metadata_track_name' in combined_df.columns and 'master_metadata_album_artist_name' in combined_df.columns:
            essential_cols = ['master_metadata_track_name', 'master_metadata_album_artist_name', 'ts']
            available_cols = [col for col in essential_cols if col in combined_df.columns]
            tracks_data = combined_df[available_cols].to_dict('records')
        
        # Store globally for other endpoints
        current_combined = {
            'combined_df': combined_df,
            'analysis_results': analysis_results,
            'visualizations': visualization_images
        }

        # **CRITICAL: Return ALL necessary data for frontend**
        response_data = {
            'message': f'Successfully analyzed {len(processed_files)} Spotify data files',
            'processedFiles': processed_files,
            'combinedData': {
                'totalRecords': len(combined_df),
                'totalSongs': total_songs,
                'tracksData': tracks_data  
            },
            'analysis': analysis_results,  # This is what ArtistsPage needs!
            'visualizations': visualization_images,
            'errors': errors,
            # Add explicit success flag
            'success': True,
            # Add analysis metadata for frontend
            'analysisMetadata': {
                'hasData': True,
                'totalArtists': analysis_results.get('unique_artists', 0),
                'totalTracks': analysis_results.get('unique_tracks', 0),
                'totalStreams': analysis_results.get('total_streams', 0)
            }
        }
        
        print(f"Analysis complete. Returning data with {len(combined_df)} records")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error in analyze-spotify: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/artists/time-of-day-analysis', methods=['GET'])
def get_artists_TOD_analysis():
    global current_combined

    if not current_combined or current_combined['combined_df'] is None:
        return jsonify({'error': 'No analysis data available. Please analyze files first.'}), 400
    
    try:
        print("Debug: Starting time of day analysis...")
        
        # Check if timestamp column exists
        if 'ts' not in current_combined['combined_df'].columns:
            return jsonify({'error': 'Timestamp data not available in the analyzed files'}), 400
        
        time_analysis = get_time_of_day_analysis(current_combined['combined_df'])
        print(f"Debug: Time analysis completed successfully")
        
        # Use the safe JSON converter
        return safe_jsonify(time_analysis)
    
    except Exception as e:
        print(f"Error in time-of-day analysis: {str(e)}")
        import traceback
        traceback.print_exc()
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

@app.route('/api/top-albums', methods=['GET'])
def get_top_albums():
    global current_combined

    if not current_combined or current_combined['combined_df'] is None:
        return jsonify([])  # No data yet

    df = current_combined['combined_df'].copy()
    df['ts'] = pd.to_datetime(df['ts'])

    # Filters
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    time_filter = request.args.get('time', 'all')
    season = request.args.get('season', 'all')

    # Date filters
    if start:
        df = df[df['ts'] >= pd.to_datetime(start)]
    if end:
        df = df[df['ts'] <= pd.to_datetime(end)]

    # Time-of-day filter
    if time_filter != 'all':
        hour = df['ts'].dt.hour
        if time_filter == 'morning':
            df = df[(hour >= 6) & (hour < 12)]
        elif time_filter == 'afternoon':
            df = df[(hour >= 12) & (hour < 17)]
        elif time_filter == 'evening':
            df = df[(hour >= 17) & (hour < 21)]
        elif time_filter == 'night':
            df = df[(hour >= 21) | (hour < 6)]

    # Season filter
    month = df['ts'].dt.month
    if season == 'spring':
        df = df[month.isin([3,4,5])]
    elif season == 'summer':
        df = df[month.isin([6,7,8])]
    elif season == 'fall':
        df = df[month.isin([9,10,11])]
    elif season == 'winter':
        df = df[month.isin([12,1,2])]

    # Album aggregation
    if 'master_metadata_album_album_name' not in df.columns:
        return jsonify([])

    album_counts = df.groupby([
        'master_metadata_album_album_name',
        'master_metadata_album_artist_name'
    ]).size().reset_index(name='plays')

    album_counts = album_counts.sort_values('plays', ascending=False)

    results = []
    for _, row in album_counts.iterrows():
        results.append({
            'title': row['master_metadata_album_album_name'],
            'artist': row['master_metadata_album_artist_name'],
            'plays': int(row['plays']),
            'cover': ''  # optional placeholder
        })

    return jsonify(results)

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
    app.run(debug=True, port=5173)