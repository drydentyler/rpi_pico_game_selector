# Raspberry Pi Pico Board Game Selector

## Description
My wife and I own a lot of board games but never know which ones to play outside a normal
rotation we have. My goal with this project was to develop a physical gadget we could use
to help pick a game for us to play.

## Required Hardware
- Raspberry Pi Pico 2W
- 8 Channel Rotary Switch
- 2 Channel Toggle Switch
- Rotary Encoder with Push Button
- 8-to-3 Priority Encoder

## How to use it
Once everything is assembled according to a schematic I hope to create one day, connect the
Raspberry Pi Pico and open a Python IDE, I used Thonny for this project, and copy all these 
files to the Pico. This can be done in Thonny after enabling the Files view, `View > Files`. 
During this step, you will also want to replace the information in `network_settings.py` with
your network name and password. Once everything is connected and the files have been copied over, 
disconnect the Pico and then plug it back in, it will begin running `main.py` and once connected 
to the Wi-Fi, it will display the IP address the webserver is running on the LCD screen.

Now that all the hardware is set up and the webserver is running, you can begin interacting
with the rotary encoder to alter the desired game duration in minutes, flip the toggle to 
pick whether you want a more complex game, and enter the number of players with the rotary switch.
Once all the parameters have been set on the dials, press the rotary encoder button and a game
will be selected matching the given criteria and displayed on the LCD screen. To return to the 
duration selection, press the rotary encoder button again.

