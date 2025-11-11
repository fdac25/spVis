import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
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
    SetAnalysisResult(null);
  }

  const handleAnalyseFiles = async (event) => {
    event.PreventDefault();

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

      const response = await fetch('api/analyze-files', {
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
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Spotify Visualization Tool</h1>
      <div className="card">
      {/* File Upload Section*/}
        <div className="upload-section">
          <h3>Upload JSON Files</h3>
          <form onSubmit={handleAnalyseFiles}>
            <label htmlFor='folderInput'>Select a the Folder provided by Spotify</label>

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
            <button type='submit' disable={isProcessing}>
              {isProcessing ? 'Analyzing...' : 'Analyze Files'}
            </button>
          </form>

          {uploadStatus && (
            <div className={`status ${isProcessing ? 'processing': ''}`}>
              {uploadStatus}
            </div>
          )}
        </div>

        <form action="/upload" method="post" enctype="multipart/form-data">
          <label for="myFile">Select a File:</label>
          <input type="file" name="myFile" id="myFile" accept=".json"></input>
          <br></br><br></br>
          <button type="submit">Upload File</button>
        </form>
        <p>
          Edit <code>src/App.jsx</code> and save to test HMR
        </p>
        <p>The Current time is {new Date(currentTime * 1000).toLocaleString()}.</p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
