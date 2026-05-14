on run argv
	if (count of argv) < 4 then error "Expected: mailbox, account, mailId, outDirPath"
	set mailboxName to item 1 of argv as string
	set accountName to item 2 of argv as string
	set mailIdStr to item 3 of argv as string
	set outDir to item 4 of argv as string
	if outDir does not end with "/" then set outDir to outDir & "/"

	tell application "Mail"
		set mb to my resolveMailbox(mailboxName, accountName)
		set m to my findMessageById(mb, mailIdStr)
		if m is missing value then error "No message with id " & mailIdStr

		set outLines to ""
		set idx to 0
		repeat with att in mail attachments of m
			if idx is 15 then exit repeat
			set fn to "mcpatt_" & (idx as string)
			set destPath to outDir & fn
			try
				save att in POSIX file destPath
				set nm to ""
				try
					set nm to name of att as string
				end try
				set mt to ""
				try
					set mt to MIME type of att as string
				end try
				set fsz to 0
				try
					set fsz to size of att as integer
				on error
					set fsz to 0
				end try
				set outLines to outLines & fn & tab & my escapeField(nm) & tab & my escapeField(mt) & tab & (fsz as string) & return
				set idx to idx + 1
			end try
		end repeat
		return outLines
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
