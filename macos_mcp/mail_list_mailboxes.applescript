on run argv
	tell application "Mail"
		set outText to ""
		repeat with acc in accounts
			set accName to name of acc as string
			try
				set outText to outText & my collectMailboxes(accName, mailboxes of acc, "")
			end try
		end repeat
		return outText
	end tell
end run

on collectMailboxes(accName, mbList, pathPrefix)
	set chunk to ""
	repeat with mb in mbList
		set mbName to name of mb as string
		set fullPath to pathPrefix & mbName
		set chunk to chunk & my escapeField(accName) & tab & my escapeField(fullPath) & return
		try
			set chunk to chunk & my collectMailboxes(accName, mailboxes of mb, fullPath & "/")
		end try
	end repeat
	return chunk
end collectMailboxes

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
