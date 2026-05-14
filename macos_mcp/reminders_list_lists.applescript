-- List Reminders.app lists. Output TSV: name, id

on run argv
	set outText to ""
	tell application "Reminders"
		repeat with rl in lists
			try
				set nm to my escapeField(name of rl as string)
				set rid to ""
				try
					set rid to my escapeField(id of rl as string)
				end try
				set outText to outText & nm & tab & rid & return
			end try
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
