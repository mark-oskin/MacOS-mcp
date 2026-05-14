-- Create a recurring event (separate from calendar_add_event for debugging).
-- argv: calendarName, summaryB64, descB64, locB64, urlB64, startUnix, endUnix, allDay 0|1,
--       recurrenceRRuleB64 (required; decodes to iCalendar RRULE, e.g. FREQ=WEEKLY;BYDAY=MO; use UNTIL=... in RRULE for end if needed)

on run argv
	set calName to item 1 of argv
	set summ to my decodeB64(item 2 of argv)
	set descB64 to item 3 of argv
	set locB64 to item 4 of argv
	set urlB64 to item 5 of argv
	set startUnix to (item 6 of argv) as number
	set endUnix to (item 7 of argv) as number
	set allDayFlag to item 8 of argv
	set rruleB64 to item 9 of argv
	set startD to my dateFromUnix(startUnix)
	set endD to my dateFromUnix(endUnix)
	set allDay to false
	if allDayFlag is "1" then set allDay to true
	set rrule to my decodeB64(rruleB64)
	tell application "Calendar"
		set calObj to my findCalendar(calName)
		tell calObj
			set ev to make new event with properties {summary:summ, start date:startD, end date:endD, allday event:allDay}
			set recurrence of ev to rrule
			if descB64 is not "" then
				set description of ev to my decodeB64(descB64)
			end if
			if locB64 is not "" then
				set location of ev to my decodeB64(locB64)
			end if
			if urlB64 is not "" then
				set url of ev to my decodeB64(urlB64)
			end if
			set u to ""
			try
				set u to uid of ev as string
			end try
			if u is "" then
				try
					set u to id of ev as string
				end try
			end if
			return u
		end tell
	end tell
end run

on findCalendar(nm)
	tell application "Calendar"
		repeat with cal in calendars
			if (name of cal as string) is nm then return cal
		end repeat
	end tell
	error "Calendar not found: " & nm
end findCalendar

on dateFromUnix(sec)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return refDate + sec
end dateFromUnix

on decodeB64(b64)
	return do shell script "printf %s " & quoted form of b64 & " | /usr/bin/base64 -D"
end decodeB64
