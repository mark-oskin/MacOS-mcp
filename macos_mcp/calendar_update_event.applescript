-- Patch an existing event by uid. argv: calendarHint (empty = search all), uid, patchB64
-- patchB64 decodes to UTF-8 lines: key=value where value is standard base64 (UTF-8 payload).
-- Keys: summary, description, location, url, start_unix, end_unix, all_day (payload "0" or "1")

on run argv
	set calHint to item 1 of argv
	set theUid to item 2 of argv
	set patchB64 to item 3 of argv
	set patchText to my decodeB64(patchB64)
	tell application "Calendar"
		set ev to missing value
		set calObj to missing value
		if calHint is not "" then
			set calObj to my findCalendar(calHint)
			set ev to my findEventOnCalendar(calObj, theUid)
		else
			repeat with cal in calendars
				try
					set ev to my findEventOnCalendar(cal, theUid)
					set calObj to cal
					exit repeat
				end try
			end repeat
		end if
		if ev is missing value then error "Event not found for uid: " & theUid
		set parlines to paragraphs of patchText
		repeat with ln in parlines
			set s to contents of ln as string
			if s is not "" then
				my applyPatchLine(ev, s)
			end if
		end repeat
		set u to ""
		tell ev
			try
				set u to uid as string
			end try
			if u is "" then
				try
					set u to id as string
				end try
			end if
		end tell
		return u
	end tell
end run

on applyPatchLine(ev, s)
	set eq to offset of "=" in s
	if eq is 0 then return
	set k to text 1 thru (eq - 1) of s
	set vb64 to text (eq + 1) thru -1 of s
	set v to my decodeB64(vb64)
	tell application "Calendar"
		tell ev
			if k is "summary" then
				set summary to v
			else if k is "description" then
				set description to v
			else if k is "location" then
				set location to v
			else if k is "url" then
				set url to v
			else if k is "start_unix" then
				set start date to my dateFromUnix(v as number)
			else if k is "end_unix" then
				set end date to my dateFromUnix(v as number)
			else if k is "all_day" then
				if v is "1" then
					set allday event to true
				else
					set allday event to false
				end if
			end if
		end tell
	end tell
end applyPatchLine

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

on dateFromUnix(sec)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return refDate + sec
end dateFromUnix

on decodeB64(b64)
	return do shell script "printf %s " & quoted form of b64 & " | /usr/bin/base64 -D"
end decodeB64
