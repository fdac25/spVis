import { useState, useEffect } from 'react';
import './App.css'

const ArtistsPage = ({ analysisResult }) => {
  const [timeAnalysis, setTimeAnalysis] = useState(null);
  const [topArtists, setTopArtists] = useState(null);
  const [visualizations, setVisualizations] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedArtist, setSelectedArtist] = useState('');
  const [artistBuildup, setArtistBuildup] = useState(null);
  const [availableArtists, setAvailableArtists] = useState([]);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    console.log('ArtistsPage Mounted:', { 
      hasAnalysis: !!analysisResult,
      analysisData: analysisResult 
    });
  }, []);

  useEffect(() => {
    const fetchArtistsData = async () => {
      // Use localAnalysisResult instead of analysisResult
      if (!localAnalysisResult) {
        setError('No analysis data available. Please analyze your Spotify files on the home page first.');
        setLoading(false);
        return;
      }
    
      try {
        setLoading(true);
        setError(null);
        
        console.log('Fetching artists data with analysis:', localAnalysisResult);
    
        // Add a delay to ensure backend is ready
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // First, check if backend is ready
        const statusResponse = await fetch('/api/analysis/status');
        if (statusResponse.ok) {
          const status = await statusResponse.json();
          console.log('Backend status:', status);
          
          if (!status.analysisReady) {
            throw new Error('Backend analysis not ready yet. Please wait...');
          }
        }
    
        // Fetch time of day analysis
        const timeResponse = await fetch('/api/artists/time-of-day-analysis');
        if (timeResponse.status === 400) {
          throw new Error('Backend not ready. Please ensure files were analyzed successfully.');
        }
        if (!timeResponse.ok) {
          throw new Error(`Time analysis failed: ${timeResponse.status}`);
        }
        const timeData = await timeResponse.json();
        if (timeData.error) throw new Error(timeData.error);
        setTimeAnalysis(timeData);
        
        // Fetch top artists
        const artistsResponse = await fetch('/api/artists/top-artists');
        if (!artistsResponse.ok) {
          throw new Error(`Top artists failed: ${artistsResponse.status}`);
        }
        const artistsData = await artistsResponse.json();
        if (artistsData.error) throw new Error(artistsData.error);
        setTopArtists(artistsData);
        
        // Fetch visualizations
        const vizResponse = await fetch('/api/visualizations/top-artists');
        if (vizResponse.ok) {
          const vizData = await vizResponse.json();
          setVisualizations(vizData);
        } else {
          console.warn('Visualizations not available yet');
        }
        
        // Fetch available artists for dropdown
        const availableResponse = await fetch('/api/artists/available-artists');
        if (availableResponse.ok) {
          const availableData = await availableResponse.json();
          setAvailableArtists(availableData.artists || []);
        }
        
      } catch (error) {
        console.error('Error fetching artists data:', error);
        
        // Retry logic
        if (retryCount < 3) {
          setRetryCount(prev => prev + 1);
          setError(`Retrying... (${retryCount + 1}/3): ${error.message}`);
        } else {
          setError(error.message);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchArtistsData();
  }, [localAnalysisResult, retryCount]);

  

  const handleArtistAnalysis = async () => {
    if (!selectedArtist) return;
    
    try {
      setError(null);
      const response = await fetch('/api/artists/stream-buildup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          artistName: selectedArtist
        })
      });
      const data = await response.json();
      setArtistBuildup(data);
    } catch (error) {
      console.error('Error fetching artist buildup:', error);
      setError(error.message);
    }
  };

  const displayImage = (base64String) => {
    return `data:image/png;base64,${base64String}`;
  };

  // Helper function to get most active time
  const getMostActiveTime = (timeSummary) => {
    if (!timeSummary || Object.keys(timeSummary).length === 0) {
      return 'No data';
    }
    const entries = Object.entries(timeSummary);
    const mostActive = entries.reduce((a, b) => a[1] > b[1] ? a : b);
    return mostActive[0].replace(/_/g, ' ');
  };

  if (loading) {
    return (
      <div className="loading">
        <h1>Artist Analysis</h1>
        <p>Loading artist data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-page">
        <h1>Artist Analysis</h1>
        <div className="error-message">
          <h3>Error Loading Data</h3>
          <p>{error}</p>
          <p>Please make sure you've analyzed files on the home page first.</p>
        </div>
      </div>
    );
  }

  if (!analysisResult) {
    return (
      <div className="no-data">
        <h1>Artist Analysis</h1>
        <p>Please analyze your Spotify files first on the home page.</p>
      </div>
    );
  }

  return (
    <div className="artists-page">
      <h1>Artist Analysis</h1>
      
      {/* Error display for API issues */}
      {error && (
        <div className="error-message" style={{marginBottom: '2rem'}}>
          <p>{error}</p>
        </div>
      )}
      
      {/* Top Artists Visualizations */}
      <section className="visualization-section">
        <h2>Top Artists</h2>
        {Object.keys(visualizations).length === 0 ? (
          <p>No visualizations available. Please analyze files on the home page.</p>
        ) : (
          <div className="visualization-grid">
            {visualizations.top_artists_5 && (
              <div className="chart-container">
                <h3>Top 5 Artists</h3>
                <img 
                  src={displayImage(visualizations.top_artists_5)} 
                  alt="Top 5 Artists" 
                  className="chart-image"
                />
              </div>
            )}
            
            {visualizations.top_artists_15 && (
              <div className="chart-container">
                <h3>Top 15 Artists</h3>
                <img 
                  src={displayImage(visualizations.top_artists_15)} 
                  alt="Top 15 Artists" 
                  className="chart-image"
                />
              </div>
            )}
          </div>
        )}
      </section>

      {/* Time of Day Analysis */}
      {timeAnalysis && (
        <section className="time-analysis-section">
          <h2>Listening Patterns</h2>
          <div className="time-stats">
            <div className="stat-card">
              <h4>Peak Listening Hour</h4>
              <p className="stat-value">{timeAnalysis.peak_hour}:00</p>
              <p className="stat-detail">{timeAnalysis.peak_hour_count} streams</p>
            </div>
            <div className="stat-card">
              <h4>Most Active Time</h4>
              <p className="stat-value">
                {getMostActiveTime(timeAnalysis.time_of_day_summary)}
              </p>
            </div>
          </div>
          
          {/* Time distribution breakdown */}
          <div className="time-breakdown">
            <h4>Streams by Time of Day</h4>
            {timeAnalysis.time_of_day_summary && Object.entries(timeAnalysis.time_of_day_summary).map(([time, count]) => (
              <div key={time} className="time-slot">
                <span className="time-label">{time.replace(/_/g, ' ')}:</span>
                <span className="time-count">{count} streams</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Top Artists List */}
      {topArtists && topArtists.top_artists && (
        <section className="top-artists-section">
          <h2>Top Artists Ranking</h2>
          <div className="artists-lists">
            <div className="artist-list">
              <h4>Top 5 Artists</h4>
              <ol>
                {Object.entries(topArtists.top_artists.top_5 || {}).map(([artist, count], index) => (
                  <li key={artist}>
                    <span className="artist-name">{artist}</span>
                    <span className="stream-count">{count} streams</span>
                  </li>
                ))}
              </ol>
            </div>
            
            <div className="artist-list">
              <h4>Top 15 Artists</h4>
              <ol>
                {Object.entries(topArtists.top_artists.top_15 || {}).map(([artist, count], index) => (
                  <li key={artist}>
                    <span className="artist-name">{artist}</span>
                    <span className="stream-count">{count} streams</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>
      )}

      {/* Individual Artist Analysis */}
      <section className="individual-artist-section">
        <h2>Analyze Specific Artist</h2>
        <div className="artist-search">
          <input
            type="text"
            value={selectedArtist}
            onChange={(e) => setSelectedArtist(e.target.value)}
            placeholder="Enter artist name..."
            className="artist-input"
            list="artist-suggestions"
          />
          <datalist id="artist-suggestions">
            {availableArtists.map(artist => (
              <option key={artist} value={artist} />
            ))}
          </datalist>
          
          <button 
            onClick={handleArtistAnalysis}
            disabled={!selectedArtist.trim()}
            className="analyze-button"
          >
            Analyze Artist
          </button>
        </div>

        {artistBuildup && (
          <div className="artist-buildup-results">
            {artistBuildup.error ? (
              <div className="error-message">
                <h4>Error</h4>
                <p>{artistBuildup.error}</p>
                {availableArtists.length > 0 && (
                  <div className="suggestions">
                    <p>Available artists include:</p>
                    <ul className="artist-suggestions-list">
                      {availableArtists.slice(0, 10).map(artist => (
                        <li key={artist} className="suggestion-item">
                          {artist}
                        </li>
                      ))}
                    </ul>
                    {availableArtists.length > 10 && (
                      <p className="more-artists">...and {availableArtists.length - 10} more artists</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <>
                <h3>{artistBuildup.artist_name} - Streaming History</h3>
                <div className="buildup-stats">
                  <div className="stat-card">
                    <h4>Total Streams</h4>
                    <p className="stat-value">{artistBuildup.total_streams}</p>
                  </div>
                  <div className="stat-card">
                    <h4>Average Daily Streams</h4>
                    <p className="stat-value">
                      {artistBuildup.stream_frequency?.average_daily?.toFixed(2) || '0'}
                    </p>
                  </div>
                  <div className="stat-card">
                    <h4>Most Streams in One Day</h4>
                    <p className="stat-value">
                      {artistBuildup.stream_frequency?.most_streams_in_day || '0'}
                    </p>
                  </div>
                </div>
                
                {/* Date Range */}
                {artistBuildup.date_range && (
                  <div className="date-range">
                    <h4>Listening Period</h4>
                    <p>First stream: {new Date(artistBuildup.date_range.first_stream).toLocaleDateString()}</p>
                    <p>Last stream: {new Date(artistBuildup.date_range.last_stream).toLocaleDateString()}</p>
                  </div>
                )}
                
                {/* Buildup data */}
                {artistBuildup.buildup_data && artistBuildup.buildup_data.length > 0 && (
                  <div className="buildup-chart">
                    <h4>Streaming Buildup Over Time</h4>
                    <p>Data available for {artistBuildup.buildup_data.length} days</p>
                    <div className="buildup-preview">
                      <p>First 5 days of streaming:</p>
                      <ul>
                        {artistBuildup.buildup_data.slice(0, 5).map((day, index) => (
                          <li key={index}>
                            {new Date(day.date).toLocaleDateString()}: {day.daily_streams} streams (Total: {day.cumulative_streams})
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default ArtistsPage;