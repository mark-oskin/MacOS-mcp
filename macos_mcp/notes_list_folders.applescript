-- argv: accountName (empty = default account)
-- Output TSV: account_name, folder_path, folder_id

on run argv
	set accHint to item 1 of argv
	set outText to ""
	tell application "Notes"
		if accHint is "" then
			set acc to default account
		else
			set acc to first account whose name is accHint
		end if
		set accNm to name of acc as string
		repeat with f in folders of acc
			set outText to outText & my walkFolder(f, accNm, "")
		end repeat
	end tell
	return outText
end run

on walkFolder(f, accNm, pathPrefix)
	set outText to ""
	tell application "Notes"
		set fn to name of f as string
		set fp to fn
		if pathPrefix is not "" then set fp to pathPrefix & "/" & fn
		set fid to ""
		try
			set fid to id of f as string
		end try
		set outText to outText & my escapeField(accNm) & tab & my escapeField(fp) & tab & my escapeField(fid) & return
		repeat with sf in folders of f
			set outText to outText & my walkFolder(sf, accNm, fp)
		end repeat
	end tell
	return outText
end walkFolder

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
