import './tracks_style.css';
import trackImg from './assets/track_front_img.png';
import backgroundImg from './assets/black_and_grey_Background_2.PNG';

const TracksPage = () => {
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
          <input type="date" id="startDate" name="startDate"/>

          <label htmlFor="endDate">End Date:</label>
          <input type="date" id="endDate" name="endDate"/>

          <button type="button" className="filter_button">Filter</button>
        </div>

        {/* SONG LIST */}
        <ul id="songList" className="song-list">
          <li className="song">
            <span className="rank">1</span>
            <span className="title">Song Title One</span>
            <span className="artist">Artist Name</span>
          </li>

          <li className="song">
            <span className="rank">2</span>
            <span className="title">Song Title Two</span>
            <span className="artist">Artist Name</span>
          </li>

          <li className="song">
            <span className="rank">3</span>
            <span className="title">Song Title Three</span>
            <span className="artist">Artist Name</span>
          </li>
        </ul>
      </section>

      <h3>SpVis - 2025</h3>
    </>
  );
};

export default TracksPage;