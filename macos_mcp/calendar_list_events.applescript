-- List Calendar events overlapping a time range. argv: calendarName (empty = all), startUnix, endUnix, limit
-- Output TSV per line: calendarName, uid, summary, startUnix, endUnix, allday, location

on run argv
	set calName to item 1 of argv
	set startUnix to (item 2 of argv) as number
	set endUnix to (item 3 of argv) as number
	set lim to (item 4 of argv) as integer
	set startD to my dateFromUnix(startUnix)
	set endD to my dateFromUnix(endUnix)
	set n to 0
	set outText to ""
	tell application "Calendar"
		if calName is "" then
			repeat with cal in calendars
				if n ≥ lim then exit repeat
				try
					set cnm to name of cal as string
					set evs to every event of cal whose (start date < endD) and (end date > startD)
					repeat with ev in evs
						if n ≥ lim then exit repeat
						set outText to outText & my formatEventLine(cal, ev, cnm)
						set n to n + 1
					end repeat
				end try
			end repeat
		else
			set calObj to my findCalendar(calName)
			tell calObj
				set cnm to name of calObj as string
				set evs to every event whose (start date < endD) and (end date > startD)
				repeat with ev in evs
					if n ≥ lim then exit repeat
					set outText to outText & my formatEventLine(calObj, ev, cnm)
					set n to n + 1
				end repeat
			end tell
		end if
	end tell
	return outText
end run

on findCalendar(nm)
	tell application "Calendar"
		repeat with cal in calendars
			if (name of cal as string) is nm then return cal
		end repeat
	end tell
	error "Calendar not found: " & nm
end findCalendar

on formatEventLine(calObj, ev, cnm)
	tell application "Calendar"
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
			set loc to ""
			try
				set loc to location as string
			end try
			set sd to start date
			set ed to end date
			set ad to false
			try
				set ad to allday event
			end try
			set su to my escapeField(summ)
			set lu to my escapeField(loc)
			set cu to my escapeField(cnm)
			set uu to my escapeField(u)
			set sux to my unixFromDate(sd) as string
			set eux to my unixFromDate(ed) as string
			set adStr to "0"
			if ad then set adStr to "1"
			return cu & tab & uu & tab & su & tab & sux & tab & eux & tab & adStr & tab & lu & return
		end tell
	end tell
end formatEventLine

on dateFromUnix(sec)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return refDate + sec
end dateFromUnix

on unixFromDate(d)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return (d - refDate)
end unixFromDate

on escapeField(t)
	if t is missing value then return ""
	set t to t as string
	set AppleScript's text item delimiters to {return, linefeed}
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set AppleScript's text item delimiters to tab
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set sep to ASCII character 30
	set AppleScript's text item delimiters to sep
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set AppleScript's text item delimiters to ""
	return t
end escapeField
