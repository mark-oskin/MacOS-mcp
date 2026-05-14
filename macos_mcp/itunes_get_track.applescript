-- argv: persistentId (Music track persistent ID string)
-- TSV: persistent_id, name, artist, album, duration_sec, track_number, genre, location (file path if available)

on run argv
	set pid to item 1 of argv
	tell application "Music"
		set tid to pid as integer
		set t to first track of library playlist 1 whose persistent ID is tid
		set nm to name of t as string
		set ar to ""
		try
			set ar to artist of t as string
		end try
		set al to ""
		try
			set al to album of t as string
		end try
		set dur to 0
		try
			set dur to duration of t as number
		end try
		set tn to 0
		try
			set tn to track number of t as integer
		end try
		set gn to ""
		try
			set gn to genre of t as string
		end try
		set loc to ""
		try
			set loc to location of t as string
		end try
		set pidOut to persistent ID of t as string
		return my escapeField(pidOut) & tab & my escapeField(nm) & tab & my escapeField(ar) & tab & my escapeField(al) & tab & (dur as string) & tab & (tn as string) & tab & my escapeField(gn) & tab & my escapeField(loc)
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
