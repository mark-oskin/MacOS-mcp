-- Delete an event by uid. argv: calendarHint (empty = search all), uid

on run argv
	set calHint to item 1 of argv
	set theUid to item 2 of argv
	tell application "Calendar"
		if calHint is not "" then
			set calObj to my findCalendar(calHint)
			set ev to my findEventOnCalendar(calObj, theUid)
			delete ev
		else
			repeat with cal in calendars
				try
					set ev to my findEventOnCalendar(cal, theUid)
					delete ev
					return "OK"
				end try
			end repeat
			error "Event not found for uid: " & theUid
		end if
	end tell
	return "OK"
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
