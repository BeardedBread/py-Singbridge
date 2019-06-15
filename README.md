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

The `p` key has to be pressed to begin the game.
During the game, a panel will pop up for you to input the bid and call you partner.
To play a card, double click on a card in your hand.

If you are using the legacy terminal inputting option, 
**all inputs are done through the terminal**.
Instructions on the input format should appear in the terminal.

When closing the game, please be a bit patient. It should close within a second or two. 
You may also close it via Keyboard Interrupt (i.e. `Ctrl+c`) in the terminal.

# Bugs and Suggestions
Please report any bugs, specifying how the bug can be recreated. 
The more specific it is, the better.

Suggestions for improvements are welcomed.

