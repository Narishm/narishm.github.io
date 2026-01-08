# NariSite Copilot Instructions

## Project Overview
NariSite is a personal VTuber schedule and game quest tracker with two independent views:
- **Weekly Calendar View** ([calendarweek.html](calendarweek.html)) – Shows 7-day schedule with animated bars, pulls from Google Calendar API
- **Monthly Calendar View** ([calendarmonth.html](calendarmonth.html)) – Dark-themed month grid with event images and details
- **Quest Data** ([json/finalquest.json](json/finalquest.json)) – Hierarchical Final Fantasy game completion tree (eras, games, alternate editions, unlocks)

## Architecture & Data Flow

### Google Calendar Integration
- **Config**: [js/config.js](js/config.js) exports `window.GCAL_CONFIG = { apiKey, calendarShareLink }`
- **API**: Calendar API v3 with public key auth; supports pagination (maxResults: 2500)
- **Color Mapping**: 11 Google Calendar color IDs mapped to hex in COLOR_ID_MAP object
- **Calendar ID Extraction**: Decodes base64-encoded `cid` parameter from share link URL

### Event Processing Pipeline
1. **Fetch**: `fetchAllEvents()` queries timeMin–timeMax range, handles pagination
2. **Group**: `coveredDayKeys()` maps multi-day events to all touched day keys
3. **Sort**: `sortEventsForDay()` orders by: all-day first, then start time, then title
4. **Feature**: `pickFeaturedEventForDay()` selects single event to display, skipping empty/marker-only if configured
5. **Render**: `makeRow()` creates DOM with day kanji+name, event title, time/TZ (if intraday)

### Time Handling
- **All-day events**: Use `event.start.date` (YYYY-MM-DD), no time display
- **Intraday events**: Use `event.start.dateTime` (ISO 8601), formatted via `formatTimeTwoLine()` with browser TZ abbr
- **Week bounds**: Sunday–Saturday (0–6 day-of-week); `startOfWeekSunday()` normalizes cursor date
- **Local logic**: All date math uses local timezone (not UTC shifts)

## Key Code Patterns

### Styling Architecture
- **CSS Variables** (`:root`): `--bg`, `--barDefault`, `--rowH`, `--gap`, `--slant` (26px polygon clipping), `--point` (arrow tip)
- **Responsive**: Breakpoint at 800px adjusts sizes; uses CSS `clamp()` for scalable fonts
- **Clip-path Shapes**: Bars use custom polygon for slanted left edge + pointed right arrow tip
- **Two-line Time**: Compact time + timezone abbreviation stacked via `<br>` in HTML

### Event Filtering Config
- `IGNORE_EMPTY_TITLES` – Skip events with blank summary
- `IGNORE_MARKER_ONLY_EVENTS` – Skip if only description (marker) but no title; determined by `looksLikeCode()` regex

### Quest JSON Structure
- **Root keys**: `eras` (array of era names), `adventures` (array of adventure objects)
- **Adventure fields**: `id`, `era`, `order` (total sequence), `type` (MAIN/ALTERNATE/CORE/SEQUEL), `name`, `edition`, `platform` (array), `unlocks` (nested array)
- **Nested Hierarchy**: Unlocks can contain unlocks (e.g., FF4 Interlude/After Years inside Complete Collection)
- **Ordering**: Global `order` field determines display sequence across all eras

## Development Workflow

### No Build Step
- HTML files are standalone; load js/config.js via `<script src="js/config.js"></script>`
- No bundler, transpiler, or CSS preprocessor – vanilla CSS + vanilla JS

### Debugging Calendar Issues
- **Check Config**: Verify `window.GCAL_CONFIG` exists after config.js loads
- **API Error Codes**: "401 Invalid Credentials" → API key invalid/revoked; "403 Calendar Not Accessible" → calendar is private (OAuth needed)
- **Pagination**: Events beyond 2500 require multiple fetches; `pageToken` from response iterates next batch
- **Timezone**: Browser `Intl.DateTimeFormat` determines TZ abbr display; consistent across all date operations

### Responsive Testing
- Viewport breakpoint: 800px (tablet/mobile); adjust `--arrowW`, `--rowH`, `--slant`, `--gap`
- Test week/month views with narrow screens; clamp() functions scale fonts automatically

## Common Modifications
- **Add a Calendar Color**: Update COLOR_ID_MAP (Google Calendar colorId → hex value)
- **Change Day Labels**: Edit DAYS array (name + kanji); weekday order is Sun–Sat
- **Filter Events**: Modify IGNORE_EMPTY_TITLES or IGNORE_MARKER_ONLY_EVENTS; edit pickFeaturedEventForDay() logic
- **Adjust Layout**: Tweak `--slant`, `--point`, `--rowH`, `--gap` CSS variables and media query thresholds
