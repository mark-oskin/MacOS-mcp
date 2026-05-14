-- List Notes.app account names (one per line).

on run argv
	set outText to ""
	tell application "Notes"
		repeat with acc in accounts
			try
				set outText to outText & (name of acc as string) & return
			end try
		end repeat
	end tell
	return outText
end run
