-- Toggle play / pause (Music.app)

on run argv
	tell application "Music" to playpause
	return "OK"
end run
