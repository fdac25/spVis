import { useState, useEffect } from 'react';
import './Artist_page.css'

const ArtistsPage = ({ analysisResult }) => {
  const [artistData, setArtistData] = useState(null);
  const [timeAnalysis, setTimeAnalysis] = useState(null);

  useEffect(() => {
    if (analysisResult && analysisResult.analysis) {
      setArtistData(analysisResult.analysis);
      
      // Fetch time analysis data
      fetchTimeAnalysis();
    }
  }, [analysisResult]);

  const fetchTimeAnalysis = async () => {
    try {
      const response = await fetch('/api/artists/time-of-day-analysis');
      if (response.ok) {
        const data = await response.json();
        setTimeAnalysis(data);
      }
    } catch (error) {
      console.error('Error fetching time analysis:', error);
    }
  };

  // Helper to format time periods
  const formatTimePeriod = (period) => {
    const labels = {
      'early_morning_0_5': 'Early Morning (12AM-6AM)',
      'morning_6_11': 'Morning (6AM-12PM)',
      'afternoon_12_17': 'Afternoon (12PM-6PM)',
      'evening_18_21': 'Evening (6PM-10PM)',
      'late_night_22_23': 'Late Night (10PM-12AM)'
    };
    return labels[period] || period;
  };

  // Helper to get most active time period
  const getMostActivePeriod = (summary) => {
    if (!summary) return null;
    const entries = Object.entries(summary);
    const mostActive = entries.reduce((a, b) => a[1] > b[1] ? a : b);
    return {
      period: formatTimePeriod(mostActive[0]),
      count: mostActive[1]
    };
  };

  // Helper function to get sorted artist data
  const getSortedArtists = (data, limit = 15) => {
    if (!data) return [];
    
    return Object.entries(data)
      .sort(([, countA], [, countB]) => countB - countA) // Sort by count descending
      .slice(0, limit);
  };

  // Fixed Bar Chart - uses sorted data
  const BarChart = ({ data, width = 400, height = 300 }) => {
    const sortedArtists = getSortedArtists(data, 10);
    
    if (sortedArtists.length === 0) {
      return <p>No artist data available for chart</p>;
    }
    
    const maxValue = Math.max(...sortedArtists.map(([_, count]) => count));
    const barWidth = (width - 100) / sortedArtists.length;
    
    return (
      <svg width={width} height={height} className="bar-chart">
        {sortedArtists.map(([artist, count], index) => {
          const barHeight = (count / maxValue) * (height - 80);
          const x = 50 + (index * barWidth);
          const y = height - 30 - barHeight;
          
          return (
            <g key={artist}>
              <rect
                x={x}
                y={y}
                width={barWidth - 5}
                height={barHeight}
                fill="#1DB954"
                className="bar"
              />
              <text
                x={x + barWidth/2 - 5}
                y={height - 10}
                textAnchor="middle"
                fontSize="10"
                className="bar-label"
              >
                {index + 1}
              </text>
              <text
                x={x + barWidth/2 - 5}
                y={y - 5}
                textAnchor="middle"
                fontSize="10"
                className="bar-value"
              >
                {count}
              </text>
            </g>
          );
        })}
      </svg>
    );
  };


  if (!analysisResult) {
    return (
      <div className="no-data">
        <h1>Artist Analysis</h1>
        <p>Please analyze your Spotify files first on the home page.</p>
      </div>
    );
  }

  if (!artistData) {
    return (
      <div className="loading">
        <h1>Artist Analysis</h1>
        <p>Loading...</p>
      </div>
    );
  }

  // Get sorted artists for the list
  const topArtistsData = artistData.top_artists?.top_15 || artistData.top_artists?.top_5 || {};
  const sortedTopArtists = getSortedArtists(topArtistsData, 15);
  const mostActivePeriod = timeAnalysis ? getMostActivePeriod(timeAnalysis.time_of_day_summary) : null;

  return (
    <div className="artists-page">
      <h1>Artist Analysis</h1>

      {/* Charts Section */}
      <section className="chart-section">
        <h2>Top Artists Visualization</h2>
        
        {sortedTopArtists.length > 0 ? (
          <div className="charts-grid">
            <div className="chart-container">
              <h3>Top Artists Bar Chart</h3>
              <BarChart data={topArtistsData} />
            </div>
          </div>
        ) : (
          <p>No top artist data available for charts</p>
        )}
      </section>

      {/* Listening Patterns Section */}
      {timeAnalysis && (
        <section className="time-analysis-section">
          <h2>Listening Patterns</h2>
          
          {/* Peak Listening Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Peak Listening Hour</h3>
              <p className="stat-number">{timeAnalysis.peak_hour}:00</p>
              <p className="stat-detail">{timeAnalysis.peak_hour_count} streams</p>
            </div>
            
            {mostActivePeriod && (
              <div className="stat-card">
                <h3>Most Active Period</h3>
                <p className="stat-number">{mostActivePeriod.period.split(' ')[0]}</p>
                <p className="stat-detail">{mostActivePeriod.count} streams</p>
              </div>
            )}
            
            <div className="stat-card">
              <h3>Total in Range</h3>
              <p className="stat-number">{timeAnalysis.total_streams_in_range}</p>
              <p className="stat-detail">streams analyzed</p>
            </div>
          </div>

          {/* Time Distribution Breakdown */}
          <div className="time-distribution">
            <h3>Streams by Time of Day</h3>
            <div className="distribution-grid">
              {timeAnalysis.time_of_day_summary && Object.entries(timeAnalysis.time_of_day_summary).map(([period, count]) => (
                <div key={period} className="time-period-card">
                  <div className="period-header">
                    <h4>{formatTimePeriod(period)}</h4>
                    <span className="period-count">{count} streams</span>
                  </div>
                  <div className="period-bar">
                    <div 
                      className="period-fill"
                      style={{
                        width: `${(count / timeAnalysis.total_streams_in_range) * 100}%`
                      }}
                    ></div>
                  </div>
                  <div className="period-percentage">
                    {((count / timeAnalysis.total_streams_in_range) * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Top Artists List*/}
      <section className="top-artists">
        <h2>Your Top Artists</h2>
        
        {sortedTopArtists.length > 0 ? (
          <div className="artist-list">
            <h3>Most Played Artists (Sorted by Play Count)</h3>
            <ol>
              {sortedTopArtists.map(([artist, count], index) => (
                <li key={artist}>
                  <span className="artist-name">{index + 1}. {artist}</span>
                  <span className="stream-count">{count} plays</span>
                </li>
              ))}
            </ol>
          </div>
        ) : (
          <p>No artist data available</p>
        )}
      </section>
    </div>
  );
};

export default ArtistsPage;