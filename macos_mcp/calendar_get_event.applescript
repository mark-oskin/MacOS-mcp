-- Get one Calendar event by uid. argv: calendarHint (empty = search all), uid
-- Output: fields separated by ASCII 30: calendar, uid, summary, description, location, url, startUnix, endUnix, allday

on run argv
	set calHint to item 1 of argv
	set theUid to item 2 of argv
	set sep to ASCII character 30
	tell application "Calendar"
		if calHint is not "" then
			set calObj to my findCalendar(calHint)
			set ev to my findEventOnCalendar(calObj, theUid)
			return my serializeEvent(calObj, ev, sep)
		else
			repeat with cal in calendars
				try
					set ev to my findEventOnCalendar(cal, theUid)
					return my serializeEvent(cal, ev, sep)
				end try
			end repeat
		end if
	end tell
	error "Event not found for uid: " & theUid
end run

on findCalendar(nm)
	tell application "Calendar"
		repeat with cal in calendars
			if (name of cal as string) is nm then return cal
		end repeat
	end tell
	error "Calendar not found: " & nm
end findCalendar

on findEventOnCalendar(calObj, theUid)
	tell application "Calendar"
		tell calObj
			repeat with ev in events
				set u to ""
				try
					set u to uid of ev as string
				end try
				if u is theUid then return ev
				try
					if (id of ev as string) is theUid then return ev
				end try
			end repeat
		end tell
	end tell
	error "not found"
end findEventOnCalendar

on serializeEvent(calObj, ev, sep)
	tell application "Calendar"
		set cnm to name of calObj as string
		tell ev
			set u to ""
			try
				set u to uid as string
			end try
			if u is "" then
				try
					set u to id as string
				end try
			end if
			set summ to ""
			try
				set summ to summary as string
			end try
			set desc to ""
			try
				set desc to description as string
			end try
			set loc to ""
			try
				set loc to location as string
			end try
			set surl to ""
			try
				set surl to url as string
			end try
			set sd to start date
			set ed to end date
			set ad to false
			try
				set ad to allday event
			end try
			set adStr to "0"
			if ad then set adStr to "1"
			return my esc(cnm, sep) & sep & my esc(u, sep) & sep & my esc(summ, sep) & sep & my esc(desc, sep) & sep & my esc(loc, sep) & sep & my esc(surl, sep) & sep & (my unixFromDate(sd) as string) & sep & (my unixFromDate(ed) as string) & sep & adStr
		end tell
	end tell
end serializeEvent

on esc(t, sep)
	if t is missing value then return ""
	set t to t as string
	set AppleScript's text item delimiters to sep
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set AppleScript's text item delimiters to ""
	return t
end esc

on unixFromDate(d)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return (d - refDate)
end unixFromDate
