## Pyramid Solitaire AI Solver

## Overview

This project is a fully functional implementation of **Pyramid Solitaire** built in Python. It features a playable graphical user interface (GUI) and integrates intelligent AI agents capable of solving the game autonomously using **Depth-First Search (DFS)** and **A* (A-Star)** algorithms.

The application includes a benchmarking tool to analyze the win rate and efficiency of different algorithms and a dynamic resolution system that adapts the game window to any screen size.

**Features**

* **Playable GUI:** A full graphical interface built with `Tkinter` and `Pillow`.
* **AI Solvers:**
    * **DFS:** Exhaustive search to find any valid winning path.
    * **A‎⁠*‎  Search:** Heuristic-based search to find solutions faster.
* **Visual Replay:** Watch the AI execute the winning moves step-by-step on the board.
* **Benchmarking Tool:** Run mass simulations to calculate win percentages and performance metrics.
* **Export Solutions:** Save winning step-by-step instructions to a text file.

## Prerequisites

* **Python 3.8+**
* **Pillow** (Python Imaging Library)

### Installation

1.  **Unzip** the project repository.
2.  Open your terminal/command prompt in the project folder.
3.  Install the required image library:

    ```bash
    pip install Pillow
    ```

### How to Run
### Method 1: Executable
Double-click the **`SolitarAI.exe`** file included in the folder. This will automatically check for dependencies and launch the game.

### Method 2: IDE
Open the folder from an IDE capable of running Python, open the **`main.py`** file, and run it.


## How to Play 
Manual Mode* **Objective:** Remove all cards from the pyramid by pairing them to sum to **13**.
* **Values:** Ace=1, J=11, Q=12, K=13.
* **Controls:** Click a card to select it. Click a valid match to remove both.
* *Example:* Click a **10** then click a **3**.
* **Kings (13)** are removed instantly when clicked.

* **Stock/Waste:** Click the top-left stockpile or click **"Rotate-Stock"**   to draw cards.

### AI Mode
1. Click **"Solve (DFS)"** or **"Solve (A*)"** on the right sidebar.
2. Wait for the status to change from "Searching..." to "Solution Found".
3. A popup will ask if you want to watch the AI play.
* **Yes:** The computer takes control and plays the game visually.
* **No:** You can use the **"Show Steps"** button to see a text list of moves or **"Export File"** to save them.


### Project Structure| File | Description |


| **`main.py`** | The entry point. Handles the GUI, user input, and game loop. |

| **`settings.py`** | Configuration file. Handles dynamic screen scaling and global constants. |

| **`models.py`** | Defines the `Card` class and Deck generation logic. |

| **`game_logic.py`** | The "Rules Engine". Validates moves, sums, and stock rotation rules. |

| **`solvers.py`** | Contains the DFS and A* algorithm implementations. |

| **`benchmark.py`** | A simulation tool for running thousands of games without graphics to test AI win rates. |

| **`Carded/`** | Directory containing the `.JPG` assets for the playing cards. |

