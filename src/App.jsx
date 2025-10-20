import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [songs, setSongs] = useState([''])
  const [currentStep, setCurrentStep] = useState('input') // 'input', 'select', 'configure'
  const [searchResults, setSearchResults] = useState([])
  const [selectedUrl, setSelectedUrl] = useState('')
  const [linesPerSlide, setLinesPerSlide] = useState(4)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentSongIndex, setCurrentSongIndex] = useState(0)
  const [validSongs, setValidSongs] = useState([])
  const [selectedUrls, setSelectedUrls] = useState([])

  const handleSongChange = (index, value) => {
    const newSongs = [...songs]
    newSongs[index] = value
    setSongs(newSongs)

    // Add new input if this is the last one and it's not empty
    if (index === songs.length - 1 && value.trim() !== '') {
      setSongs([...newSongs, ''])
    }
  }

  const handleSearch = async () => {
    // Filter out empty songs
    const filteredSongs = songs.filter(song => song.trim() !== '')

    if (filteredSongs.length === 0) {
      setError('Please enter at least one song name')
      return
    }

    setError('')
    setLoading(true)
    setCurrentSongIndex(0)
    setValidSongs(filteredSongs)
    setSelectedUrls([])

    try {
      // Search for the first song
      const response = await axios.post('/api/search', {
        song_name: filteredSongs[0]
      })

      setSearchResults(response.data)
      setCurrentStep('select')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error searching for song')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectResult = async (url) => {
    const newSelectedUrls = [...selectedUrls, url]
    setSelectedUrls(newSelectedUrls)

    // Check if we have more songs to process
    const nextIndex = currentSongIndex + 1

    if (nextIndex < validSongs.length) {
      // Search for the next song
      setLoading(true)
      setError('')
      setCurrentSongIndex(nextIndex)

      try {
        const response = await axios.post('/api/search', {
          song_name: validSongs[nextIndex]
        })

        setSearchResults(response.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Error searching for song')
      } finally {
        setLoading(false)
      }
    } else {
      // All songs selected, move to configure
      setCurrentStep('configure')
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/generate', {
        urls: selectedUrls,
        lines_per_slide: linesPerSlide
      }, {
        responseType: 'blob'
      })

      // Create a download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'lyrics_presentation.pptx')
      document.body.appendChild(link)
      link.click()
      link.remove()

      // Reset to initial state
      setSongs([''])
      setCurrentStep('input')
      setSearchResults([])
      setSelectedUrls([])
      setValidSongs([])
      setCurrentSongIndex(0)
      setLinesPerSlide(4)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating presentation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="container">
        <h1 className="title">Lyrics to Slides</h1>

        {currentStep === 'input' && (
          <div className="input-section">
            {songs.map((song, index) => (
              <input
                key={index}
                type="text"
                className="song-input"
                placeholder="Enter song name (e.g., Yesterday by The Beatles)"
                value={song}
                onChange={(e) => handleSongChange(index, e.target.value)}
              />
            ))}

            {error && <div className="error">{error}</div>}

            <button
              className="primary-button"
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        )}

        {currentStep === 'select' && (
          <div className="select-section">
            <h2 className="subtitle">
              Select the correct song {currentSongIndex + 1} of {validSongs.length}
            </h2>
            <p className="song-name">"{validSongs[currentSongIndex]}"</p>

            <div className="results-list">
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  className="result-card"
                  onClick={() => handleSelectResult(result.link)}
                >
                  <h3 className="result-title">{result.title}</h3>
                  <p className="result-snippet">{result.snippet}</p>
                </div>
              ))}
            </div>

            <button
              className="secondary-button"
              onClick={() => setCurrentStep('input')}
            >
              Back
            </button>
          </div>
        )}

        {currentStep === 'configure' && (
          <div className="configure-section">
            <h2 className="subtitle">Configure your presentation</h2>

            <div className="config-card">
              <label className="config-label">
                Lines per slide:
                <input
                  type="number"
                  className="config-input"
                  min="1"
                  max="20"
                  value={linesPerSlide}
                  onChange={(e) => setLinesPerSlide(parseInt(e.target.value))}
                />
              </label>
            </div>

            {error && <div className="error">{error}</div>}

            <div className="button-group">
              <button
                className="secondary-button"
                onClick={() => setCurrentStep('select')}
              >
                Back
              </button>

              <button
                className="primary-button"
                onClick={handleGenerate}
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Generate Slides'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
