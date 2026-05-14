on run argv
	if (count of argv) < 5 then error "Expected: fromMailbox, fromAccount, toMailbox, toAccount, idsCommaSep"
	set fromMbName to item 1 of argv as string
	set fromAcct to item 2 of argv as string
	set toMbName to item 3 of argv as string
	set toAcct to item 4 of argv as string
	set idsStr to item 5 of argv as string

	tell application "Mail"
		set srcMb to my resolveMailbox(fromMbName, fromAcct)
		set destMb to my resolveDestMailbox(toMbName, toAcct, srcMb)

		set tid to AppleScript's text item delimiters
		set AppleScript's text item delimiters to ","
		set idParts to text items of idsStr
		set AppleScript's text item delimiters to tid

		set movedN to 0
		repeat with idToken in idParts
			set idStr to my trim(contents of idToken)
			if idStr is not "" then
				set m to my findMessageById(srcMb, idStr)
				if m is not missing value then
					move m to destMb
					set movedN to movedN + 1
				end if
			end if
		end repeat
		return (movedN as string)
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

on resolveDestMailbox(toMbName, toAcct, srcMb)
	tell application "Mail"
		if toAcct is not "" then
			return mailbox toMbName of (first account whose name is toAcct)
		end if
		try
			set srcAcct to account of srcMb
			return mailbox toMbName of srcAcct
		on error
			repeat with acc in accounts
				try
					return mailbox toMbName of acc
				end try
			end repeat
			error "No destination mailbox \"" & toMbName & "\" found"
		end try
	end tell
end resolveDestMailbox

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
