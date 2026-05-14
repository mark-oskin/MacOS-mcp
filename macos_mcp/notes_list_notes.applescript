-- argv: accountHint (empty = default account), folderPath (e.g. Notes or Work/Clients), limit
-- TSV: id, name, created_unix, modified_unix, plaintext_preview

on run argv
	set accHint to item 1 of argv
	set folderPath to item 2 of argv
	set lim to (item 3 of argv) as integer
	set n to 0
	set outText to ""
	tell application "Notes"
		if accHint is "" then
			set acc to default account
		else
			set acc to first account whose name is accHint
		end if
		set fld to my resolveFolderPath(acc, folderPath)
		repeat with nt in notes of fld
			if n ≥ lim then exit repeat
			set nid to ""
			try
				set nid to my escapeField(id of nt as string)
			end try
			set nm to my escapeField(name of nt as string)
			set cux to ""
			try
				set cux to my unixFromDate(creation date of nt) as string
			end try
			set mux to ""
			try
				set mux to my unixFromDate(modification date of nt) as string
			end try
			set pv to ""
			try
				set pv to plaintext of nt as string
				if (length of pv) > 400 then set pv to text 1 thru 400 of pv
			end try
			set pvEsc to my escapeField(pv)
			set outText to outText & nid & tab & nm & tab & cux & tab & mux & tab & pvEsc & return
			set n to n + 1
		end repeat
	end tell
	return outText
end run

on resolveFolderPath(acc, relPath)
	tell application "Notes"
		set delim to AppleScript's text item delimiters
		set AppleScript's text item delimiters to "/"
		set bits to text items of relPath
		set AppleScript's text item delimiters to delim
		if (count of bits) is 0 then error "folderPath must be non-empty"
		set cur to missing value
		set pool to folders of acc
		repeat with i from 1 to count of bits
			set segS to item i of bits as string
			if segS is "" then
				-- skip empty segment from leading slash
			else
				set found to missing value
				repeat with f in pool
					if (name of f as string) is segS then
						set found to f
						exit repeat
					end if
				end repeat
				if found is missing value then error "folder not found in path: " & relPath
				set cur to found
				set pool to folders of cur
			end if
		end repeat
		if cur is missing value then error "folder not found: " & relPath
		return cur
	end tell
end resolveFolderPath

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

on unixFromDate(d)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return (d - refDate)
end unixFromDate