If you navigate to the webserver IP address in a browser, you will be served a simple input form
for adding new games with fields including the game's name, minimum and maximum number of players, 
typical duration in minutes and complexity. The complexity is a metric used on the site 
BoardGameGeek, commonly called _weight_, and can be found on their site, here is additional 
information on how [weight](https://boardgamegeek.com/wiki/page/Weight) is defined.


## The progress of this project told through lessons learned
### Planning for the correct hardware
The biggest thing that I learned while working through this project was the importance of
planning before getting started because in retrospect I jumped into this project way too quickly
and therefore experienced many issues revolving around the hardware I chose to use. The first
big lesson I learned was that since the Pico requires MicroPython, I wouldn't be able to use
a light-weight database tool like SQLite like I had expected and therefore required an adaptation
to using a txt file. However, what I also learned from beginning to implement the txt file was that
the there was no file persistence in the Pico file system after reading a file and then trying to
append to that same file. This lead to a solution that overall I am not happy with but worked and lead
to learning more features of Python.

### Function Decorators
Working with the txt file as a database required careful interaction with the file so that I could always use the
correct method parameter (read, write, append) and ensure that after reading the file to rewrite it and guarantee file
persistence when the file system couldn't. My solution was to create a decorator function that would act similar to a
context manager for working with the txt file and be able to handle requests like reading all the games, getting a 
random game or inserting a game.

Below is the decorator function, which would accept `args` and `kwargs` as parameters to the decorated function. This
would then check if the keyword `method` was included, corresponding to 'a' for append, 'r' for read, and 'w' for write.
It would then open the txt file in that corresponding method and assign that file object to the keyword `file` and pass
the `args` and `kwargs` on to the decorated function. Once the decorated function is executed and the return value, `rv`,
is received, the file object is closed and `rv` is returned.
```python
def txt_context_manager(func):
    def wrapper(*args, **kwargs):
        if 'method' in kwargs:
            # Open the database file in the correct method
            f = open(GamesDB._file_name, kwargs['method'])
            # pass the file into the function being decorated as a kwarg
            kwargs['file'] = f
            # Execute the decorated function with the necessary args and kwargs
            rv = func(*args, **kwargs)
            # Close the file
            f.close()
            # Return any return value from the decorated function
            return rv
    return wrapper
```

This is the higher-level function from the database wrapper class and in this case calling the `insert_game` function. All
it needs to pass to the function is the `Game` object for the new game and the method to interact with the file, in this 
case, the new game is going to be appended to the end of the txt file ('a').
```python
def insert_game(self, game: Game):
    """
    Wrapper function for inserting a game into the database

    Args:
        game: Game, provided game object that is to be inserted into the database
    """
    # Insert the game using the 'a' (append) method for writing to the txt file
    return self.db.insert_game(game=game, method='a')
```

The decorator is then added to the function that is being wrapped and will properly handle interactions with the txt file
from there.
```python
@txt_context_manager
def insert_game(self, game: Game, **kwargs) -> int:
```
### Dunder Methods
At the same I was learning function decorators I was also learning about context managers and dunder methods and began
to get ideas as to how I could incorporate them into this project. The simplest way I could think of to use dunder methods
was to utilize `__repr__` and `__str__` for debugging and writing game objects to the txt file. Instead of using `f` strings
for writing out every game object, I overwrote the `__repr__` function in my Game class to be the format I would expect
to read from, and write back to, the txt file. At this point, I am still not completely sure whether to use the `__str__`
or `__repr__` method in this case because I understand the `__str__` method is for 'nicely printable, human-readable'
representation and `__repr__` is for developers and debugging, but I would say the way I use it has been used for both
purposes since I have been working on this. Ultimately, I suppose changing it to `__str__` would be the most correct decision
since this will be essentially a 'product' and debugging would not be done anymore.

```python
def __repr__(self):
    return f'{self.id},{self.name},{self.min_players},{self.max_players},{self.duration},{self.complexity}'
```

### Context Managers
While learning about dunder methods I was also introduced to context managers and given the most common example of working
with txt files through the `with` keyword. As I continued working on this project, I ran into issues constantly where an
exception thrown in my code would force the program to quit and leave the webserver open and unable to connect back to it
by rerunning the code. This led me to realize that a context manager on my webserve could be incredibly useful to ensure
the webserver is closed properly everytime. 

Creating the context manager for the webserver was then straight forward overriding my webserver class's `__enter__` and 
`__exit__` dunder methods. In the `__enter__` function, the Pico will connect to the Wi-Fi and return it's assigned IP
address and then take that assigned IP address and open a socket for communication over the network and finally must return
the instance of the webserver.

I also learned that the `__exit__` function **must** accept the three parameters exception type, value and traceback which
I include in the printed error statement after closing the webserver's connection.


### Rotary Encoders
I learned so much more about rotary encoders than I had anticipated before beginning this project and have a newfound 
appreciation for them when I feel that click of a dial. 

I didn't think that I would have needed such in depth knowledge 
of how they work in order to implement one, but I was very wrong. I wrestled with working with my rotary encoder for 
a lot longer than I would ever like to admit, sometimes the issue being code related and other times the resistors I 
was using were just accidentally touching on my breadboard. But after watching a lot of YouTube [videos](https://www.youtube.com/watch?v=sgnEUxeNxpM) 
and reading a many tutorials I was finally able to get it to work reliably. 

### Pico Dual Core Capabilities
At one point I was struggling desperately with trying to have the Pico webserver running while also listening to the 
rotary encoder in a combined `while True:` loop and could not have both work at the same time. I tried to find a creative
solution to listen to both which lead me to attempting multithreading and utilizing the Pico's dual cores.

All of my attempts to use the two cores of the Pico were with code that would listen constantly for either requests or
changed to the rotary encoder through `while True:` loops, which in hindsight were not the optimal way of working with 
either a rotary encoder or webserver at the same time and the current code reflects that. However, I made attempts at using
Core 1 for the rotary encoder and Core 2 for the webserver and reversed them but could never successfully have both working.

During those attempts though, I did learn about multithreading again which was something I had only used once before and 
learned how to implement semaphores for controlling the use of shared resources like the txt file for either getting a
random game which would be requested from the rotary encoder or inserting a game as a request from the webserver.

### Pico Interrupts
The current code reflects what ended up being the most effective way of working with the rotary encoder and webserver
at the same time which is utilizing interrupt requests on the 3 pins of the rotary encoder and a `while True:` loop on
the webserver to constantly serve the clients. 

The interrupts work by assigning a condition to listen for that would trigger a function handler and in the case of the 
'CLK', 'DT', and 'SW' pins, they were all listening for any rising or falling changes, however the handler functions were
different between both the 'CLK' and 'DT' pins and the 'SW' pin. I learned through this process that the handler functions
must accept the Pin parameter, although never used in my code, and often need global access to the variables/object instances
they need to work with. It was also good practice to temporarily remove the function handler while currently in it so that
there couldn't be multiple or overlapping requests. 

### Soldering and Circuit Board Layout
Once I had all the hardware features of this project working on a breadboard I wanted to transfer it to a perfboard to 
consolidate everything and remove excess wires. I had never soldered before and my first attempts at soldering wire to 
the rotary encoder, toggle switch and rotary switch were all pretty poor and needed to be redone several times. I tried 
to be extra cautious with the planning and layout of my perfboard to make sure everything fit and was laid out in the 
most efficient way but my excitement of laying everything out properly lead me to soldering everything onto the board at
once and never testing each individual component as it was added. 

Realizing my mistake, it felt pointless to try and test my first perfboard because there were so many things that could 
have gone wrong that I scrapped it and took an even more detailed approach. This time I wrote out a 27-step procedure 
for every wire and component that needed to be soldered to the board and a simple test I could perform with a multimeter 
like checking continuity or a software test checking each component was being read correctly from the Pico. 

This more detailed attempt revealed issues with the 8-to-3 priority encoder I was using and that I wasn't reliably reading
the binary output for the number of players. There were times when I could start at 8 players on the rotary switch and work
my way down to 1 but not back up. After a lot of probing with the multimeter, troubleshooting and learning to read datasheets, 
realized the priority encoder I was working with had a priority low and the expected voltage for a non-selected channel 
on the rotary switch was higher than what it was currently getting in my setup. 

The solution after some simple testing was to add pull-up resistors to bring up the voltage on each of the 8 input 
channels on the encoder which has since required a review of the perfboard layout that has not been done yet. 

### Pull-up Resistors and Common Node Issues
After realizing the solution to the issues I faced with the rotary switch simply required adding in pull-up resistors
to the inputs of the priority encoder, I went ahead and soldered another perf board, this time with only one pull-up 
resistor on each half of the board. This way I thought I could then connect 4 wires from the resistor to each of the 4
priority encoder inputs on each half. However, this quickly proved to be a problem because any Low signal sent to one of
the 4 inputs on a half of the board was shared with the others as well. Meaning a Low signal sent to input 4 propagated
to inputs 5, 6, and 7. 

It appeared that I had two courses of action I could take, either connect resistors directly from the power rails on the
perf board to the priority encoder inputs, requiring 8 resistors, or I could somewhat continue my original plan of having 
2 resistors from the power rails but now diodes between the resistor common node and the priority encoder inputs to prevent,
back flow of the Low signal to the other inputs, requiring 2 resistors and 8 diodes. To decide, I posed the question to 
an LLM with the situation, my findings and what I thought were the only two options but asked for additional insight. It 
responded saying the best option in this scenario was to go the 8 resistor route, and that's what I did. 

Ultimately I had failed to think about how having a common node for each half of the board could be affected by a low signal
getting passed between all the shared nodes. If I had done more extensive breadboard work earlier on then I perhaps could
have discovered this issue and solved it before once again soldering and then discovering a problem. 

I also discovered the importance of keeping the wires you are soldering neat while performing the final tests on the rotary
switch on the perf board. All the wires from the rotary switch are threaded flexible wires and I didn't properly tighten
one of them so there were extra strands that were loose and connecting to nearby inputs and disrupting the signals.


## Next steps
### Priority Encoder Changes
As I discovered with the priority encoder, the 8 inputs need higher idle voltages than they were originally getting, and
therefore I need to go back and revisit this part and likely verify that it all works integrated together on a perfboard.

### Custom PCB Design
One of the main goals of moving the project on from being on a breadboard to a perfboard was so that I could eventually
learn to design and print a custom PCB but currently that is on hold. I've tried multiple times to create the schematic/
PCB design, but I genuinely have no idea what I am doing when it comes to that and so this in conjunction with the latest
changes I've had to make with the pull-up resistors on the priority encoder will mean this aspect of the project will
have to wait a while.

### React Application
I also would love to give the webpage/server more functionality than it currently has but in the current configuration of
the project this would involve a lot of writing HTML in txt files, but I believe it could be possible to instead create a
React application that could work instead. I watched a [YouTube video](https://www.youtube.com/watch?v=mTpkV7xZln0&t=163s) 
where someone created a similar React application to communicate with a Pico but for the purposes of controlling a Roomba,
and I believe for my goals this should also work. More research and simple tests need to be done in order to confirm this,
but I believe it would work by opening a custom socket to the Pico's IP address and communicate via that. 

The capabilities of the webpage/server would be expanded to have more direct interaction with the database and actions such 
as viewing all the games in the webpage, making edits, inserting or removing games could all be done within the webpage.

### BoardGameGeek API and Barcode Scanning
I have the dream of incorporating the BoardGameGeek API to be able to send a board game
name and receive the weight(complexity) rating so users don't have to search it themselves.
And a further extension of this would be to include a way to scan the barcode on a game and
find the game that way, this would then be sent to the BGG API and receive all the necessary information back so the user
can just scan games in their collections, and they will be added automatically.

### Misc
- There should be an option added for lack of Wi-Fi, power outage or just no Wi-Fi available.
- Considerations to whether this will be portable and have some sort of battery attached or simply plug into a wall.
- Learning to design and build/print a custom case/enclosure for this project.
- There are also plenty of TODOs that I have added into the code since reviewing this that will need to be taken care of.


