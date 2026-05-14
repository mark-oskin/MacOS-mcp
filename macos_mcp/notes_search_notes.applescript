-- argv: query, accountHint (empty = default account), limit
-- TSV: id, name, modified_unix, plaintext_preview (400)

use framework "Foundation"
use scripting additions

on run argv
	set q to item 1 of argv
	set accHint to item 2 of argv
	set lim to (item 3 of argv) as integer
	set n to 0
	set outText to ""
	set qLower to my asLower(q)
	tell application "Notes"
		if accHint is "" then
			set acc to default account
		else
			set acc to first account whose name is accHint
		end if
		repeat with f in folders of acc
			if n ≥ lim then exit repeat
			set sub to my searchFolder(f, qLower, lim, n, outText)
			set n to item 1 of sub
			set outText to item 2 of sub
		end repeat
	end tell
	return outText
end run

on searchFolder(f, qLower, lim, n, outText)
	tell application "Notes"
		repeat with nt in notes of f
			if n ≥ lim then exit repeat
			set nm to name of nt as string
			set pv to ""
			try
				set pv to plaintext of nt as string
			end try
			if my asLower(nm) contains qLower or my asLower(pv) contains qLower then
				set nid to my escapeField(id of nt as string)
				set nmEsc to my escapeField(nm)
				set mux to my unixFromDate(modification date of nt) as string
				set prv to pv
				if (length of prv) > 400 then set prv to text 1 thru 400 of prv
				set outText to outText & nid & tab & nmEsc & tab & mux & tab & my escapeField(prv) & return
				set n to n + 1
			end if
		end repeat
		repeat with sf in folders of f
			if n ≥ lim then exit repeat
			set sub to my searchFolder(sf, qLower, lim, n, outText)
			set n to item 1 of sub
			set outText to item 2 of sub
		end repeat
	end tell
	return {n, outText}
end searchFolder

on asLower(t)
	set s to current application's NSString's stringWithString:t
	return (s's lowercaseString()) as text
end asLower

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
