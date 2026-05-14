-- argv: accountHint (empty = default account), folderPath, nameB64, bodyB64

on run argv
	set accHint to item 1 of argv
	set folderPath to item 2 of argv
	set nm to my decodeB64(item 3 of argv)
	set bod to my decodeB64(item 4 of argv)
	tell application "Notes"
		if accHint is "" then
			set acc to default account
		else
			set acc to first account whose name is accHint
		end if
		set fld to my resolveFolderPath(acc, folderPath)
		tell fld
			set nn to make new note with properties {name:nm, body:bod}
			return id of nn as string
		end tell
	end tell
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
			if segS is not "" then
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

on decodeB64(b64)
	return do shell script "printf %s " & quoted form of b64 & " | /usr/bin/base64 -D"
end decodeB64
