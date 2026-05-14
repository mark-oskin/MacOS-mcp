-- argv: query, limit, maxScan — scan library tracks from index 1 up to maxScan
-- TSV: persistent_id, name, artist, album, duration_sec, track_number

on run argv
	set q to item 1 of argv
	set lim to (item 2 of argv) as integer
	set maxScan to (item 3 of argv) as integer
	set n to 0
	set outText to ""
	tell application "Music"
		set lib to library playlist 1
		set c to count of tracks of lib
		if maxScan < c then set c to maxScan
		repeat with i from 1 to c
			if n ≥ lim then exit repeat
			set t to track i of lib
			set nm to ""
			try
				set nm to name of t as string
			end try
			set ar to ""
			try
				set ar to artist of t as string
			end try
			set al to ""
			try
				set al to album of t as string
			end try
			set hay to nm & " " & ar & " " & al
			ignoring case
				if hay contains q then
					set pid to persistent ID of t as string
					set dur to 0
					try
						set dur to duration of t as number
					end try
					set tn to 0
					try
						set tn to track number of t as integer
					end try
					set outText to outText & pid & tab & my escapeField(nm) & tab & my escapeField(ar) & tab & my escapeField(al) & tab & (dur as string) & tab & (tn as string) & return
					set n to n + 1
				end if
			end ignoring
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
