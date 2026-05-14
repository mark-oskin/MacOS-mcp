on run argv
	if (count of argv) < 5 then error "Expected: mailbox, account, idsCommaSep, readFlag, flagFlag"
	set mailboxName to item 1 of argv as string
	set accountName to item 2 of argv as string
	set idsStr to item 3 of argv as string
	set readFlag to (item 4 of argv as integer) is 1
	set flagFlag to (item 5 of argv as integer) is 1

	tell application "Mail"
		set mb to my resolveMailbox(mailboxName, accountName)
		set tid to AppleScript's text item delimiters
		set AppleScript's text item delimiters to ","
		set idParts to text items of idsStr
		set AppleScript's text item delimiters to tid
		set n to 0
		repeat with idToken in idParts
			set idStr to my trim(contents of idToken)
			if idStr is not "" then
				set m to my findMessageById(mb, idStr)
				if m is not missing value then
					tell m
						set read status to readFlag
						set flagged to flagFlag
					end tell
					set n to n + 1
				end if
			end if
		end repeat
		return n as string
	end tell
end run

on resolveMailbox(mailboxName, accountName)
	tell application "Mail"
		if accountName is not "" then
			return mailbox mailboxName of (first account whose name is accountName)
		else
			repeat with acc in accounts
				try
					return mailbox mailboxName of acc
				end try
			end repeat
			error "No mailbox named \"" & mailboxName & "\" found in any account"
		end if
	end tell
end resolveMailbox

on findMessageById(mb, mailIdStr)
	tell application "Mail"
		try
			set idNum to mailIdStr as number
			return first message of mb whose id is idNum
		end try
		repeat with i from 1 to (count of messages of mb)
			set m to message i of mb
			try
				if (id of m as string) is mailIdStr then return m
			end try
		end repeat
		return missing value
	end tell
end findMessageById

on trim(s)
	set s to s as string
	repeat while s is not "" and (character 1 of s is space or character 1 of s is tab)
		if (length of s) is 1 then return ""
		set s to text 2 thru -1 of s
	end repeat
	repeat while s is not "" and (character -1 of s is space or character -1 of s is tab)
		if (length of s) is 1 then return ""
		set s to text 1 thru -2 of s
	end repeat
	return s
end trim
