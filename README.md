[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

This repo is dedicated to Chess1M (a.k.a. Fischer Double Random Chess) which is like Chess960 (a.k.a. Fischer Random) but allows asymmetric starting positions for Black and White.
This results in 960 x 960 = 921,600 possible starting positions - just shy of one million (hence the name 'Chess1M'). Castling rules are the same as in Chess960.

There are several parts:
(1)  Generation of Chess960 and Chess1M reference tables: these include standard FEN and Shredder FEN positions.

#WIP (2)  Sampling tool for randomly selecting a specified number of positions from the Chess1M universe of 921,600.

#WIP (3)  Calculation tool for starting position scores (in centipawns) for the randomly sampled positions. Uses Stockfish binary engine to value the sampled positions. 
#WIP      User defines time in s, no. of cores, hash table size and no. of main line moves for analysis.

#WIP (4)  Tool to merge output files from multiple valuation runs.

#WIP (5)  Tool to analyse distribution of starting score for visual analysis.

#WIP (6)  Tool to randomly select a single starting position from the Chess1M position given user-defined minimum/maximum evaluation score.

#WIP      This tool can be used for running tournaments using the Chess1M format.
