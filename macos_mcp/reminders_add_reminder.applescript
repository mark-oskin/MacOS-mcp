-- argv: listName, nameB64, bodyB64, dueUnixStr (empty = no due date)

on run argv
	set listName to item 1 of argv
	set nm to my decodeB64(item 2 of argv)
	set bod to my decodeB64(item 3 of argv)
	set dueStr to item 4 of argv
	tell application "Reminders"
		tell (first list whose name is listName)
			if dueStr is "" then
				set nr to make new reminder with properties {name:nm, body:bod}
			else
				set dueD to my dateFromUnix(dueStr as number)
				set nr to make new reminder with properties {name:nm, body:bod, due date:dueD}
			end if
			return id of nr as string
		end tell
	end tell
end run

on dateFromUnix(sec)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return refDate + sec
end dateFromUnix

on decodeB64(b64)
	return do shell script "printf %s " & quoted form of b64 & " | /usr/bin/base64 -D"
end decodeB64
