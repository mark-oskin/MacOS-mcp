-- argv: listHint (empty = search all), reminderId, completedFlag 0|1

on run argv
	set listHint to item 1 of argv
	set rid to item 2 of argv
	set fl to item 3 of argv
	set wantDone to false
	if fl is "1" then set wantDone to true
	tell application "Reminders"
		if listHint is not "" then
			set rl to first list whose name is listHint
			set r to first reminder of rl whose id is rid
			set completed of r to wantDone
		else
			repeat with rl in lists
				try
					set r to first reminder of rl whose id is rid
					set completed of r to wantDone
					return "OK"
				end try
			end repeat
			error "Reminder not found: " & rid
		end if
	end tell
	return "OK"
end run
