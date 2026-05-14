-- argv: query, listName (empty = all lists), includeCompleted 0|1, limit

use framework "Foundation"
use scripting additions

on run argv
	set q to item 1 of argv
	set listName to item 2 of argv
	set incDone to item 3 of argv
	set lim to (item 4 of argv) as integer
	set qLower to my asLower(q)
	set n to 0
	set outText to ""
	tell application "Reminders"
		if listName is not "" then
			set rl to first list whose name is listName
			set rlist to {}
			if incDone is "1" then
				set rlist to reminders of rl
			else
				set rlist to (every reminder of rl whose completed is false)
			end if
			repeat with r in rlist
				if n ≥ lim then exit repeat
				set nm to ""
				try
					set nm to name of r as string
				end try
				set bod to ""
				try
					set bod to body of r as string
				end try
				if my asLower(nm) contains qLower or my asLower(bod) contains qLower then
					set outText to outText & my formatRow(r, rl)
					set n to n + 1
				end if
			end repeat
		else
			repeat with rl in lists
				if n ≥ lim then exit repeat
				set rlist to {}
				if incDone is "1" then
					set rlist to reminders of rl
				else
					set rlist to (every reminder of rl whose completed is false)
				end if
				repeat with r in rlist
					if n ≥ lim then exit repeat
					set nm to ""
					try
						set nm to name of r as string
					end try
					set bod to ""
					try
						set bod to body of r as string
					end try
					if my asLower(nm) contains qLower or my asLower(bod) contains qLower then
						set outText to outText & my formatRow(r, rl)
						set n to n + 1
					end if
				end repeat
			end repeat
		end if
	end tell
	return outText
end run

on formatRow(r, rl)
	tell application "Reminders"
		set rid to ""
		try
			set rid to my escapeField(id of r as string)
		end try
		set nmEsc to my escapeField(name of r as string)
		set bodEsc to ""
		try
			set bodEsc to my escapeField(body of r as string)
		end try
		set dux to ""
		try
			set dux to my unixFromDate(due date of r) as string
		end try
		set doneStr to "0"
		try
			if completed of r then set doneStr to "1"
		end try
		set lnm to my escapeField(name of rl as string)
		return rid & tab & nmEsc & tab & bodEsc & tab & dux & tab & doneStr & tab & lnm & return
	end tell
end formatRow

on asLower(t)
	set s to current application's NSString's stringWithString:t
	return (s's lowercaseString()) as text
end asLower

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
