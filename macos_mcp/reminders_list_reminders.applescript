-- argv: listName, includeCompleted 0|1, limit
-- TSV: id, name, body, due_unix, completed0|1, list_name

on run argv
	set listName to item 1 of argv
	set incDone to item 2 of argv
	set lim to (item 3 of argv) as integer
	set n to 0
	set outText to ""
	tell application "Reminders"
		set rl to first list whose name is listName
		set rlist to {}
		if incDone is "1" then
			set rlist to reminders of rl
		else
			set rlist to (every reminder of rl whose completed is false)
		end if
		repeat with r in rlist
			if n ≥ lim then exit repeat
			set rid to ""
			try
				set rid to my escapeField(id of r as string)
			end try
			set nm to ""
			try
				set nm to my escapeField(name of r as string)
			end try
			set bod to ""
			try
				set bod to my escapeField(body of r as string)
			end try
			set dux to ""
			try
				set dd to due date of r
				set dux to my unixFromDate(dd) as string
			end try
			set doneStr to "0"
			try
				if completed of r then set doneStr to "1"
			end try
			set lnm to my escapeField(name of rl as string)
			set outText to outText & rid & tab & nm & tab & bod & tab & dux & tab & doneStr & tab & lnm & return
			set n to n + 1
		end repeat
	end tell
	return outText
end run

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

on unixFromDate(d)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return (d - refDate)
end unixFromDate
