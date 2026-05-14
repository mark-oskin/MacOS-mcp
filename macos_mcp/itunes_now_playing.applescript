-- Current track / transport. Output ASCII 30: player_state, persistent_id, name, artist, album, position_sec, duration_sec

on run argv
	set sep to ASCII character 30
	tell application "Music"
		set ps to player state as string
		if player state is stopped then
			return my esc(ps, sep) & sep & sep & sep & sep & sep & sep & sep
		end if
		try
			set t to current track
			set pid to persistent ID of t as string
			set nm to name of t as string
			set ar to ""
			try
				set ar to artist of t as string
			end try
			set al to ""
			try
				set al to album of t as string
			end try
			set pos to player position as number
			set dur to duration of t as number
			return my esc(ps, sep) & sep & my esc(pid, sep) & sep & my esc(nm, sep) & sep & my esc(ar, sep) & sep & my esc(al, sep) & sep & (pos as string) & sep & (dur as string)
		on error
			return my esc(ps, sep) & sep & sep & sep & sep & sep & sep & sep
		end try
	end tell
end run

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
