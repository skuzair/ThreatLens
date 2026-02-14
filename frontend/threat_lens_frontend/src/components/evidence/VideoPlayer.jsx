import { useRef, useState, useEffect } from 'react'

export default function VideoPlayer({ videoUrl, evidenceName, timestamp }) {
  const videoRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [playbackRate, setPlaybackRate] = useState(1)
  const [error, setError] = useState(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const updateTime = () => setCurrentTime(video.currentTime)
    const updateDuration = () => setDuration(video.duration)
    const handleEnded = () => setIsPlaying(false)
    const handleError = () => setError('Failed to load video. Video may be unavailable or URL expired.')

    video.addEventListener('timeupdate', updateTime)
    video.addEventListener('loadedmetadata', updateDuration)
    video.addEventListener('ended', handleEnded)
    video.addEventListener('error', handleError)

    return () => {
      video.removeEventListener('timeupdate', updateTime)
      video.removeEventListener('loadedmetadata', updateDuration)
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('error', handleError)
    }
  }, [])

  const togglePlay = () => {
    const video = videoRef.current
    if (video.paused) {
      video.play()
      setIsPlaying(true)
    } else {
      video.pause()
      setIsPlaying(false)
    }
  }

  const handleSeek = (e) => {
    const video = videoRef.current
    const newTime = parseFloat(e.target.value)
    video.currentTime = newTime
    setCurrentTime(newTime)
  }

  const handleVolumeChange = (e) => {
    const video = videoRef.current
    const newVolume = parseFloat(e.target.value)
    video.volume = newVolume
    setVolume(newVolume)
  }

  const handlePlaybackRateChange = (rate) => {
    const video = videoRef.current
    video.playbackRate = rate
    setPlaybackRate(rate)
  }

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const downloadVideo = () => {
    const link = document.createElement('a')
    link.href = videoUrl
    link.download = evidenceName || 'evidence_video.mp4'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div style={{
      background: '#1a2233',
      borderRadius: '8px',
      padding: '16px',
      border: '1px solid #1e2d45'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px'
      }}>
        <div>
          <h3 style={{ 
            color: '#e2e8f0', 
            fontSize: '16px',
            fontWeight: '600',
            marginBottom: '4px'
          }}>
            🎥 Video Evidence
          </h3>
          <p style={{ 
            color: '#64748b', 
            fontSize: '12px',
            margin: 0
          }}>
            {evidenceName || 'Security Camera Recording'}
          </p>
        </div>
        <div style={{
          color: '#64748b',
          fontSize: '11px',
          background: '#0a0e1a',
          padding: '4px 8px',
          borderRadius: '4px'
        }}>
          🕐 {timestamp ? new Date(timestamp).toLocaleString() : 'Unknown time'}
        </div>
      </div>

      {error ? (
        <div style={{
          background: '#450a0a',
          border: '1px solid #7f1d1d',
          borderRadius: '4px',
          padding: '20px',
          textAlign: 'center',
          color: '#ef4444',
          fontSize: '14px'
        }}>
          ⚠️ {error}
        </div>
      ) : (
        <>
          {/* Video Element */}
          <div style={{
            position: 'relative',
            background: '#000',
            borderRadius: '4px',
            overflow: 'hidden',
            marginBottom: '12px'
          }}>
            <video
              ref={videoRef}
              style={{
                width: '100%',
                height: 'auto',
                display: 'block'
              }}
              src={videoUrl}
            >
              Your browser does not support the video tag.
            </video>
            
            {!isPlaying && (
              <button
                onClick={togglePlay}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'rgba(255, 255, 255, 0.9)',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 1)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)'}
              >
                ▶️
              </button>
            )}
          </div>

          {/* Controls */}
          <div style={{
            background: '#0a0e1a',
            borderRadius: '4px',
            padding: '12px'
          }}>
            {/* Progress Bar */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px'
            }}>
              <span style={{ color: '#64748b', fontSize: '11px', minWidth: '40px' }}>
                {formatTime(currentTime)}
              </span>
              <input
                type="range"
                min="0"
                max={duration || 0}
                value={currentTime}
                onChange={handleSeek}
                style={{
                  flex: 1,
                  height: '4px',
                  borderRadius: '2px',
                  outline: 'none',
                  cursor: 'pointer',
                  background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #1e2d45 ${(currentTime / duration) * 100}%, #1e2d45 100%)`
                }}
              />
              <span style={{ color: '#64748b', fontSize: '11px', minWidth: '40px', textAlign: 'right' }}>
                {formatTime(duration)}
              </span>
            </div>

            {/* Control Buttons */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              {/* Left Controls */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  onClick={togglePlay}
                  style={{
                    background: '#1e2d45',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '6px 12px',
                    color: '#e2e8f0',
                    cursor: 'pointer',
                    fontSize: '16px',
                    transition: 'background 0.2s'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = '#2d3f5f'}
                  onMouseOut={(e) => e.currentTarget.style.background = '#1e2d45'}
                >
                  {isPlaying ? '⏸️' : '▶️'}
                </button>

                {/* Volume */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '14px' }}>
                    {volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊'}
                  </span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={handleVolumeChange}
                    style={{
                      width: '60px',
                      height: '4px',
                      cursor: 'pointer'
                    }}
                  />
                </div>

                {/* Playback Speed */}
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[0.5, 1, 1.5, 2].map(rate => (
                    <button
                      key={rate}
                      onClick={() => handlePlaybackRateChange(rate)}
                      style={{
                        background: playbackRate === rate ? '#3b82f6' : '#1e2d45',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        color: '#e2e8f0',
                        cursor: 'pointer',
                        fontSize: '11px',
                        transition: 'background 0.2s'
                      }}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              </div>

              {/* Right Controls */}
              <button
                onClick={downloadVideo}
                style={{
                  background: '#1e2d45',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '6px 12px',
                  color: '#e2e8f0',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  transition: 'background 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = '#2d3f5f'}
                onMouseOut={(e) => e.currentTarget.style.background = '#1e2d45'}
              >
                ⬇️ Download
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
