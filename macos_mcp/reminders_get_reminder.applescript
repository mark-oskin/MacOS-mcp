-- argv: listHint (empty = search all lists), reminderId
-- Output ASCII 30: list_name, id, name, body, due_unix, completed0|1

on run argv
	set listHint to item 1 of argv
	set rid to item 2 of argv
	set sep to ASCII character 30
	tell application "Reminders"
		if listHint is not "" then
			set rl to first list whose name is listHint
			set r to first reminder of rl whose id is rid
			return my serialize(r, rl, sep)
		else
			repeat with rl in lists
				try
					set r to first reminder of rl whose id is rid
					return my serialize(r, rl, sep)
				end try
			end repeat
		end if
	end tell
	error "Reminder not found: " & rid
end run

on serialize(r, rl, sep)
	tell application "Reminders"
		set lnm to name of rl as string
		set nm to ""
		try
			set nm to name of r as string
		end try
		set bod to ""
		try
			set bod to body of r as string
		end try
		set dux to ""
		try
			set dux to my unixFromDate(due date of r) as string
		end try
		set doneStr to "0"
		try
			if completed of r then set doneStr to "1"
		end try
		set uid to id of r as string
		return my esc(lnm, sep) & sep & my esc(uid, sep) & sep & my esc(nm, sep) & sep & my esc(bod, sep) & sep & dux & sep & doneStr
	end tell
end serialize

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
