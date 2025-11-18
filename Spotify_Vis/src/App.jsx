import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploadStatus, setUploadStatus] = useState('')
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)


  useEffect(() => {
    fetch('/api/time').then(res => res.json()).then(data => {
      setCurrentTime(data.time);
    });
  }, []);

  const handleFolderSelect = (event) => {
    const files = Array.from(event.target.files);
    const jsonFiles = files.filter(file=> file.name.toLowerCase().endsWith('.json'));

    setSelectedFiles(jsonFiles);
    setUploadStatus(`Selected ${jsonFiles.length} JSON files`);
    setAnalysisResult(null);
  }

  const handleAnalyseFiles = async (event) => {
    event.preventDefault();

    if (selectedFiles.length === 0){
      setUploadStatus('Please select a folder containing JSON files');
      return;
    }

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });

    try {
      setIsProcessing(true);
      setUploadStatus('Analyzing Files...');

      const response = await fetch('/api/analyze-spotify', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if(response.ok) {
        setUploadStatus(`Successfully analyzed ${result.processedFiles.length} files`);
        setAnalysisResult(result);

        setSelectedFiles([]);
        const fileInput = document.getElementById('folderInput');
        if(fileInput) fileInput.value = '';
      } else {
        setUploadStatus(`Analysis failed: ${result.error}`);
      }
    } catch (error){
      setUploadStatus('Analysis error: ' + error.message);
    }finally{
      setIsProcessing(false);
    }
  }

  return (
    <>
      <h1>Spotify Visualization Tool</h1>
      <div className="card">
      {/* File Upload Section*/}
        <div className="upload-section">
          <h3>Upload JSON Files</h3>
          <form onSubmit={handleAnalyseFiles}>
            <label htmlFor='folderInput'>Select a the Folder provided by Spotify </label>

            <input 
              type="file"
              id="folderInput"
              webkitdirectory="true"
              directory="true"
              multiple
              onChange={handleFolderSelect}
              accept='.json' 
            />
            <br /><br />
            <button type='submit' disabled={isProcessing}>
              {isProcessing ? 'Analyzing...' : 'Analyze Files'}
            </button>
          </form>

          {/* Display analysis results with song count */}
          {analysisResult && (
            <div className="/api/analysis-spotify">
              <h4>Analysis Results</h4>
              <p><strong>Total Songs Processed:</strong> {analysisResult.combinedData.totalSongs?.toLocaleString()}</p>
              <p><strong>Total Records:</strong> {analysisResult.combinedData.totalRecords?.toLocaleString()}</p>
              <p><strong>Files Analyzed:</strong> {analysisResult.processedFiles.length}</p>

              {/* You can add more analysis results here */}
              {analysisResult.analysis && (
                <div className="detailed-stats">
                  <p><strong>Unique Artists:</strong> {analysisResult.analysis.unique_artists?.toLocaleString()}</p>
                  <p><strong>Unique Tracks:</strong> {analysisResult.analysis.unique_tracks?.toLocaleString()}</p>
                  <p><strong>Unique Albums:</strong> {analysisResult.analysis.unique_albums?.toLocaleString()}</p>
                </div>
              )}
            </div>
          )}

          {uploadStatus && (
            <div className={`status ${isProcessing ? 'processing': ''}`}>
              {uploadStatus}
            </div>
          )}
        </div>
      </div>
      <div className='How to'>
        <h2>Here is how you can get your extended listening history from Spotify</h2>
        <p>First you will need to follow this link: <a href='https://open.spotify.com/' target='_blank'>Spotify login</a> and login to your spotify account.</p>
        <br></br>
        <p>You then click on your profile picture and go to your account. The page you should end up on looks like this:</p>
        <img src='../spVis_how_to.png' alt='account_page' height={900} width={1200}></img>
        <p>Navigate to the bottom of the page and click on the Account Privacy tab. You will then go down to the Download Your Data section.</p>
        <img src='../spVis_download.png' alt='download_page' height={900} width={1200}></img>
        <p>Make sure you only have the extended listening data box checked and request your data from Spotify. It can take a couple of weeks to receive but when you do you will get an email with the folder of
          the JSON files you will need to upload. 
        </p>

      </div>
    </>
  )
}

export default App
