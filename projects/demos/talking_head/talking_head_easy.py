from rstem import speaker

# Make the RaspberryPi say "Hello World"
speaker.say("Hello World", wait=True)

# TODO: should we do speaker.say() or my_speech thing?

## create a variable my_speech that is the converted text into sound
#my_speech = speaker.Speech("Hello World") 

## play that sound tell it to wait until the sound has stopped playing before finishing the program
#my_speech.play(wait=True)
