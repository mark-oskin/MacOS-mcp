on run argv
	if (count of argv) < 3 then error "Expected: mailbox, account (or empty), mailId [, recipientPreviewLen [, bodyMaxChars]]"
	set mailboxName to item 1 of argv as string
	set accountName to item 2 of argv as string
	set mailIdStr to item 3 of argv as string
	set recvPreviewLen to 220
	if (count of argv) > 3 then set recvPreviewLen to (item 4 of argv as integer)
	set bodyMax to 500000
	if (count of argv) > 4 then set bodyMax to (item 5 of argv as integer)
	set rs to ASCII character 30

	tell application "Mail"
		set mb to missing value
		if accountName is not "" then
			try
				set mb to mailbox mailboxName of (first account whose name is accountName)
			on error errMsg number errNum
				error "Account/mailbox lookup failed: " & errMsg
			end try
		else
			repeat with acc in accounts
				try
					set mb to mailbox mailboxName of acc
					exit repeat
				end try
			end repeat
			if mb is missing value then error "No mailbox named \"" & mailboxName & "\" found in any account"
		end if

		set targetMsg to missing value
		try
			set idNum to mailIdStr as number
			set targetMsg to first message of mb whose id is idNum
		end try
		if targetMsg is missing value then
			repeat with i from 1 to (count of messages of mb)
				set m to message i of mb
				try
					if (id of m as string) is mailIdStr then
						set targetMsg to m
						exit repeat
					end if
				end try
			end repeat
		end if
		if targetMsg is missing value then error "No message with id " & mailIdStr & " in mailbox \"" & mailboxName & "\""

		set mid to ""
		try
			set mid to (id of targetMsg) as string
		end try

		set rfcId to ""
		try
			set rfcId to my escapeField((message id of targetMsg) as string)
		end try

		set subj to ""
		try
			set subj to my escapeField(subject of targetMsg as string)
		end try

		set snd to ""
		try
			set snd to my escapeField(sender of targetMsg as string)
		end try

		set ds to ""
		try
			set ds to my escapeField(date received of targetMsg as string)
		end try

		set toLine to ""
		try
			set toLine to my summarizeRecipientList(to recipients of targetMsg, recvPreviewLen)
		end try
		set ccLine to ""
		try
			set ccLine to my summarizeRecipientList(cc recipients of targetMsg, recvPreviewLen)
		end try

		set bodyText to ""
		try
			set bodyText to content of targetMsg as string
		end try
		set bodyText to my stripRecordSep(bodyText)
		if (length of bodyText) > bodyMax then set bodyText to text 1 thru bodyMax of bodyText

		return mid & rs & rfcId & rs & subj & rs & snd & rs & ds & rs & toLine & rs & ccLine & rs & bodyText
	end tell
end run

on summarizeRecipientList(recList, maxLen)
	set out to ""
	tell application "Mail"
		try
			repeat with rc in recList
				if (length of out) > maxLen then exit repeat
				try
					set out to out & ((address of rc) as string) & "; "
				end try
			end repeat
		end try
	end tell
	set out to my escapeField(out)
	if (length of out) > maxLen then set out to text 1 thru maxLen of out
	return out
end summarizeRecipientList

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

on stripRecordSep(t)
	set sep to ASCII character 30
	set AppleScript's text item delimiters to sep
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set AppleScript's text item delimiters to ""
	return t
end stripRecordSep
