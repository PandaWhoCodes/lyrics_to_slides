import { useState, useEffect } from 'react'
import axios from 'axios'
import { AnimatePresence } from 'framer-motion'
import { Music, Search, CheckCircle, Sparkles, AlertCircle } from 'lucide-react'

// Components
import { Button } from './components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/Card'
import { Input, Textarea } from './components/ui/Input'
import { Badge } from './components/ui/Badge'
import { ProgressSteps } from './components/ui/ProgressSteps'
import { FadeIn } from './components/animations/FadeIn'
import { StaggeredList, StaggeredItem } from './components/animations/StaggeredList'
import { PageTransition } from './components/animations/PageTransition'
import { AnimatedModal } from './components/animations/AnimatedModal'
import { LoadingOverlay } from './components/animations/LoadingSpinner'

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
  const [currentStep, setCurrentStep] = useState('input')
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [error, setError] = useState('')
  const [currentSongIndex, setCurrentSongIndex] = useState(0)
  const [validSongs, setValidSongs] = useState([])
  const [selectedUrls, setSelectedUrls] = useState([])
  const [extractedSongs, setExtractedSongs] = useState([])
  const [songSearchHistory, setSongSearchHistory] = useState({})
  const [reselectingSongName, setReselectingSongName] = useState('')
  const [manualInputSongName, setManualInputSongName] = useState('')
  const [manualLyricsText, setManualLyricsText] = useState('')
  const [showManualInput, setShowManualInput] = useState(false)
  const [preloadedLyrics, setPreloadedLyrics] = useState({}) // Cache for preloaded lyrics
  const [preloadingUrls, setPreloadingUrls] = useState(new Set()) // Track URLs being preloaded

  // Cycle through loading messages
  useEffect(() => {
    if (loading) {
      const initialMessage = christianLoadingMessages[Math.floor(Math.random() * christianLoadingMessages.length)]
      setLoadingMessage(initialMessage)

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

    if (index === songs.length - 1 && value.trim() !== '') {
      setSongs([...newSongs, ''])
    }
  }

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (!loading && songs.some(s => s.trim() !== '')) {
        handleSearch()
      }
    }
  }

  const handleSearch = async () => {
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
    setPreloadedLyrics({}) // Clear preloaded cache
    setPreloadingUrls(new Set())
    setLoadingMessage(`Searching for all ${filteredSongs.length} songs...`)

    try {
      const response = await axios.post('/api/search-batch', {
        song_names: filteredSongs
      })

      const newHistory = {}
      response.data.forEach(songResult => {
        newHistory[songResult.song_name] = songResult.results
      })
      setSongSearchHistory(newHistory)

      setSearchResults(response.data[0].results)
      setCurrentStep('select')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error searching for songs')
    } finally {
      setLoading(false)
    }
  }

  // Preload lyrics in the background (fire and forget)
  const preloadLyrics = async (url, songName) => {
    // Skip if already preloaded or currently preloading
    if (preloadedLyrics[url] || preloadingUrls.has(url)) {
      return
    }

    // Mark as preloading
    setPreloadingUrls(prev => new Set([...prev, url]))

    try {
      const response = await axios.post('/api/extract-lyrics', {
        urls: [url]
      })

      if (response.data && response.data[0]) {
        setPreloadedLyrics(prev => ({
          ...prev,
          [url]: {
            ...response.data[0],
            songName: songName,
            originalUrl: url
          }
        }))
      }
    } catch (err) {
      console.log('Preload failed for:', url, err)
      // Silently fail - will be retried during final validation
    } finally {
      setPreloadingUrls(prev => {
        const newSet = new Set(prev)
        newSet.delete(url)
        return newSet
      })
    }
  }

  const handleSelectResult = async (url) => {
    const currentSong = validSongs[currentSongIndex]
    const newSelectedUrls = [...selectedUrls, { song: currentSong, url }]
    setSelectedUrls(newSelectedUrls)

    // Start preloading lyrics for the selected URL in the background
    preloadLyrics(url, currentSong)

    const nextIndex = currentSongIndex + 1

    if (nextIndex < validSongs.length) {
      setCurrentSongIndex(nextIndex)
      setSearchResults(songSearchHistory[validSongs[nextIndex]])
      setCurrentStep('select')
    } else {
      // All songs selected - use preloaded lyrics where available
      await validateLyricsWithPreloaded(newSelectedUrls)
    }
  }

  const handleReselect = (songName) => {
    setError('')
    const searchHistory = songSearchHistory[songName]
    if (searchHistory) {
      setSearchResults(searchHistory)
      setReselectingSongName(songName)
      setCurrentStep('reselect')
      setCurrentSongIndex(validSongs.indexOf(songName))
    }
  }

  const handleRemoveSong = (songName) => {
    setExtractedSongs(extractedSongs.filter(s => s.songName !== songName))
    setSelectedUrls(selectedUrls.filter(s => s.song !== songName))
  }

  const handleManualInput = (songName) => {
    setManualInputSongName(songName)
    setManualLyricsText('')
    setShowManualInput(true)
  }

  const handleSubmitManualLyrics = async () => {
    if (!manualLyricsText.trim()) {
      setError('Please enter lyrics')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/manual-lyrics', {
        title: manualInputSongName,
        lyrics: manualLyricsText,
        clean_formatting: true
      })

      if (response.data.success) {
        const existingIndex = extractedSongs.findIndex(s => s.songName === manualInputSongName)

        const manualEntry = {
          success: true,
          title: response.data.title,
          lyrics: response.data.lyrics,
          songName: manualInputSongName,
          originalUrl: 'manual-input',
          url: 'manual-input'
        }

        if (existingIndex >= 0) {
          const updatedSongs = [...extractedSongs]
          updatedSongs[existingIndex] = manualEntry
          setExtractedSongs(updatedSongs)
        } else {
          setExtractedSongs([...extractedSongs, manualEntry])
        }

        const urlIndex = selectedUrls.findIndex(s => s.song === manualInputSongName)
        if (urlIndex >= 0) {
          const updatedUrls = [...selectedUrls]
          updatedUrls[urlIndex] = { song: manualInputSongName, url: 'manual-input' }
          setSelectedUrls(updatedUrls)
        } else {
          setSelectedUrls([...selectedUrls, { song: manualInputSongName, url: 'manual-input' }])
        }

        setShowManualInput(false)
        setManualInputSongName('')
        setManualLyricsText('')
        setError('')

        // If in select step, advance to next song or proceed to extraction
        if (currentStep === 'select') {
          if (currentSongIndex < validSongs.length - 1) {
            const nextIndex = currentSongIndex + 1
            setCurrentSongIndex(nextIndex)
            if (songSearchHistory[validSongs[nextIndex]]) {
              setSearchResults(songSearchHistory[validSongs[nextIndex]])
            }
          } else {
            // All songs done, proceed to review with what we have
            // Need to extract lyrics for songs that have URLs selected
            const songsWithUrls = selectedUrls.filter(s => s.url !== 'manual-input')
            if (songsWithUrls.length > 0) {
              await validateLyrics(songsWithUrls)
            } else {
              // All songs were manual, go to review
              setCurrentStep('review')
            }
          }
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing manual lyrics')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchAllSites = async (songName) => {
    setLoading(true)
    setError('')
    setLoadingMessage(`Searching all sites for "${songName}"...`)

    try {
      const response = await axios.post('/api/search-all', {
        song_name: songName
      })

      if (response.data && response.data.length > 0) {
        setSearchResults(response.data)
        // Update cache with expanded results
        setSongSearchHistory(prev => ({
          ...prev,
          [songName]: response.data
        }))
      } else {
        setError('No additional results found. Try entering lyrics manually.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error searching all sites')
    } finally {
      setLoading(false)
    }
  }

  const handleReselectResult = async (url) => {
    const songName = reselectingSongName || validSongs[currentSongIndex]

    if (loading) return

    setLoading(true)
    setError('')

    try {
      const response = await axios.post('/api/extract-lyrics', {
        urls: [url]
      })

      const existingUrlIndex = selectedUrls.findIndex(s => s.song === songName)

      let updatedUrls
      if (existingUrlIndex >= 0) {
        updatedUrls = [...selectedUrls]
        updatedUrls[existingUrlIndex] = { song: songName, url }
      } else {
        updatedUrls = [...selectedUrls, { song: songName, url }]
      }
      setSelectedUrls(updatedUrls)

      const existingExtractedIndex = extractedSongs.findIndex(s => s.songName === songName)

      let updatedExtracted
      if (existingExtractedIndex >= 0) {
        updatedExtracted = [...extractedSongs]
        updatedExtracted[existingExtractedIndex] = {
          ...response.data[0],
          songName: songName,
          originalUrl: url
        }
      } else {
        updatedExtracted = [...extractedSongs, {
          ...response.data[0],
          songName: songName,
          originalUrl: url
        }]
      }

      setExtractedSongs(updatedExtracted)
      setReselectingSongName('')
      setError('')
      setCurrentStep('review')
    } catch (err) {
      setError(err.response?.data?.detail || 'Error validating lyrics')
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

  // Optimized validation that uses preloaded lyrics
  const validateLyricsWithPreloaded = async (songUrls) => {
    setLoading(true)
    setError('')
    setLoadingMessage('Finalizing lyrics extraction...')

    try {
      const results = []
      const urlsToFetch = []
      const urlsToFetchIndices = []

      // Check which URLs already have preloaded lyrics
      songUrls.forEach((item, index) => {
        if (item.url === 'manual-input') {
          // Skip manual inputs - they're already in extractedSongs
          const existing = extractedSongs.find(s => s.songName === item.song)
          if (existing) {
            results[index] = existing
          }
        } else if (preloadedLyrics[item.url]) {
          // Use preloaded lyrics
          results[index] = preloadedLyrics[item.url]
        } else {
          // Need to fetch this one
          urlsToFetch.push(item.url)
          urlsToFetchIndices.push({ index, song: item.song, url: item.url })
        }
      })

      // Fetch any URLs that weren't preloaded
      if (urlsToFetch.length > 0) {
        setLoadingMessage(`Extracting ${urlsToFetch.length} remaining song${urlsToFetch.length > 1 ? 's' : ''}...`)

        const response = await axios.post('/api/extract-lyrics', {
          urls: urlsToFetch
        })

        // Merge fetched results
        response.data.forEach((result, fetchIndex) => {
          const { index, song, url } = urlsToFetchIndices[fetchIndex]
          results[index] = {
            ...result,
            songName: song,
            originalUrl: url
          }
        })
      }

      // Filter out undefined entries and set results
      const finalResults = results.filter(r => r !== undefined)
      setExtractedSongs(finalResults)
      setCurrentStep('review')

      // Clear preloaded cache
      setPreloadedLyrics({})
    } catch (err) {
      setError(err.response?.data?.detail || 'Error validating lyrics')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    setLoading(true)
    setError('')

    const successfulSongs = extractedSongs.filter(s => s.success)

    if (successfulSongs.length === 0) {
      setError('No valid songs to generate presentation')
      setLoading(false)
      return
    }

    try {
      const response = await axios.post('/api/generate', {
        urls: successfulSongs.map(s => s.originalUrl),
        validated_songs: successfulSongs.map(s => ({
          title: s.title,
          lyrics: s.lyrics
        }))
      }, {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'lyrics_presentation.pptx')
      document.body.appendChild(link)
      link.click()
      link.remove()

      // Reset
      setSongs([''])
      setCurrentStep('input')
      setSearchResults([])
      setSelectedUrls([])
      setValidSongs([])
      setCurrentSongIndex(0)
      setLinesPerSlide(4)
      setExtractedSongs([])
      setSongSearchHistory({})
      setPreloadedLyrics({})
      setPreloadingUrls(new Set())
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating presentation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full">
      {/* Loading Overlay */}
      <AnimatePresence>
        {loading && <LoadingOverlay message={loadingMessage} />}
      </AnimatePresence>

      {/* Main Container */}
      <FadeIn>
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-12">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-3 mb-3">
              <Music className="text-blue-500" size={32} />
              <h1 className="text-4xl font-bold text-gray-900">Lyrics to Slides</h1>
              <Sparkles className="text-yellow-500" size={32} />
            </div>
            <p className="text-gray-600">Create beautiful worship presentations in minutes</p>
          </div>

          {/* Progress Steps */}
          {currentStep !== 'input' && currentStep !== 'reselect' && (
            <ProgressSteps currentStep={currentStep} />
          )}

          {/* Error Message */}
          {error && (
            <FadeIn>
              <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl flex items-start gap-3">
                <AlertCircle className="text-red-500 flex-shrink-0" size={20} />
                <p className="text-red-700 text-sm font-medium">{error}</p>
              </div>
            </FadeIn>
          )}

          {/* Step Content */}
          <PageTransition pageKey={currentStep}>
            {/* INPUT STEP */}
            {currentStep === 'input' && (
              <div className="space-y-4">
                <FadeIn delay={0.1}>
                  <div className="space-y-3">
                    {songs.map((song, index) => (
                      <FadeIn key={index} delay={index * 0.05}>
                        <Input
                          type="text"
                          placeholder="Enter song name (e.g., Amazing Grace)"
                          value={song}
                          onChange={(e) => handleSongChange(index, e.target.value)}
                          onKeyDown={handleKeyDown}
                        />
                      </FadeIn>
                    ))}
                  </div>
                </FadeIn>

                <FadeIn delay={0.3}>
                  <Button
                    onClick={handleSearch}
                    disabled={loading || songs.every(s => s.trim() === '')}
                    className="w-full"
                    size="lg"
                  >
                    <Search size={20} />
                    Search for Songs
                    <span className="text-xs opacity-80 ml-2 px-2 py-1 bg-white/20 rounded">
                      Ctrl + Enter
                    </span>
                  </Button>
                </FadeIn>
              </div>
            )}

            {/* SELECT STEP */}
            {currentStep === 'select' && (
              <div>
                <div className="text-center mb-6">
                  <Badge variant="info" className="text-base px-4 py-2">
                    Song {currentSongIndex + 1} of {validSongs.length}
                  </Badge>
                  <h2 className="text-2xl font-semibold text-gray-900 mt-3">
                    Select source for "{validSongs[currentSongIndex]}"
                  </h2>
                  {/* Preloading indicator */}
                  {(preloadingUrls.size > 0 || Object.keys(preloadedLyrics).length > 0) && (
                    <p className="text-sm text-green-600 mt-2 flex items-center justify-center gap-2">
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                      {preloadingUrls.size > 0
                        ? `Extracting lyrics in background (${Object.keys(preloadedLyrics).length} ready)...`
                        : `${Object.keys(preloadedLyrics).length} song${Object.keys(preloadedLyrics).length !== 1 ? 's' : ''} ready`
                      }
                    </p>
                  )}
                </div>

                <StaggeredList className="space-y-3">
                  {searchResults.map((result, index) => (
                    <StaggeredItem key={index} onClick={() => !loading && handleSelectResult(result.link)}>
                      <Card hover={!loading} className={loading ? 'opacity-50 cursor-not-allowed' : ''}>
                        <CardHeader>
                          <CardTitle>{result.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="line-clamp-2">{result.snippet}</p>
                        </CardContent>
                      </Card>
                    </StaggeredItem>
                  ))}
                </StaggeredList>

                {/* Alternative options when search results aren't good enough */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <p className="text-gray-500 text-sm mb-3">Not finding what you need?</p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => handleSearchAllSites(validSongs[currentSongIndex])}
                      disabled={loading}
                    >
                      Search All Sites
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => handleManualInput(validSongs[currentSongIndex])}
                      disabled={loading}
                    >
                      Enter Manually
                    </Button>
                  </div>
                </div>

                <div className="mt-6">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setError('')
                      if (currentSongIndex > 0) {
                        // Go to previous song
                        const prevIndex = currentSongIndex - 1
                        setCurrentSongIndex(prevIndex)
                        setSearchResults(songSearchHistory[validSongs[prevIndex]] || [])
                      } else {
                        // At first song, go back to input
                        setCurrentStep('input')
                      }
                    }}
                    disabled={loading}
                  >
                    Back
                  </Button>
                </div>
              </div>
            )}

            {/* REVIEW STEP */}
            {currentStep === 'review' && (
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
                  Review Extracted Lyrics
                </h2>

                <StaggeredList className="space-y-4">
                  {extractedSongs.map((song, index) => (
                    <StaggeredItem key={index}>
                      <Card
                        hover={false}
                        className={`${
                          song.success
                            ? 'border-green-300 bg-gradient-to-br from-white to-green-50'
                            : 'border-red-300 bg-gradient-to-br from-white to-red-50'
                        }`}
                      >
                        <div className="flex items-start gap-4">
                          <div
                            className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                              song.success ? 'bg-green-100' : 'bg-red-100'
                            }`}
                          >
                            {song.success ? (
                              <CheckCircle className="text-green-600" size={24} />
                            ) : (
                              <AlertCircle className="text-red-600" size={24} />
                            )}
                          </div>

                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                              {song.success ? song.title : song.songName}
                            </h3>

                            {song.success ? (
                              <div>
                                <p className="text-green-700 font-medium flex items-center gap-2 mb-3">
                                  <CheckCircle size={16} />
                                  Lyrics extracted successfully
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => {
                                      setManualInputSongName(song.songName)
                                      setManualLyricsText(song.lyrics || '')
                                      setShowManualInput(true)
                                    }}
                                  >
                                    Edit Lyrics
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleReselect(song.songName)}
                                  >
                                    Try Different Source
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              <div>
                                <p className="text-red-700 mb-4">{song.error || 'No lyrics found'}</p>
                                <div className="flex flex-wrap gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => handleReselect(song.songName)}
                                  >
                                    Try Different Source
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleManualInput(song.songName)}
                                  >
                                    Enter Manually
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="danger"
                                    onClick={() => handleRemoveSong(song.songName)}
                                  >
                                    Remove Song
                                  </Button>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </Card>
                    </StaggeredItem>
                  ))}
                </StaggeredList>

                <div className="mt-8 flex gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setCurrentStep('input')
                      setExtractedSongs([])
                    }}
                  >
                    Start Over
                  </Button>

                  {extractedSongs.some(s => s.success) && (
                    <Button
                      className="flex-1"
                      onClick={handleGenerate}
                      disabled={loading}
                    >
                      <Sparkles size={20} />
                      Generate Presentation ({extractedSongs.filter(s => s.success).length} Song
                      {extractedSongs.filter(s => s.success).length !== 1 ? 's' : ''})
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* RESELECT STEP */}
            {currentStep === 'reselect' && (
              <div>
                <div className="text-center mb-6">
                  <h2 className="text-2xl font-semibold text-gray-900">
                    Choose different source for "{reselectingSongName || validSongs[currentSongIndex]}"
                  </h2>
                  <p className="text-gray-600 mt-2">Select a different source that might have better lyrics</p>
                </div>

                <StaggeredList className="space-y-3">
                  {searchResults.map((result, index) => (
                    <StaggeredItem key={index} onClick={() => !loading && handleReselectResult(result.link)}>
                      <Card hover={!loading} className={loading ? 'opacity-50 cursor-not-allowed' : ''}>
                        <CardHeader>
                          <CardTitle>{result.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="line-clamp-2">{result.snippet}</p>
                        </CardContent>
                      </Card>
                    </StaggeredItem>
                  ))}
                </StaggeredList>

                <div className="mt-6">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setError('')
                      setCurrentStep('review')
                    }}
                    disabled={loading}
                  >
                    Back to Review
                  </Button>
                </div>
              </div>
            )}

          </PageTransition>
        </div>
      </FadeIn>

      {/* Manual Lyrics Input Modal */}
      <AnimatedModal
        isOpen={showManualInput}
        onClose={() => setShowManualInput(false)}
        title="Enter Lyrics Manually"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setShowManualInput(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitManualLyrics}
              disabled={loading || !manualLyricsText.trim()}
            >
              Add Lyrics
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Paste lyrics for: <strong className="text-gray-900">{manualInputSongName}</strong>
          </p>

          <Textarea
            placeholder="Paste the song lyrics here...

You can include section markers like [Verse 1], [Chorus], etc.
They will be automatically cleaned for the presentation."
            value={manualLyricsText}
            onChange={(e) => setManualLyricsText(e.target.value)}
            rows={15}
          />

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-semibold text-blue-900 mb-2">💡 Tips:</p>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>The lyrics will be automatically cleaned of metadata</li>
              <li>Section markers like [Verse], [Chorus] will be removed</li>
              <li>Ad-libs like (yeah), (oh) will be removed</li>
              <li>The lyrics will be grouped into slides automatically</li>
            </ul>
          </div>
        </div>
      </AnimatedModal>
    </div>
  )
}

export default App
