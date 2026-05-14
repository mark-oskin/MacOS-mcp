on run argv
	if (count of argv) < 7 then error "Expected: account, fromAddress, to, cc, bcc, subject, bodyFilePath"
	set accountQuery to item 1 of argv as string
	set fromAddr to item 2 of argv as string
	set toLine to item 3 of argv as string
	set ccLine to item 4 of argv as string
	set bccLine to item 5 of argv as string
	set subj to item 6 of argv as string
	set bodyPath to item 7 of argv as string

	set bodyText to my readBodyFile(bodyPath)

	tell application "Mail"
		-- Always create at application level. `tell account …` / `outgoing messages of account`
		-- breaks on many setups (wrong container, -1728, -2700). Pick account via `sender` instead.
		set newMsg to make new outgoing message with properties {visible:false}

		tell newMsg
			repeat with a in my splitCSV(toLine)
				set addr to contents of a
				try
					make new to recipient at end of to recipients with properties {address:addr}
				on error
					make new to recipient with properties {address:addr}
				end try
			end repeat
			repeat with a in my splitCSV(ccLine)
				set addr to contents of a
				try
					make new cc recipient at end of cc recipients with properties {address:addr}
				on error
					make new cc recipient with properties {address:addr}
				end try
			end repeat
			repeat with a in my splitCSV(bccLine)
				set addr to contents of a
				try
					make new bcc recipient at end of bcc recipients with properties {address:addr}
				on error
					make new bcc recipient with properties {address:addr}
				end try
			end repeat
			set subject to subj
			set content to bodyText

			if fromAddr is not "" then
				set sender to fromAddr
			else if accountQuery is not "" then
				set senderLine to my findSenderLineForAccountQuery(accountQuery)
				if senderLine is "" then error "No Mail account matched \"" & accountQuery & "\". Use the account name from Mail's sidebar, an email on that account, or pass from_address."
				set sender to senderLine
			end if
		end tell
		send newMsg
	end tell
	return "OK"
end run

on findSenderLineForAccountQuery(accountQuery)
	if accountQuery is "" then return ""
	set q to accountQuery as string
	tell application "Mail"
		ignoring case
			repeat with acc in accounts
				try
					if (name of acc as string) is q then return my buildSenderLineFromAccount(acc)
				end try
				try
					repeat with em in email addresses of acc
						if (em as string) is q then return my buildSenderLineFromAccount(acc)
					end repeat
				end try
			end repeat
		end ignoring
	end tell
	return ""
end findSenderLineForAccountQuery

on buildSenderLineFromAccount(acc)
	tell application "Mail"
		set disp to name of acc as string
		try
			set em to item 1 of (email addresses of acc) as string
			return disp & " <" & em & ">"
		on error
			return disp
		end try
	end tell
end buildSenderLineFromAccount

on readBodyFile(posixPath)
	set f to POSIX file posixPath
	open for access f without write permission
	try
		set bodyText to read f for (get eof f) as «class utf8»
	on error
		try
			set bodyText to read f for (get eof f)
		on error err2
			close access f
			error "Could not read body file: " & err2
		end try
	end try
	close access f
	return bodyText
end readBodyFile

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

on splitCSV(addrLine)
	if addrLine is "" then return {}
	set tid to AppleScript's text item delimiters
	set AppleScript's text item delimiters to ","
	set rawParts to text items of addrLine
	set AppleScript's text item delimiters to tid
	set outList to {}
	repeat with ap in rawParts
		set t to my trim(contents of ap)
		if t is not "" then set end of outList to t
	end repeat
	return outList
end splitCSV
