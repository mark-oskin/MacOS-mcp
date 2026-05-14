-- argv: listHint (empty = search all), reminderId

on run argv
	set listHint to item 1 of argv
	set rid to item 2 of argv
	tell application "Reminders"
		if listHint is not "" then
			set rl to first list whose name is listHint
			set r to first reminder of rl whose id is rid
			delete r
		else
			repeat with rl in lists
				try
					set r to first reminder of rl whose id is rid
					delete r
					return "OK"
				end try
			end repeat
			error "Reminder not found: " & rid
		end if
	end tell
	return "OK"
end run
