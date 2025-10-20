import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

// Christian music-themed loading messages
const christianLoadingMessages = [
  "🎵 Tuning the heavenly harps...",
  "✨ Gathering lyrics from the choir loft...",
  "🙏 Saying a quick prayer for good lyrics...",
  "🎼 Checking the hymnal...",
  "⛪ Consulting the worship team...",
  "📖 Searching the Psalms for inspiration...",
  "🎹 Warming up the church organ...",
  "🕊️ Waiting for divine inspiration...",
  "🎺 Summoning the angelic brass section...",
  "✝️ Blessing the lyrics...",
  "🎻 Tuning the strings of praise...",
  "🙌 Raising holy hands in preparation...",
  "💫 Aligning with the heavenly chorus...",
  "🎵 Harmonizing with the saints...",
  "📜 Unrolling the ancient scrolls...",
  "🔔 Ringing the church bells...",
  "🎤 Testing the worship microphones...",
  "🌟 Following the star to the lyrics...",
  "🎸 Strumming the chords of faith...",
  "🥁 Setting the rhythm of redemption...",
  "🎶 Composing a symphony of grace...",
  "🕯️ Lighting the candles of worship...",
  "📻 Tuning into Heaven's FM...",
  "🎧 Adjusting the holy headphones...",
  "🌈 Painting lyrics with covenant colors...",
  "⚡ Channeling worship energy...",
  "🏛️ Echoing through the sanctuary...",
  "💝 Wrapping lyrics in love...",
  "🗣️ Practicing the hallelujahs...",
  "🌅 Waiting for the morning worship..."
]

