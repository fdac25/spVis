import { useState, useEffect } from 'react';
import './tracks_style.css';
import trackImg from './assets/track_front_img.png';
import backgroundImg from './assets/black_and_grey_Background_2.PNG';

const TracksPage = ({ analysisResult }) => {
  const [tracks, setTracks] = useState([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch tracks on initial load
  useEffect(() => {
    if (analysisResult?.combinedData?.tracksData) {
      fetchTracks();
    }
  }, [analysisResult]);

  // Fetch tracks from backend API
  const fetchTracks = async (params = {}) => {
    if (!analysisResult?.combinedData?.tracksData) {
      setError('No tracks data available');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('/api/top-tracks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          processedFiles: analysisResult.processedFiles,
          tracks_data: analysisResult.combinedData.tracksData,
          start_date: params.start || '',
          end_date: params.end || ''
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch tracks');
      }
      
      const data = await response.json();
      setTracks(data);
    } catch (err) {
      console.error('Error fetching tracks:', err);
      setError('Failed to load tracks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle filter button click
  const handleApplyFilter = () => {
    fetchTracks({
      start: startDate,
      end: endDate
    });
  };

  return (
    <>
      {/* HEADER */}
      <header>
        <a href="#" className="logo">SpVis</a>

        <nav>
          <a href="#">Home</a>
          <a href="#" className="active">Tracks</a>
          <a href="#">Albums</a>
          <a href="#">Artists</a>
        </nav>
      </header>

      {/* TOP SECTION */}
      <section className="tracks_top">
        <div className="tracks-img_top">
          <img src={trackImg} alt="playing bar" />
        </div>

        <div className="tracks-content_top">
          <h1>Your </h1>
          <span>TOP</span>
          <h1> tracks</h1>
        </div>
      </section>

      <section className="seperator_top">
        <img src={backgroundImg} alt="background" />
      </section>

      {/* MIDDLE SECTION */}
      <section className="tracks_middle">
        <h3>Top 10 Tracks</h3>

        {/* DATE FILTER */}
        <div className="date-filter">
          <label htmlFor="startDate">Start Date:</label>
          <input 
            type="date" 
            id="startDate" 
            name="startDate"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />

          <label htmlFor="endDate">End Date:</label>
          <input 
            type="date" 
            id="endDate" 
            name="endDate"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />

          <button 
            type="button" 
            className="filter_button"
            onClick={handleApplyFilter}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Filter'}
          </button>
        </div>

        {/* ERROR MESSAGE */}
        {error && (
          <div style={{ color: 'red', padding: '1rem' }}>
            {error}
          </div>
        )}

        {/* SONG LIST */}
        <ul id="songList" className="song-list">
          {loading ? (
            <li style={{ textAlign: 'center', padding: '2rem' }}>Loading tracks...</li>
          ) : tracks.length === 0 ? (
            <li style={{ textAlign: 'center', padding: '2rem' }}>
              {analysisResult ? 'No tracks found for the selected period' : 'Please upload data to see tracks'}
            </li>
          ) : (
            tracks.map((track) => (
              <li className="song" key={`${track.rank}-${track.title}`}>
                <span className="rank">{track.rank}</span>
                <span className="title">{track.title}</span>
                <span className="artist">{track.artist}</span>
                <span className="play-count">{track.play_count} plays</span>
              </li>
            ))
          )}
        </ul>
      </section>

      <h3>SpVis - 2025</h3>
    </>
  );
};

export default TracksPage;