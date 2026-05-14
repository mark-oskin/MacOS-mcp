-- List calendars in Calendar.app (macOS). Tool prefix calendar_* for Calendar automation.

on run argv
	tell application "Calendar"
		set outText to ""
		repeat with cal in calendars
			try
				set nm to my escapeField(name of cal as string)
				set cid to ""
				try
					set cid to my escapeField(id of cal as string)
				end try
				set wStr to "0"
				try
					if writable of cal then set wStr to "1"
				end try
				set colStr to ""
				try
					set colStr to my escapeField(color of cal as string)
				end try
				set outText to outText & nm & tab & cid & tab & wStr & tab & colStr & return
			end try
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