function App() {
  const [songs, setSongs] = useState([''])
  const [currentStep, setCurrentStep] = useState('input') // 'input', 'select', 'review', 'configure', 'reselect'
  const [searchResults, setSearchResults] = useState([])
  const [selectedUrl, setSelectedUrl] = useState('')
  const [linesPerSlide, setLinesPerSlide] = useState(4)
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [error, setError] = useState('')
  const [currentSongIndex, setCurrentSongIndex] = useState(0)
  const [validSongs, setValidSongs] = useState([])
  const [selectedUrls, setSelectedUrls] = useState([])
  const [extractedSongs, setExtractedSongs] = useState([])
  const [songSearchHistory, setSongSearchHistory] = useState({}) // Store search results for reselection
  const [reselectingSongName, setReselectingSongName] = useState('') // Track which song is being reselected

  // Cycle through loading messages
  useEffect(() => {
    if (loading) {
      // Set initial message
      const initialMessage = christianLoadingMessages[Math.floor(Math.random() * christianLoadingMessages.length)]
      setLoadingMessage(initialMessage)

      // Cycle through messages every 2 seconds
      const interval = setInterval(() => {
        const randomMessage = christianLoadingMessages[Math.floor(Math.random() * christianLoadingMessages.length)]
        setLoadingMessage(randomMessage)
      }, 2000)

      return () => clearInterval(interval)
    }
  }, [loading])

  const handleSongChange = (index, value) => {
    const newSongs = [...songs]
    newSongs[index] = value
    setSongs(newSongs)

    // Add new input if this is the last one and it's not empty
    if (index === songs.length - 1 && value.trim() !== '') {
      setSongs([...newSongs, ''])
    }
  }

  const handleKeyDown = (e) => {
    // Check for Ctrl+Enter (Windows/Linux) or Cmd+Enter (Mac)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      // Only submit if not already loading and there are valid songs
      if (!loading && songs.some(s => s.trim() !== '')) {
        handleSearch()
      }
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

      // Store search results for potential reselection
      const newHistory = { ...songSearchHistory }
      newHistory[filteredSongs[0]] = response.data
      setSongSearchHistory(newHistory)

      setSearchResults(response.data)
      setCurrentStep('select')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error searching for song')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectResult = async (url) => {
    const newSelectedUrls = [...selectedUrls, { song: validSongs[currentSongIndex], url }]
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

        // Store search results for potential reselection
        const newHistory = { ...songSearchHistory }
        newHistory[validSongs[nextIndex]] = response.data
        setSongSearchHistory(newHistory)

        setSearchResults(response.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Error searching for song')
      } finally {
        setLoading(false)
      }
    } else {
      // All songs selected, validate lyrics extraction
      await validateLyrics(newSelectedUrls)
    }
  }

  const handleReselect = (songName) => {
    // Clear any existing errors
    setError('')

    // Find the search results for this song
    const searchHistory = songSearchHistory[songName]
    if (searchHistory) {
      setSearchResults(searchHistory)
      setReselectingSongName(songName)
      setCurrentStep('reselect')
      setCurrentSongIndex(validSongs.indexOf(songName))
    }
  }

  const handleRemoveSong = (songName) => {
    // Remove song from extracted songs
    setExtractedSongs(extractedSongs.filter(s => s.songName !== songName))
    // Also remove from selectedUrls to prevent duplicates
    setSelectedUrls(selectedUrls.filter(s => s.song !== songName))
  }

  const handleReselectResult = async (url) => {
    const songName = reselectingSongName || validSongs[currentSongIndex]

    // Prevent duplicate clicks
    if (loading) return

    // Re-validate just this song
    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/extract-lyrics', {
        urls: [url]
      })

      // Check if this song already exists in selectedUrls
      const existingUrlIndex = selectedUrls.findIndex(s => s.song === songName)

      // Update or add the URL for this song
      let updatedUrls
      if (existingUrlIndex >= 0) {
        // Update existing
        updatedUrls = [...selectedUrls]
        updatedUrls[existingUrlIndex] = { song: songName, url }
      } else {
        // Add new (shouldn't happen in reselect, but just in case)
        updatedUrls = [...selectedUrls, { song: songName, url }]
      }
      setSelectedUrls(updatedUrls)

      // Check if song already exists in extractedSongs
      const existingExtractedIndex = extractedSongs.findIndex(s => s.songName === songName)

      // Update or add the extraction result for this song
      let updatedExtracted
      if (existingExtractedIndex >= 0) {
        // Update existing
        updatedExtracted = [...extractedSongs]
        updatedExtracted[existingExtractedIndex] = {
          ...response.data[0],
          songName: songName,
          originalUrl: url
        }
      } else {
        // Add new
        updatedExtracted = [...extractedSongs, {
          ...response.data[0],
          songName: songName,
          originalUrl: url
        }]
      }

      setExtractedSongs(updatedExtracted)
      setReselectingSongName('')
      setError('') // Clear any errors
      setCurrentStep('review')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error validating lyrics')
      // Don't go back to review on error, stay on reselect
    } finally {
      setLoading(false)
    }
  }

  const validateLyrics = async (songUrls) => {
    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/extract-lyrics', {
        urls: songUrls.map(s => s.url)
      })

      // Map extraction results back to songs
      const results = response.data.map((result, index) => ({
        ...result,
        songName: songUrls[index].song,
        originalUrl: songUrls[index].url
      }))

      setExtractedSongs(results)
      setCurrentStep('review')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error validating lyrics')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError('')

    // Filter only successful songs
    const successfulSongs = extractedSongs.filter(s => s.success)

    if (successfulSongs.length === 0) {
      setError('No valid songs to generate presentation')
      setLoading(false)
      return
    }

    try {
      const response = await axios.post('/api/generate', {
        urls: successfulSongs.map(s => s.originalUrl),
        lines_per_slide: linesPerSlide,
        validated_songs: successfulSongs.map(s => ({
          title: s.title,
          lyrics: s.lyrics
        }))
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
      setExtractedSongs([])
      setSongSearchHistory({})
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating presentation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="loading-spinner"></div>
            <p className="loading-message">{loadingMessage}</p>
          </div>
        </div>
      )}

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
                onKeyDown={handleKeyDown}
              />
            ))}

            {error && <div className="error">{error}</div>}

            <button
              className="primary-button"
              onClick={handleSearch}
              disabled={loading || songs.every(s => s.trim() === '')}
              title="Press Ctrl+Enter (or Cmd+Enter on Mac) to submit"
            >
              Search
              <span className="keyboard-hint">Ctrl + Enter</span>
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
                  className={`result-card ${loading ? 'disabled' : ''}`}
                  onClick={() => !loading && handleSelectResult(result.link)}
                >
                  <h3 className="result-title">{result.title}</h3>
                  <p className="result-snippet">{result.snippet}</p>
                </div>
              ))}
            </div>

            <button
              className="secondary-button"
              onClick={() => {
                setError('')
                setCurrentStep('input')
              }}
              disabled={loading}
            >
              Back
            </button>
          </div>
        )}

        {currentStep === 'review' && (
          <div className="review-section">
            <h2 className="subtitle">Review Extracted Lyrics</h2>

            {extractedSongs.length > 0 && (
              <div className="review-list">
                {extractedSongs.map((song, index) => (
                  <div
                    key={index}
                    className={`review-card ${song.success ? 'success' : 'failed'}`}
                  >
                    <div className="review-header">
                      <span className="review-status">
                        {song.success ? '✓' : '✗'}
                      </span>
                      <h3 className="review-title">
                        {song.success ? song.title : song.songName}
                      </h3>
                    </div>

                    {!song.success && (
                      <div className="review-error">
                        <p className="error-message">{song.error || 'No lyrics found'}</p>
                        <div className="review-actions">
                          <button
                            className="action-button reselect"
                            onClick={() => handleReselect(song.songName)}
                          >
                            Try Different Source
                          </button>
                          <button
                            className="action-button remove"
                            onClick={() => handleRemoveSong(song.songName)}
                          >
                            Remove Song
                          </button>
                        </div>
                      </div>
                    )}

                    {song.success && (
                      <div className="review-success">
                        <p className="success-message">✓ Lyrics extracted successfully</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {error && <div className="error">{error}</div>}

            <div className="button-group">
              <button
                className="secondary-button"
                onClick={() => {
                  setCurrentStep('input')
                  setExtractedSongs([])
                }}
              >
                Start Over
              </button>

              {extractedSongs.some(s => s.success) && (
                <button
                  className="primary-button"
                  onClick={() => setCurrentStep('configure')}
                >
                  Continue with {extractedSongs.filter(s => s.success).length} Song{extractedSongs.filter(s => s.success).length !== 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>
        )}

        {currentStep === 'reselect' && (
          <div className="select-section">
            <h2 className="subtitle">
              Reselect source for "{reselectingSongName || validSongs[currentSongIndex]}"
            </h2>
            <p className="info-text">Choose a different source that might have better lyrics:</p>

            <div className="results-list">
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  className={`result-card ${loading ? 'disabled' : ''}`}
                  onClick={() => !loading && handleReselectResult(result.link)}
                >
                  <h3 className="result-title">{result.title}</h3>
                  <p className="result-snippet">{result.snippet}</p>
                </div>
              ))}
            </div>

            {error && <div className="error">{error}</div>}

            <button
              className="secondary-button"
              onClick={() => {
                setError('')
                setCurrentStep('review')
              }}
              disabled={loading}
            >
              Back to Review
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
                Generate Slides
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
