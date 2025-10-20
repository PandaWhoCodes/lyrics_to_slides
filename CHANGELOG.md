# Changelog

All notable changes to the Lyrics to Slides project will be documented in this file.

## [1.1.0] - 2024-10-20

### Added

#### 🎯 Robust Lyrics Extraction & Review System
- **New Review Step**: After selecting songs, users now see a review screen showing which songs successfully extracted lyrics and which failed
- **Smart Error Handling**: Songs with no lyrics found are clearly marked with error messages
- **Reselection Feature**: Users can try different sources for failed songs without starting over
- **Remove Option**: Failed songs can be removed from the presentation entirely
- **Partial Success Support**: Presentations can be generated with only the songs that succeeded

#### 🎵 Christian Music-Themed Loading Experience
- **30+ Loading Messages**: Fun, faith-inspired loading messages like:
  - "🎵 Tuning the heavenly harps..."
  - "🙏 Saying a quick prayer for good lyrics..."
  - "⛪ Consulting the worship team..."
  - "📖 Searching the Psalms for inspiration..."
- **Message Cycling**: Loading messages change every 2 seconds during operations
- **Beautiful Loading Overlay**: Full-screen overlay with spinner and message display

#### ⌨️ Keyboard Shortcuts
- **Ctrl+Enter / Cmd+Enter**: Quick submit from any input field on the first page
- **Visual Hint**: Keyboard shortcut displayed on Search button
- **Platform Support**: Works on both Windows/Linux (Ctrl) and Mac (Cmd)

### Fixed

#### 🐛 Critical Bug Fixes
- **Duplicate Songs Prevention**: Fixed issue where songs could appear multiple times in the final presentation
- **Reselection Flow**: Fixed broken reselection that was immediately returning to review screen
- **Error Persistence**: Fixed errors carrying over between screens inappropriately
- **API Key Security**: Removed exposed API key from documentation, replaced with placeholder

#### 🎨 UI/UX Improvements
- **Disabled States**: All buttons and cards properly disabled during loading operations
- **Error Clearing**: Errors now clear when navigating between screens
- **Loading States**: Consistent loading behavior across all operations
- **Visual Feedback**: Clear visual indicators for success/failure states

### Changed

#### 📦 Backend Improvements
- **New Endpoint**: Added `/api/extract-lyrics` for batch lyrics validation
- **Error Handling**: Backend now handles partial failures gracefully
- **Import Paths**: Fixed module import paths for proper deployment
- **Validation**: Pre-validation of lyrics before presentation generation

#### 🎨 Frontend Enhancements
- **State Management**: Improved tracking of selected songs and URLs
- **Flow Control**: Better navigation between selection, review, and generation steps
- **CSS Animations**: Added smooth animations for loading overlay and transitions
- **Responsive Design**: Loading overlay works on all screen sizes

### Technical Details

#### New API Endpoints
- `POST /api/extract-lyrics`: Validates lyrics extraction for multiple URLs
  - Returns success/failure status for each URL
  - Includes extracted title and lyrics for successful extractions
  - Provides detailed error messages for failures

#### Component Architecture
- Added review step in the application flow
- Implemented proper state management for reselection
- Created reusable loading overlay component
- Enhanced error boundary handling

## [1.0.0] - 2024-10-20

### Initial Release
- Basic song search functionality
- Lyrics extraction from multiple sources
- PowerPoint generation with customizable slides
- Multi-song presentation support
- Frontend UI with React + Vite
- Backend API with FastAPI
- Deployment configuration for Render

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.*