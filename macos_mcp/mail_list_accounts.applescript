on run argv
	tell application "Mail"
		set outText to ""
		repeat with acc in accounts
			set n to my escapeField(name of acc as string)
			set emlList to ""
			try
				repeat with em in email addresses of acc
					if emlList is not "" then set emlList to emlList & ","
					set emlList to emlList & my escapeField(em as string)
				end repeat
			end try
			set outText to outText & n & tab & emlList & return
		end repeat
		return outText
	end tell
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
