on run argv
	if (count of argv) < 6 then error "Expected: mailbox, account, query, limit, maxScan, recipientPreviewLen"
	set mailboxName to item 1 of argv as string
	set accountName to item 2 of argv as string
	set queryRaw to item 3 of argv as string
	set msgLimit to (item 4 of argv as integer)
	set maxScan to (item 5 of argv as integer)
	set recvPreviewLen to (item 6 of argv as integer)

	tell application "Mail"
		set mb to missing value
		if accountName is not "" then
			try
				set mb to mailbox mailboxName of (first account whose name is accountName)
			on error errMsg
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

		set c to count of messages of mb
		if c is 0 then return ""

		set scanN to maxScan
		if scanN > c then set scanN to c

		set outText to ""
		set foundN to 0
		ignoring case
			repeat with i from 1 to scanN
				if foundN is msgLimit then exit repeat
				set m to message i of mb
				set subj to ""
				try
					set subj to subject of m as string
				end try
				set snd to ""
				try
					set snd to sender of m as string
				end try
				set hay to subj & " " & snd
				if hay contains queryRaw then
					set foundN to foundN + 1
					set mid to ""
					try
						set mid to (id of m) as string
					end try
					set rfcId to ""
					try
						set rfcId to my escapeField((message id of m) as string)
					end try
					set subjEsc to my escapeField(subj)
					set sndEsc to my escapeField(snd)
					set ds to ""
					try
						set ds to my escapeField(date received of m as string)
					end try
					set toLine to ""
					try
						set toLine to my summarizeRecipientList(to recipients of m, recvPreviewLen)
					end try
					set ccLine to ""
					try
						set ccLine to my summarizeRecipientList(cc recipients of m, recvPreviewLen)
					end try
					set outText to outText & mid & tab & rfcId & tab & subjEsc & tab & sndEsc & tab & ds & tab & toLine & tab & ccLine & return
				end if
			end repeat
		end ignoring
		return outText
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
