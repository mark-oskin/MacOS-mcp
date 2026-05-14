-- List Music.app playlists. TSV: name, persistent_id, special_kind

on run argv
	set outText to ""
	tell application "Music"
		repeat with pl in playlists
			try
				set nm to my escapeField(name of pl as string)
				set pid to ""
				try
					set pid to persistent ID of pl as string
				end try
				set sk to ""
				try
					set sk to special kind of pl as string
				end try
				set skEsc to my escapeField(sk)
				set outText to outText & nm & tab & pid & tab & skEsc & return
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
