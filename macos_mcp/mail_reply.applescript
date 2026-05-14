on run argv
	if (count of argv) < 6 then error "Expected: mailbox, account, mailId, bodyFilePath, replyAll(0|1)"
	set mailboxName to item 1 of argv as string
	set accountName to item 2 of argv as string
	set mailIdStr to item 3 of argv as string
	set bodyPath to item 4 of argv as string
	set replyAllStr to item 5 of argv as string

	set bodyText to my readBodyFile(bodyPath)

	tell application "Mail"
		set mb to my resolveMailbox(mailboxName, accountName)
		set m to my findMessageById(mb, mailIdStr)
		if m is missing value then error "No message with id " & mailIdStr

		set rmsg to missing value
		if replyAllStr is "1" then
			try
				set rmsg to reply m with reply to all without opening window
			on error
				set rmsg to reply m without opening window
			end try
		else
			set rmsg to reply m without opening window
		end if

		delay 0.5
		tell rmsg
			set content to bodyText
			send
		end tell
	end tell
	return "OK"
end run

on readBodyFile(posixPath)
	set f to POSIX file posixPath
	open for access f without write permission
	try
		set bodyText to read f for (get eof f) as «class utf8»
	on error
		set bodyText to read f for (get eof f)
	end try
	close access f
	return bodyText
end readBodyFile

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
