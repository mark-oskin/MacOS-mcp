-- argv: persistentId (empty = start/resume playback without changing current track selection)

on run argv
	set pid to item 1 of argv
	tell application "Music"
		if pid is "" then
			play
		else
			set tid to pid as integer
			set t to first track of library playlist 1 whose persistent ID is tid
			play t
		end if
	end tell
	return "OK"
end run
