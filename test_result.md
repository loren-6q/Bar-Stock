# Test Result Document

## Bug Fixes Being Tested

### Bug 1: App crashes when editing prices in Manage tab
- **Fix**: Added parseFloat() safety wrappers around cost calculations
- **Test**: Edit Unit ฿ or Case ฿ fields in Manage tab, verify no crash

### Bug 2: No way to review stock check after save
- **Fix**: Added "View Details" button on saved sessions in History tab
- **Test**: Go to History > Click "View Details" on a session > Verify counts are displayed

### Bug 3: Shopping tab edits not persistent
- **Fix**: Order adjustments now saved to localStorage
- **Test**: Edit quantities in Shopping tab > Switch tabs > Return to Shopping > Verify edits preserved

## API Endpoints
- GET /api/stock-sessions/{session_id}/counts - Get counts for a session

