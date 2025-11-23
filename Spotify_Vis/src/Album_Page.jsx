import { useState, useEffect } from 'react';
import './album_style.css';
import backgroundImg from './assets/black_and_grey_Background_2.PNG';

const AlbumPage = () => {
  {/*State for storing album data from API*/}
  const [albums, setAlbums] = useState([]);
  {/*State for filter inputs*/}
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [timeFilter, setTimeFilter] = useState('all');
  const [seasonFilter, setSeasonFilter] = useState('all');

  {/*Initial load (all data)*/}
  useEffect(() => {
    fetchAlbums();
  }, []);

  {/*Fetch from backend API*/}
  const fetchAlbums = async (params = {}) => {
    try {
      const queryParams = new URLSearchParams({
        start: params.start || '',
        end: params.end || '',
        time: params.time || 'all',
        season: params.season || 'all'
      });
      
      const response = await fetch(`/api/top-albums?${queryParams}`);
      const data = await response.json();
      setAlbums(data);
    } catch (err) {
      console.error('Error fetching albums:', err);
    }
  };

  {/*Get inputs and use filter button*/}
  const handleApplyFilter = () => {
    fetchAlbums({
      start: startDate,
      end: endDate,
      time: timeFilter,
      season: seasonFilter
    });
  };

  return (
    <>
      {/* HEADER CODE */}
      <header>
        <a href="#" className="logo">SpVis</a>
        {/* Navigation Bar */}
        <nav>
          <a href="#">Home</a> {/* Placeholder until Homepage is designed */}
          <a href="#">Tracks</a>
          <a href="#">Albums</a>
          <a href="#">Artists</a> {/* Placeholder until Artists page is designed */}
        </nav>
      </header>

      {/* TOP SECTION CODE */}
      <section className="album_top">
        {/* Albums Image (Vinyl Record) */}
        <div className="album-img_top">
          <svg width="200" height="200" viewBox="0 0 200 200">
            {/* Outer vinyl edge */}
            <circle cx="100" cy="100" r="95" fill="#1a1a1a" stroke="#333" strokeWidth="2"/>
            
            {/* grooves (multiple rings) */}
            <circle cx="100" cy="100" r="90" fill="none" stroke="#0a0a0a" strokeWidth="1"/>
            <circle cx="100" cy="100" r="85" fill="none" stroke="#0a0a0a" strokeWidth="1"/>
            <circle cx="100" cy="100" r="80" fill="none" stroke="#0a0a0a" strokeWidth="1"/>
            <circle cx="100" cy="100" r="75" fill="none" stroke="#0a0a0a" strokeWidth="1"/>
            <circle cx="100" cy="100" r="70" fill="#0a0a0a"/>
            
            {/* Green label area */}
            <circle cx="100" cy="100" r="50" fill="#1db954"/>
            
            {/* Small indicator marks on label */}
            <line x1="100" y1="55" x2="100" y2="65" stroke="#000" strokeWidth="2"/>
            <circle cx="100" cy="120" r="3" fill="#000"/>
            
            {/* Center hole */}
            <circle cx="100" cy="100" r="15" fill="#000"/>
          </svg>
        </div>
        <div className="album-content_top">
          <h1>Your</h1> <span>TOP</span> <h1>Albums</h1>
        </div>
      </section>

      {/* Separator */}
      <section className="separator_top">
        <img src={backgroundImg} alt="background" />
      </section>

      {/* MIDDLE SECTION CODE */}
      <section className="album_middle">
        {/* Controllers for the User */}
        <div className="controls-container">
          <h3>Top Albums</h3>
          {/* Date Filter */}
          <div className="filter-row">
            {/* Starting Date */}
            <div className="input-group">
              <label htmlFor="startDate">Start:</label>
              <input 
                type="date" 
                id="startDate" 
                name="startDate"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            {/* Ending Date */}
            <div className="input-group">
              <label htmlFor="endDate">End:</label>
              <input 
                type="date" 
                id="endDate" 
                name="endDate"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            {/* Time of Day */}
            <div className="input-group">
              <label htmlFor="timeFilter">Time of Day:</label>
              <select id="timeFilter" value={timeFilter} onChange={(e) => setTimeFilter(e.target.value)}>
                <option value="all">All Day</option>
                <option value="morning">Morning (6am - 12pm)</option>
                <option value="afternoon">Afternoon (12pm - 5pm)</option>
                <option value="evening">Evening (5pm - 9pm)</option>
                <option value="night">Late Night (9pm - 6am)</option>
              </select>
            </div>
            {/* Season Filter */}
            <div className="input-group">
              <label htmlFor="seasonFilter">Seasons:</label>
              <select id="seasonFilter" value={seasonFilter} onChange={(e) => setSeasonFilter(e.target.value)}>
                <option value="all">All Year</option>
                <option value="spring">Spring (Mar-May)</option>
                <option value="summer">Summer (Jun-Aug)</option>
                <option value="fall">Fall (Sep-Nov)</option>
                <option value="winter">Winter (Dec-Feb)</option>
              </select>
            </div>

            {/* Apply Filter */}
            <button type="button" className="filter_button" onClick={handleApplyFilter}>
              Apply Filter
            </button>
          </div>
        </div>

        {/* Dynamically load the top albums */}
        <ul id="albumList" className="album-list">
          {albums.length === 0 ? (
            <li style={{ padding: '60px', textAlign: 'center', color: '#666', fontSize: '18px' }}>
              No albums found with the current filters.
            </li>
          ) : (
            //Iterate through albums and list them (slice to top 50 if needed)
            albums.slice(0, 50).map((album, index) => (
              <li key={`${album.title}-${index}`} className="album">
                <span className="rank">{index + 1}</span>
                <div className="album-cover">
                  <img src={album.cover || 'assets/placeholder_album.jpg'} alt={album.title} />
                </div>
                <span className="title">{album.title}</span>
                <span className="artist">{album.artist}</span>
                <span className="playcount">{album.plays.toLocaleString()} plays</span>
              </li>
            ))
          )}
        </ul>
      </section>

      <h3>SpVis - 2025</h3>
    </>
  );
};

export default AlbumPage;