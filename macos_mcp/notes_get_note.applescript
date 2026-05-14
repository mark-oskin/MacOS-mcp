-- argv: noteId
-- Output ASCII 30: account, folder_path, id, name, created_unix, modified_unix, plaintext, body

on run argv
	set nid to item 1 of argv
	set sep to ASCII character 30
	tell application "Notes"
		set nt to my findNoteById(nid)
		if nt is missing value then error "Note not found: " & nid
		set acc to my containerAccount(nt)
		set accNm to name of acc as string
		set fp to my folderPathOfNote(nt, acc)
		set nm to name of nt as string
		set bod to ""
		try
			set bod to body of nt as string
		end try
		set ptx to ""
		try
			set ptx to plaintext of nt as string
		end try
		set cux to my unixFromDate(creation date of nt) as string
		set mux to my unixFromDate(modification date of nt) as string
		set uid to id of nt as string
		return my esc(accNm, sep) & sep & my esc(fp, sep) & sep & my esc(uid, sep) & sep & my esc(nm, sep) & sep & cux & sep & mux & sep & my esc(ptx, sep) & sep & my esc(bod, sep)
	end tell
end run

on findNoteById(nid)
	tell application "Notes"
		repeat with acc in accounts
			set nt to my findInAccount(acc, nid)
			if nt is not missing value then return nt
		end repeat
	end tell
	return missing value
end findNoteById

on findInAccount(acc, nid)
	tell application "Notes"
		repeat with f in folders of acc
			set nt to my findInFolder(f, nid)
			if nt is not missing value then return nt
		end repeat
	end tell
	return missing value
end findInAccount

on findInFolder(f, nid)
	tell application "Notes"
		repeat with nt in notes of f
			if (id of nt as string) is nid then return nt
		end repeat
		repeat with sf in folders of f
			set x to my findInFolder(sf, nid)
			if x is not missing value then return x
		end repeat
	end tell
	return missing value
end findInFolder

on containerAccount(nt)
	tell application "Notes"
		set x to container of nt
		repeat 40 times
			if (class of x) is account then return x
			set x to container of x
		end repeat
	end tell
	error "Could not resolve account for note"
end containerAccount

on folderPathOfNote(nt, acc)
	tell application "Notes"
		set lst to {}
		set cur to container of nt
		repeat 40 times
			if (class of cur) is account then exit repeat
			set beginning of lst to (name of cur as string)
			set cur to container of cur
		end repeat
		set delim to AppleScript's text item delimiters
		set AppleScript's text item delimiters to "/"
		set s to lst as string
		set AppleScript's text item delimiters to delim
		return s
	end tell
end folderPathOfNote

on esc(t, sep)
	if t is missing value then return ""
	set t to t as string
	set AppleScript's text item delimiters to sep
	set parts to text items of t
	set AppleScript's text item delimiters to " "
	set t to parts as string
	set AppleScript's text item delimiters to ""
	return t
end esc

on unixFromDate(d)
	set refDate to date "Thursday, January 1, 1970 12:00:00 AM"
	return (d - refDate)
end unixFromDate
