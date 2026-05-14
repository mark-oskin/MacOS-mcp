-- argv: noteId, nameField (__SKIP__ or base64 UTF-8), bodyField (__SKIP__ or base64 UTF-8)

on run argv
	set nid to item 1 of argv
	set nameTok to item 2 of argv
	set bodyTok to item 3 of argv
	tell application "Notes"
		set nt to my findNoteById(nid)
		if nt is missing value then error "Note not found: " & nid
		if nameTok is not "__SKIP__" then
			set name of nt to my decodeB64(nameTok)
		end if
		if bodyTok is not "__SKIP__" then
			set body of nt to my decodeB64(bodyTok)
		end if
		return id of nt as string
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

on decodeB64(b64)
	return do shell script "printf %s " & quoted form of b64 & " | /usr/bin/base64 -D"
end decodeB64
