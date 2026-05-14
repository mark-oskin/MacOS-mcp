-- argv: noteId

on run argv
	set nid to item 1 of argv
	tell application "Notes"
		set nt to my findNoteById(nid)
		if nt is missing value then error "Note not found: " & nid
		delete nt
	end tell
	return "OK"
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
