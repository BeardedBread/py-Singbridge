# SingBridge
A python implementation of the Singaporean version of the Bridge Card game.

# Requirements
Python 3.6, pygame, signalslot

# Installation
1. Clone this repository
2. Make a virtual environment (optinal but recommended). Remember to activate it.
3. Install the required packages from requirements.txt:
`pip install -r requirements.txt`
4. Run main.py:
`python main.py`

# Run Options
When running `main.py`, you can give options:

`python main.py [options]`

3 options are availables:
* `-a` or `--autoplay`: To run the game with all bots
* `-va` or `--view-all`: All player cards are revealed
* `-s` or `--seed` followed by a file path: To run the game with a specified RNG seed
* `-t` or `--terminal`: To play with legacy terminal inputting
An example command:

`python main.py -a -s ./seeds/low_point_hand.rng`

This command runs the game with all bots and a seed from `./seeds/low_point_hand.rng`

# Controls
I hope that you know how to play the Singaporean version of Bridge.

Currently, the `p` key has to be pressed to begin the game.
During the game, **all inputs are done through the terminal**.
Instructions on the input format should appear in the terminal.

I'm looking into changing the input to be mouse-based as a separate version.

When closing the game, please be a bit patient. It should close within a second or two. 
You may also close it via Keyboard Interrupt (i.e. `Ctrl+c`) in the terminal.

# Bugs and Suggestions
Please report any bugs, specifying how the bug can be recreated. 
The more specific it is, the better.

Suggestions for improvements on the code are welcomed.

